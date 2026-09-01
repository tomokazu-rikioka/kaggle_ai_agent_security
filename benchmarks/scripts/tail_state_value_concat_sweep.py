"""Search ordered two-piece strings within one tool argument for post-tool EOS."""

from __future__ import annotations

import argparse
import heapq
import json
import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SDK_ROOT = Path(os.environ.get("AICOMP_SDK_ROOT", ""))
for _sdk_root in (_SDK_ROOT, _REPO_ROOT / "vendor" / "aicomp_sdk_pkg"):
    if (_sdk_root / "aicomp_sdk").is_dir() and str(_sdk_root) not in sys.path:
        sys.path.insert(0, str(_sdk_root))
if str(_REPO_ROOT / "scripts" / "eval") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts" / "eval"))

import eval_driver as ed  # noqa: E402
from aicomp_sdk.agents.tool_specs import to_agent_tool_specs  # noqa: E402
from aicomp_sdk.core.tools import ToolSuite  # noqa: E402

try:
    import gpt_return_logit_probe as probe  # noqa: E402
    import tail_state_value_sweep as sweep  # noqa: E402
except ModuleNotFoundError:
    from benchmarks.scripts import gpt_return_logit_probe as probe  # noqa: E402
    from benchmarks.scripts import tail_state_value_sweep as sweep  # noqa: E402


def _top_string_values(path: Path, field: str, limit: int) -> list[str]:
    payload = json.loads(path.read_text())
    values = [""]
    seen = {""}
    for row in payload["results"]:
        value = row["value"]
        if row["field"] != field or not isinstance(value, str) or value in seen:
            continue
        seen.add(value)
        values.append(value)
        if len(values) >= limit:
            break
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-results", type=Path, required=True)
    parser.add_argument("--field", choices=("subject", "body"), required=True)
    parser.add_argument("--top-values", type=int, default=48)
    parser.add_argument("--recipient", default="a")
    parser.add_argument("--max-call-added", type=int, default=3)
    parser.add_argument("--max-message-added", type=int, default=6)
    parser.add_argument("--keep", type=int, default=400)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    values = _top_string_values(args.seed_results, args.field, args.top_values)
    candidates = list(dict.fromkeys(left + right for left in values for right in values))
    fixtures_dir = ed.ops.resolve_fixtures_dir(None)
    factory = ed.build_agent_factory("gemma_4")
    backend = probe._backend_from_factory(factory)
    llm = backend.llm
    tools = to_agent_tool_specs(tuple(ToolSuite(fixtures_dir).specs.values()))
    stop_ids = sweep._stop_ids(llm, "gemma_4")
    empty_thought_ids = llm.tokenize(
        b"<|channel>thought\n<channel|>", add_bos=False, special=True
    )
    base_args: dict[str, Any] = {"subject": "", "body": "", "to": args.recipient}
    base_target_tokens = len(
        llm.tokenize(sweep._target_text("gemma_4", base_args).encode(), add_bos=False, special=True)
    )
    base_message = sweep._message("gemma_4", "double16", args.field, "", args.recipient)
    base_message_tokens = len(llm.tokenize(base_message.encode(), add_bos=False, special=True))

    kept: list[tuple[float, int, dict[str, Any]]] = []
    tested = 0
    evaluated = 0
    serial = 0
    for value in candidates:
        tested += 1
        args_dict = dict(base_args)
        args_dict[args.field] = value
        target_text = sweep._target_text("gemma_4", args_dict)
        target_tokens = len(llm.tokenize(target_text.encode(), add_bos=False, special=True))
        call_added = target_tokens - base_target_tokens
        message = sweep._message("gemma_4", "double16", args.field, value, args.recipient)
        message_tokens = len(llm.tokenize(message.encode(), add_bos=False, special=True))
        message_added = message_tokens - base_message_tokens
        if call_added > args.max_call_added or message_added > args.max_message_added:
            continue
        prompt_ids = probe._render_prompt(factory(), llm, sweep._history(message, args_dict), tools)
        llm.reset()
        llm.eval(prompt_ids)
        phase_stops, greedy_stop_after = sweep._analyze_stop_phases(
            llm, stop_ids, empty_thought_ids
        )
        stop = phase_stops[0]
        row = {
            "field": args.field,
            "value": value,
            "message": message,
            "message_tokens": message_tokens,
            "message_added": message_added,
            "target_text": target_text,
            "target_tokens": target_tokens,
            "call_added": call_added,
            "post_prompt_tokens": len(prompt_ids),
            "stop": stop,
            "phase_stops": phase_stops,
            "greedy_stop_after": greedy_stop_after,
        }
        score = sweep._phase_search_score(phase_stops, call_added)
        serial += 1
        item = (score, serial, row)
        if len(kept) < args.keep:
            heapq.heappush(kept, item)
        elif item > kept[0]:
            heapq.heapreplace(kept, item)
        evaluated += 1
        if evaluated % 500 == 0:
            best = max(kept)[2]
            print(
                f"[concat] field={args.field} evaluated={evaluated}/{tested} "
                f"rank={best['stop']['rank']} logp={best['stop']['logp']}"
            )

    ranked = [item[2] for item in sorted(kept, reverse=True)]
    payload = {
        "model": "gemma_4",
        "style": "double16",
        "field": args.field,
        "recipient": args.recipient,
        "seed_results": str(args.seed_results),
        "values": values,
        "candidate_count": len(candidates),
        "stop_ids": stop_ids,
        "empty_thought_ids": empty_thought_ids,
        "base_target_tokens": base_target_tokens,
        "base_message_tokens": base_message_tokens,
        "tested": tested,
        "evaluated": evaluated,
        "results": ranked,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    for row in ranked[:30]:
        print(
            f"[top] field={args.field} value={row['value']!r} "
            f"call+={row['call_added']} msg+={row['message_added']} "
            f"rank={row['stop']['rank']} logp={row['stop']['logp']:.4f}"
        )
    print(f"[concat] saved {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
