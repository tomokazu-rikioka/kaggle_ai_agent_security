"""Score the minimal second GPT tool call without sampling long failure paths.

The normal multi-hop screen can spend hundreds of tokens on a bad continuation.
This probe instead teacher-forces the desired 18-token call after the first
``email.send -> sent`` history and records its token-level likelihood.  It also
checks whether ``<|return|>`` is preferred after the second successful call.
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

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SDK_ROOT = Path(os.environ.get("AICOMP_SDK_ROOT", ""))
for _sdk_root in (_SDK_ROOT, _REPO_ROOT / "vendor" / "aicomp_sdk_pkg"):
    if (_sdk_root / "aicomp_sdk").is_dir() and str(_sdk_root) not in sys.path:
        sys.path.insert(0, str(_sdk_root))
if str(_REPO_ROOT / "scripts" / "eval") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts" / "eval"))

import eval_driver as ed  # noqa: E402
import gpt_return_logit_probe as probe  # noqa: E402
from aicomp_sdk.agents.tool_specs import to_agent_tool_specs  # noqa: E402
from aicomp_sdk.agents.types import ToolCall, ToolResult  # noqa: E402
from aicomp_sdk.core.env.sandbox import _DEFAULT_RUNTIME_INSTRUCTIONS  # noqa: E402
from aicomp_sdk.core.runtime_history import RuntimeHistory  # noqa: E402
from aicomp_sdk.core.tools import ToolSuite  # noqa: E402


def _load_variants(
    path_str: str,
) -> tuple[dict[str, Callable[[str], str]], Callable[[str, str], dict[str, Any]]]:
    path = Path(path_str).resolve()
    spec = importlib.util.spec_from_file_location("_two_call_target_variants", path)
    if not spec or not spec.loader:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    variants = getattr(module, "VARIANTS", None)
    if not isinstance(variants, dict) or not variants:
        raise TypeError("VARIANTS dictが必要です")
    arguments = getattr(module, "TOOL_ARGUMENTS", None)
    if arguments is None:

        def default_arguments(_name: str, recipient: str) -> dict[str, Any]:
            return {"subject": "", "body": "", "to": recipient}

        arguments = default_arguments
    if not callable(arguments):
        raise TypeError("TOOL_ARGUMENTSはcallableにしてください")
    return variants, arguments


def _history_after_calls(
    message: str,
    arguments: dict[str, Any],
    count: int,
) -> RuntimeHistory:
    history = RuntimeHistory().with_instruction(_DEFAULT_RUNTIME_INSTRUCTIONS).with_user_message(message)
    for index in range(count):
        call = ToolCall(
            call_id=f"call_{index + 1:06d}",
            tool_name="email.send",
            arguments=arguments,
        )
        history = history.with_tool_request(call).with_tool_result(
            ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                output_text="sent",
                is_error=False,
            )
        )
    return history


def _logp(logits: np.ndarray, token_id: int) -> tuple[float, float, int, int]:
    target = float(logits[token_id])
    maximum = float(np.max(logits))
    logsumexp = maximum + math.log(float(np.exp(logits - maximum).sum()))
    top_id = int(np.argmax(logits))
    rank = int(np.count_nonzero(logits > target)) + 1
    return target - logsumexp, target - maximum, rank, top_id


def _teacher_forced(llm: Any, prompt_ids: list[int], target_ids: list[int]) -> dict[str, Any]:
    llm.reset()
    llm.eval(prompt_ids)
    rows: list[dict[str, Any]] = []
    greedy_prefix = 0
    still_greedy = True
    total_nll = 0.0
    for index, token_id in enumerate(target_ids):
        logits = probe._current_logits(llm)
        logp, margin, rank, top_id = _logp(logits, token_id)
        if still_greedy and rank == 1:
            greedy_prefix += 1
        else:
            still_greedy = False
        total_nll -= logp
        rows.append(
            {
                "index": index,
                "target_id": token_id,
                "target_piece": probe._piece(llm, token_id),
                "rank": rank,
                "logp": round(logp, 6),
                "margin_to_top": round(margin, 6),
                "top_id": top_id,
                "top_piece": probe._piece(llm, top_id),
            }
        )
        llm.eval([token_id])
    return {
        "target_tokens": len(target_ids),
        "target_nll": round(total_nll, 6),
        "nll_per_token": round(total_nll / len(target_ids), 6),
        "greedy_prefix": greedy_prefix,
        "all_greedy": greedy_prefix == len(target_ids),
        "first_rank": rows[0]["rank"],
        "rows": rows,
    }


def _single_token_stats(llm: Any, prompt_ids: list[int], token_id: int) -> dict[str, Any]:
    llm.reset()
    llm.eval(prompt_ids)
    logp, margin, rank, top_id = _logp(probe._current_logits(llm), token_id)
    return {
        "id": token_id,
        "rank": rank,
        "logp": round(logp, 6),
        "margin_to_top": round(margin, 6),
        "top_id": top_id,
        "top_piece": probe._piece(llm, top_id),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants-file", required=True)
    parser.add_argument("--recipients", default="a,b,c")
    parser.add_argument("--out", default="gpt_two_call_target_probe.json")
    args = parser.parse_args()

    variants, tool_arguments = _load_variants(args.variants_file)
    recipients = tuple(dict.fromkeys(item.strip() for item in args.recipients.split(",") if item.strip()))
    if not recipients:
        raise ValueError("recipientが空です")

    fixtures_dir = ed.ops.resolve_fixtures_dir(None)
    factory = ed.build_agent_factory("gpt_oss")
    backend = probe._backend_from_factory(factory)
    llm = backend.llm
    tools = to_agent_tool_specs(tuple(ToolSuite(fixtures_dir).specs.values()))
    return_ids = llm.tokenize(b"<|return|>", add_bos=False, special=True)
    if len(return_ids) != 1:
        raise RuntimeError(f"<|return|> must be one token: {return_ids}")

    results: dict[str, Any] = {}
    for variant_index, (name, builder) in enumerate(variants.items(), start=1):
        recipient_rows = []
        for recipient in recipients:
            message = builder(recipient)
            arguments = tool_arguments(name, recipient)
            one_call_prompt = probe._render_prompt(
                factory(),
                llm,
                _history_after_calls(message, arguments, 1),
                tools,
            )
            target_text = (
                "<|channel|>commentary to=functions.email.send<|message|>"
                + json.dumps(arguments, ensure_ascii=False, separators=(",", ":"))
            )
            target_ids = llm.tokenize(target_text.encode(), add_bos=False, special=True)
            target = _teacher_forced(llm, one_call_prompt, target_ids)

            two_call_prompt = probe._render_prompt(
                factory(),
                llm,
                _history_after_calls(message, arguments, 2),
                tools,
            )
            finish = _single_token_stats(llm, two_call_prompt, return_ids[0])
            recipient_rows.append(
                {
                    "recipient": recipient,
                    "message": message,
                    "message_tokens": len(
                        llm.tokenize(message.encode(), add_bos=False, special=True)
                    ),
                    "one_call_prompt_tokens": len(one_call_prompt),
                    "target_text": target_text,
                    "target": target,
                    "two_call_prompt_tokens": len(two_call_prompt),
                    "finish_return": finish,
                }
            )

        results[name] = {
            "target_nll_mean": round(
                sum(row["target"]["target_nll"] for row in recipient_rows) / len(recipient_rows),
                6,
            ),
            "target_nll_max": max(row["target"]["target_nll"] for row in recipient_rows),
            "first_rank_max": max(row["target"]["first_rank"] for row in recipient_rows),
            "greedy_prefix_min": min(row["target"]["greedy_prefix"] for row in recipient_rows),
            "all_greedy_rate": round(
                sum(row["target"]["all_greedy"] for row in recipient_rows) / len(recipient_rows),
                6,
            ),
            "finish_return_rank_max": max(row["finish_return"]["rank"] for row in recipient_rows),
            "finish_return_logp_mean": round(
                sum(row["finish_return"]["logp"] for row in recipient_rows) / len(recipient_rows),
                6,
            ),
            "rows": recipient_rows,
        }
        if variant_index % 20 == 0 or variant_index == len(variants):
            ranked = sorted(
                results.items(),
                key=lambda item: (
                    -item[1]["all_greedy_rate"],
                    item[1]["target_nll_mean"],
                    item[1]["finish_return_rank_max"],
                ),
            )
            best_name, best = ranked[0]
            print(
                f"[two-call-target] {variant_index}/{len(variants)} best={best_name} "
                f"greedy={best['all_greedy_rate']:.3f} nll={best['target_nll_mean']:.3f} "
                f"finish_rank={best['finish_return_rank_max']}"
            )

    payload = {
        "model": "gpt_oss",
        "variants_file": str(Path(args.variants_file).resolve()),
        "recipients": recipients,
        "return_token_id": return_ids[0],
        "results": results,
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    ranked = sorted(
        results.items(),
        key=lambda item: (
            -item[1]["all_greedy_rate"],
            item[1]["target_nll_mean"],
            item[1]["finish_return_rank_max"],
        ),
    )
    print(
        "[top-json]",
        json.dumps(
            [
                {
                    "name": name,
                    **{key: value for key, value in row.items() if key != "rows"},
                }
                for name, row in ranked[:40]
            ],
            sort_keys=True,
        ),
    )
    print(f"[two-call-target] saved {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
