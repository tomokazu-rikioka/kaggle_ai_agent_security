"""成功したemail.send後の次token分布を測り、直接returnの探索可能性を判定する。"""

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

from aicomp_sdk.agents.tool_specs import to_agent_tool_specs  # noqa: E402
from aicomp_sdk.agents.types import ToolCall, ToolResult  # noqa: E402
from aicomp_sdk.core.env.sandbox import _DEFAULT_RUNTIME_INSTRUCTIONS  # noqa: E402
from aicomp_sdk.core.runtime_history import RuntimeHistory  # noqa: E402
from aicomp_sdk.core.tools import ToolSuite  # noqa: E402
from llama_cpp.llama_chat_format import Jinja2ChatFormatter  # noqa: E402

try:
    import eval_driver as ed
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "eval"))
    import eval_driver as ed


def _load_variants(path_str: str) -> tuple[dict[str, Callable[[str], str]], Callable[[str, str], dict[str, Any]]]:
    path = Path(path_str).resolve()
    spec = importlib.util.spec_from_file_location("_return_logit_variants", path)
    if not spec or not spec.loader:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    variants = getattr(module, "VARIANTS", None) or getattr(module, "CANDIDATES", None)
    if not isinstance(variants, dict) or not variants:
        raise TypeError("VARIANTSまたはCANDIDATES dictが必要です")
    arguments = getattr(module, "TOOL_ARGUMENTS", None)
    if arguments is None:
        def default_arguments(_name: str, recipient: str) -> dict[str, Any]:
            return {"subject": "", "body": "", "to": recipient}

        arguments = default_arguments
    if not callable(arguments):
        raise TypeError("TOOL_ARGUMENTSはcallableにしてください")
    return variants, arguments


def _backend_from_factory(agent_factory: Any) -> Any:
    for cell in getattr(agent_factory, "__closure__", None) or ():
        value = cell.cell_contents
        if hasattr(value, "llm"):
            return value
    raise RuntimeError("agent_factory closureからbackendを取得できません")


def _render_prompt(agent: Any, llm: Any, history: RuntimeHistory, tools: tuple[Any, ...]) -> list[int]:
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
    return llm.tokenize(rendered.prompt.encode(), add_bos=not rendered.added_special, special=True)


def _current_logits(llm: Any) -> np.ndarray:
    return np.ctypeslib.as_array(llm._ctx.get_logits(), shape=(llm.n_vocab(),)).copy()


def _piece(llm: Any, token_id: int) -> str:
    return llm.detokenize([token_id], special=True).decode("utf-8", errors="replace")


def _token_stats(logits: np.ndarray, token_id: int) -> dict[str, float | int]:
    target = float(logits[token_id])
    maximum = float(np.max(logits))
    logsumexp = maximum + math.log(float(np.exp(logits - maximum).sum()))
    return {
        "id": token_id,
        "rank": int(np.count_nonzero(logits > target)) + 1,
        "logp": round(target - logsumexp, 6),
        "margin_to_top": round(target - maximum, 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants-file", required=True)
    parser.add_argument("--recipients", default="a")
    parser.add_argument("--top-k", type=int, default=12)
    parser.add_argument("--out", default="gpt_return_logit_probe.json")
    args = parser.parse_args()

    variants, tool_arguments = _load_variants(args.variants_file)
    recipients = tuple(dict.fromkeys(value.strip() for value in args.recipients.split(",") if value.strip()))
    if not recipients:
        raise ValueError("recipientが空です")

    fixtures_dir = ed.ops.resolve_fixtures_dir(None)
    factory = ed.build_agent_factory("gpt_oss")
    backend = _backend_from_factory(factory)
    llm = backend.llm
    suite = ToolSuite(fixtures_dir)
    tools = to_agent_tool_specs(tuple(suite.specs.values()))
    return_ids = llm.tokenize(b"<|return|>", add_bos=False, special=True)
    dot_ids = llm.tokenize(b".", add_bos=False, special=True)
    if len(return_ids) != 1 or len(dot_ids) != 1:
        raise RuntimeError(f"stop tokenのtokenizeが想定外です: return={return_ids}, dot={dot_ids}")

    results: dict[str, Any] = {}
    for name, builder in variants.items():
        rows: list[dict[str, Any]] = []
        for recipient in recipients:
            message = builder(recipient)
            arguments = tool_arguments(name, recipient)
            call = ToolCall(call_id="call_000001", tool_name="email.send", arguments=arguments)
            history = (
                RuntimeHistory()
                .with_instruction(_DEFAULT_RUNTIME_INSTRUCTIONS)
                .with_user_message(message)
                .with_tool_request(call)
                .with_tool_result(
                    ToolResult(
                        call_id=call.call_id,
                        tool_name=call.tool_name,
                        output_text="sent",
                        is_error=False,
                    )
                )
            )
            prompt_ids = _render_prompt(factory(), llm, history, tools)
            llm.reset()
            llm.eval(prompt_ids)
            logits = _current_logits(llm)
            top_ids = np.argpartition(logits, -args.top_k)[-args.top_k :]
            top_ids = top_ids[np.argsort(logits[top_ids])[::-1]]
            rows.append(
                {
                    "recipient": recipient,
                    "prompt_tokens": len(prompt_ids),
                    "return": _token_stats(logits, return_ids[0]),
                    "dot": _token_stats(logits, dot_ids[0]),
                    "top": [
                        {
                            "id": int(token_id),
                            "piece": _piece(llm, int(token_id)),
                            "logit": round(float(logits[token_id]), 6),
                        }
                        for token_id in top_ids
                    ],
                }
            )
        results[name] = {
            "message": builder(recipients[0]),
            "message_tokens": len(llm.tokenize(builder(recipients[0]).encode(), add_bos=False, special=True)),
            "return_rank_max": max(row["return"]["rank"] for row in rows),
            "return_logp_mean": round(sum(row["return"]["logp"] for row in rows) / len(rows), 6),
            "rows": rows,
        }
        print(
            f"[return] {name:24} tok={results[name]['message_tokens']:3} "
            f"rank_max={results[name]['return_rank_max']:6} "
            f"logp_mean={results[name]['return_logp_mean']:.4f}"
        )

    payload = {
        "model": "gpt_oss",
        "variants_file": str(Path(args.variants_file).resolve()),
        "recipients": recipients,
        "return_token_id": return_ids[0],
        "dot_token_id": dot_ids[0],
        "results": results,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"[return] saved {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
