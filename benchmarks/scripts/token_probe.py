"""候補promptをN=30へ上げる前に、token空間とtarget tool-call尤度で順位付けする。

静的embedding cosineよりタスクへ直接的な、full chat/tool schema条件下のteacher-forced NLLを測る。
baselineがgreedy生成した正解tool-call列を共通targetとし、候補ごとのtarget token順位/margin、
token列編集距離、短い予備生成の到達性をJSONへ保存する。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

_LOCAL_SDK_ROOT = Path(__file__).resolve().parents[2] / "vendor" / "aicomp_sdk_pkg"
_SDK_ROOT = Path(os.environ.get("AICOMP_SDK_ROOT", ""))
for _sdk_root in (_SDK_ROOT, _LOCAL_SDK_ROOT):
    if (_sdk_root / "aicomp_sdk").is_dir() and str(_sdk_root) not in sys.path:
        sys.path.insert(0, str(_sdk_root))

from aicomp_sdk.agents.gpt_oss_agent import _parse_gpt_oss_harmony_response  # noqa: E402
from aicomp_sdk.agents.hf_chat_template.types import HFGenerationResponse  # noqa: E402
from aicomp_sdk.agents.tool_specs import to_agent_tool_specs  # noqa: E402
from aicomp_sdk.agents.types import ToolCallDecision  # noqa: E402
from aicomp_sdk.core.env.sandbox import _DEFAULT_RUNTIME_INSTRUCTIONS  # noqa: E402
from aicomp_sdk.core.runtime_history import RuntimeHistory  # noqa: E402
from aicomp_sdk.core.tools import ToolSuite  # noqa: E402
from llama_cpp.llama_chat_format import Jinja2ChatFormatter  # noqa: E402

try:
    import eval_driver as ed
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "eval"))
    import eval_driver as ed


def _default_expected_arguments(_name: str, recipient: str) -> dict[str, Any]:
    return {"to": recipient, "subject": "", "body": ""}


def _load_candidates(
    path_str: str,
) -> tuple[
    dict[str, Any],
    str,
    str | None,
    Callable[[str, str], dict[str, Any]],
    Callable[[str, str], str] | None,
]:
    path = Path(path_str).resolve()
    spec = importlib.util.spec_from_file_location("_token_probe_candidates", path)
    if not spec or not spec.loader:
        raise ImportError(f"候補moduleをロードできません: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    candidates = getattr(mod, "CANDIDATES", None)
    baseline_name = getattr(mod, "BASELINE_NAME", "b0_english")
    expected_marker = getattr(mod, "EXPECTED_MARKER", None)
    expected_arguments = getattr(mod, "EXPECTED_ARGUMENTS", None)
    target_text = getattr(mod, "TARGET_TEXT", None)
    if not isinstance(candidates, dict) or baseline_name not in candidates:
        raise TypeError(f"CANDIDATES dict とbaseline '{baseline_name}' が必要です")
    if expected_marker is not None and not isinstance(expected_marker, str):
        raise TypeError("EXPECTED_MARKER はstrまたは未定義にしてください")
    if expected_arguments is None:
        expected_arguments = _default_expected_arguments
    if not callable(expected_arguments):
        raise TypeError("EXPECTED_ARGUMENTS は(candidate_name, recipient)を受けるcallableにしてください")
    if target_text is not None and not callable(target_text):
        raise TypeError("TARGET_TEXT は(candidate_name, recipient)を受けるcallableにしてください")
    return candidates, baseline_name, expected_marker, expected_arguments, target_text


def _backend_from_factory(agent_factory: Any) -> Any:
    for cell in getattr(agent_factory, "__closure__", None) or ():
        value = cell.cell_contents
        if hasattr(value, "llm"):
            return value
    raise RuntimeError("agent_factory closureからllama.cpp backendを取得できません")


def _render_prompt(agent: Any, llm: Any, message: str, tools: tuple[Any, ...]) -> list[int]:
    history = RuntimeHistory().with_instruction(_DEFAULT_RUNTIME_INSTRUCTIONS).with_user_message(message)
    request = agent._delegate._build_request(history, tools)
    template = llm.metadata.get("tokenizer.chat_template")
    if not isinstance(template, str) or not template:
        raise RuntimeError("GGUF metadataにtokenizer.chat_templateがありません")
    bos = llm.detokenize([llm.token_bos()], special=True).decode("utf-8", errors="replace")
    eos = llm.detokenize([llm.token_eos()], special=True).decode("utf-8", errors="replace")
    rendered = Jinja2ChatFormatter(template=template, eos_token=eos, bos_token=bos)(
        messages=request.messages,
        tools=request.tools,
    )
    return llm.tokenize(rendered.prompt.encode("utf-8"), add_bos=not rendered.added_special, special=True)


def _token_pieces(llm: Any, ids: list[int]) -> list[str]:
    return [llm.detokenize([token_id], special=True).decode("utf-8", errors="replace") for token_id in ids]


def _levenshtein(left: list[int], right: list[int]) -> int:
    if len(left) > len(right):
        left, right = right, left
    previous = list(range(len(left) + 1))
    for row, right_value in enumerate(right, start=1):
        current = [row]
        for col, left_value in enumerate(left, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[col] + 1,
                    previous[col - 1] + (left_value != right_value),
                )
            )
        previous = current
    return previous[-1]


def _common_prefix(left: list[int], right: list[int]) -> int:
    count = 0
    for left_value, right_value in zip(left, right, strict=False):
        if left_value != right_value:
            break
        count += 1
    return count


def _current_logits(llm: Any) -> np.ndarray:
    # logits_all=Falseでもllama.cpp batchは最後のtokenのlogitsを保持する。全系列scores配列を
    # n_ctx×vocabで確保せず、teacher forcingを1 tokenずつ進めてこの行だけ読む。
    return np.ctypeslib.as_array(llm._ctx.get_logits(), shape=(llm.n_vocab(),)).copy()


def _target_likelihood(llm: Any, prompt_ids: list[int], target_ids: list[int]) -> dict[str, Any]:
    llm.reset()
    llm.eval(prompt_ids)
    logps: list[float] = []
    ranks: list[int] = []
    margins: list[float] = []
    for target_id in target_ids:
        logits = _current_logits(llm)
        target_logit = float(logits[target_id])
        maximum = float(np.max(logits))
        logsumexp = maximum + math.log(float(np.exp(logits - maximum).sum()))
        logps.append(target_logit - logsumexp)
        ranks.append(int(np.count_nonzero(logits > target_logit)) + 1)
        top_two = np.partition(logits, -2)[-2:]
        best_other = float(np.min(top_two) if target_logit == float(np.max(top_two)) else np.max(top_two))
        margins.append(target_logit - best_other)
        llm.eval([target_id])
    return {
        "target_mean_nll": round(-sum(logps) / len(logps), 5) if logps else None,
        "target_total_nll": round(-sum(logps), 5),
        "target_rank_mean": round(sum(ranks) / len(ranks), 3) if ranks else None,
        "target_rank_p95": sorted(ranks)[int((len(ranks) - 1) * 0.95)] if ranks else None,
        "target_margin_mean": round(sum(margins) / len(margins), 5) if margins else None,
        "target_first_logp": round(logps[0], 5) if logps else None,
    }


def _greedy_text(llm: Any, prompt_ids: list[int], max_tokens: int) -> tuple[str, list[int]]:
    completion = llm.create_completion(
        prompt=prompt_ids,
        max_tokens=max_tokens,
        temperature=0.0,
        top_k=1,
        top_p=1.0,
        min_p=0.0,
        repeat_penalty=1.0,
    )
    text = str(completion["choices"][0]["text"])
    ids = llm.tokenize(text.encode("utf-8"), add_bos=False, special=True)
    return text, ids


def _preview_semantics(raw_text: str, model: str, expected_arguments: dict[str, Any]) -> dict[str, Any]:
    """採点環境と同じparserでpreviewを解釈し、mail tool/argsの完全一致を確認する。"""
    try:
        if model == "gpt_oss":
            parsed = _parse_gpt_oss_harmony_response(raw_text)
            calls = parsed.get("tool_calls", []) if isinstance(parsed, dict) else []
            function = calls[0].get("function", {}) if len(calls) == 1 and isinstance(calls[0], dict) else {}
            name = function.get("name")
            arguments = function.get("arguments")
        else:
            response = HFGenerationResponse(text=raw_text, raw_text=raw_text)
            decision = ed._build_kaggle_gemma4_parser().parse(response, fallback_call_id="preview")
            calls = [decision] if isinstance(decision, ToolCallDecision) else []
            name = decision.call.tool_name if calls else None
            arguments = decision.call.arguments if calls else None
    except Exception as err:  # probeは不正候補も扱うため、parse失敗を測定値として残す
        return {
            "preview_parse_error": f"{type(err).__name__}: {err}",
            "preview_tool_call_count": 0,
            "preview_tool_name": None,
            "preview_arguments": None,
            "preview_exact_target": False,
            "preview_exact_email": False,
        }

    exact = len(calls) == 1 and name == "email.send" and arguments == expected_arguments
    return {
        "preview_parse_error": None,
        "preview_tool_call_count": len(calls),
        "preview_tool_name": name,
        "preview_arguments": arguments,
        "preview_exact_target": exact,
        "preview_exact_email": exact,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["gpt_oss", "gemma_4"], required=True)
    ap.add_argument("--candidates-file", required=True)
    ap.add_argument("--recipient", default="a")
    ap.add_argument("--validation-recipients", default="a,b,c,z,aa,ad")
    ap.add_argument("--preview-tokens", type=int, default=64)
    ap.add_argument("--target-tokens", type=int, default=64)
    ap.add_argument(
        "--prune-primary-miss",
        action="store_true",
        help="代表recipientで不一致なら残りrecipient生成とtarget NLLを省略する",
    )
    ap.add_argument(
        "--prune-primary-output-miss",
        action="store_true",
        help="代表recipientのraw出力がTARGET_TEXTと違えば残りrecipient生成とtarget NLLを省略する",
    )
    ap.add_argument("--out", default="token_probe_results.json")
    args = ap.parse_args()

    candidates, baseline_name, configured_marker, expected_arguments, configured_target = _load_candidates(
        args.candidates_file
    )
    fixtures_dir = ed.ops.resolve_fixtures_dir(None)
    agent_factory = ed.build_agent_factory(args.model)
    backend = _backend_from_factory(agent_factory)
    llm = backend.llm
    agent = agent_factory()
    suite = ToolSuite(fixtures_dir)
    tools = to_agent_tool_specs(tuple(suite.specs.values()))

    messages = {name: builder(args.recipient) for name, builder in candidates.items()}
    message_ids = {
        name: llm.tokenize(message.encode("utf-8"), add_bos=False, special=True) for name, message in messages.items()
    }
    prompts = {name: _render_prompt(agent, llm, message, tools) for name, message in messages.items()}

    baseline_prompt = prompts[baseline_name]
    target_text, target_ids = _greedy_text(llm, baseline_prompt, args.target_tokens)
    if not target_ids:
        raise RuntimeError("baselineのgreedy targetが空です")
    baseline_message_ids = message_ids[baseline_name]
    expected_marker = configured_marker or ("to=functions.email.send" if args.model == "gpt_oss" else "call:email.send")

    results: dict[str, Any] = {}
    for name in candidates:
        preview_text, preview_ids = _greedy_text(llm, prompts[name], args.preview_tokens)
        desired_target_text = configured_target(name, args.recipient) if configured_target else target_text
        desired_target_ids = llm.tokenize(desired_target_text.encode("utf-8"), add_bos=False, special=True)
        primary_semantics = _preview_semantics(preview_text, args.model, expected_arguments(name, args.recipient))
        primary_exact_output = preview_text == desired_target_text
        validation_rows: list[dict[str, Any]] = []
        validation_recipients = list(
            dict.fromkeys(r.strip() for r in args.validation_recipients.split(",") if r.strip())
        )
        evaluated_validation_recipients = validation_recipients
        if args.prune_primary_miss and not primary_semantics["preview_exact_target"]:
            evaluated_validation_recipients = [args.recipient]
        if args.prune_primary_output_miss and not primary_exact_output:
            evaluated_validation_recipients = [args.recipient]
        for recipient in evaluated_validation_recipients:
            if recipient == args.recipient:
                validation_text, validation_ids = preview_text, preview_ids
                semantics = primary_semantics
            else:
                validation_message = candidates[name](recipient)
                validation_prompt = _render_prompt(agent, llm, validation_message, tools)
                validation_text, validation_ids = _greedy_text(llm, validation_prompt, args.preview_tokens)
                semantics = _preview_semantics(validation_text, args.model, expected_arguments(name, recipient))
            validation_rows.append(
                {
                    "recipient": recipient,
                    "token_count": len(validation_ids),
                    "exact": semantics["preview_exact_target"],
                    "exact_output": validation_text
                    == (configured_target(name, recipient) if configured_target else target_text),
                    "tool_name": semantics["preview_tool_name"],
                    "arguments": semantics["preview_arguments"],
                    "parse_error": semantics["preview_parse_error"],
                }
            )
        edit = _levenshtein(baseline_message_ids, message_ids[name])
        exact_rate = (
            round(sum(row["exact"] for row in validation_rows) / len(validation_recipients), 5)
            if validation_recipients
            else None
        )
        exact_output_rate = (
            round(sum(row["exact_output"] for row in validation_rows) / len(validation_recipients), 5)
            if validation_recipients
            else None
        )
        likelihood = (
            _target_likelihood(llm, prompts[name], desired_target_ids)
            if (not args.prune_primary_miss or exact_rate == 1.0)
            and (not args.prune_primary_output_miss or primary_exact_output)
            else {
                "target_mean_nll": None,
                "target_total_nll": None,
                "target_rank_mean": None,
                "target_rank_p95": None,
                "target_margin_mean": None,
                "target_first_logp": None,
            }
        )
        results[name] = {
            "message": messages[name],
            "message_token_count": len(message_ids[name]),
            "message_token_ids": message_ids[name],
            "message_token_pieces": _token_pieces(llm, message_ids[name]),
            "full_prompt_token_count": len(prompts[name]),
            "baseline_token_edit": edit,
            "baseline_token_edit_normalized": round(edit / max(len(baseline_message_ids), len(message_ids[name])), 5),
            "baseline_common_prefix_tokens": _common_prefix(baseline_message_ids, message_ids[name]),
            "preview_token_count": len(preview_ids),
            "preview_has_target_marker": expected_marker in preview_text,
            "preview_text": preview_text,
            "desired_target_text": desired_target_text,
            "desired_target_token_count": len(desired_target_ids),
            "desired_target_token_ids": desired_target_ids,
            "desired_target_token_pieces": _token_pieces(llm, desired_target_ids),
            **primary_semantics,
            "preview_exact_output": primary_exact_output,
            "validation_previews": validation_rows,
            "preview_exact_rate": exact_rate,
            "preview_exact_output_rate": exact_output_rate,
            "preview_token_count_max": max((row["token_count"] for row in validation_rows), default=len(preview_ids)),
            **likelihood,
        }
        nll = results[name]["target_mean_nll"]
        rank = results[name]["target_rank_mean"]
        nll_text = "-" if nll is None else f"{nll:.4f}"
        rank_text = "-" if rank is None else f"{rank:.1f}"
        print(
            f"[probe] {name:24} tok={len(message_ids[name]):3} edit={edit:3} "
            f"nll={nll_text} rank={rank_text} "
            f"preview={len(preview_ids):2}/{results[name]['preview_token_count_max']:2} "
            f"exact={results[name]['preview_exact_rate']:.3f} "
            f"raw={results[name]['preview_exact_output_rate']:.3f}"
        )

    payload = {
        "model": args.model,
        "parser_profile": "kaggle_gemma4" if args.model == "gemma_4" else "sdk_default",
        "baseline_name": baseline_name,
        "recipient": args.recipient,
        "target_text": target_text,
        "target_token_count": len(target_ids),
        "target_token_ids": target_ids,
        "target_token_pieces": _token_pieces(llm, target_ids),
        "expected_marker": expected_marker,
        "results": results,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"[probe] saved {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
