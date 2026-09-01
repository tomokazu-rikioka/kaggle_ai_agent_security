"""Combine the best one-piece Gemma post-tool EOS prompt triggers.

The full-vocabulary pass is a first-order search.  This script evaluates both
same-position concatenations and cross-position pairs from its top unique
pieces, while retaining only candidates within a small prompt-token budget.
"""

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
    import gemma_tail_trigger_sweep as sweep  # noqa: E402
    import gpt_return_logit_probe as probe  # noqa: E402
except ModuleNotFoundError:
    from benchmarks.scripts import gemma_tail_trigger_sweep as sweep  # noqa: E402
    from benchmarks.scripts import gpt_return_logit_probe as probe  # noqa: E402


def _message(style: str, recipient: str, first: str, second: str, layout: str) -> str:
    baseline = sweep._BASELINES[style].format(recipient=recipient)
    if layout == "finish":
        return baseline.replace("Finish", first + second + "Finish", 1)
    if layout == "to":
        return baseline.replace('to:"', first + second + 'to:"', 1)
    if layout == "replace":
        return baseline.replace("Finish", first + second, 1)
    if layout == "finish_to":
        return baseline.replace("Finish", first + "Finish", 1).replace('to:"', second + 'to:"', 1)
    if layout == "to_finish":
        return baseline.replace("Finish", second + "Finish", 1).replace('to:"', first + 'to:"', 1)
    raise ValueError(layout)


def _unique_pieces(path: Path, limit: int) -> list[str]:
    payload = json.loads(path.read_text())
    pieces: list[str] = []
    seen: set[str] = set()
    for row in payload["results"]:
        piece = row["piece"]
        if piece in seen:
            continue
        seen.add(piece)
        pieces.append(piece)
        if len(pieces) >= limit:
            break
    return pieces


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-results", type=Path, required=True)
    parser.add_argument("--style", choices=tuple(sweep._BASELINES), default="double16")
    parser.add_argument("--recipient", default="a")
    parser.add_argument("--top-pieces", type=int, default=48)
    parser.add_argument("--layouts", default="finish,to,replace,finish_to,to_finish")
    parser.add_argument("--max-added", type=int, default=3)
    parser.add_argument("--keep", type=int, default=400)
    parser.add_argument("--out", default="gemma_tail_pair_sweep.json")
    args = parser.parse_args()

    pieces = _unique_pieces(args.seed_results, args.top_pieces)
    layouts = tuple(item.strip() for item in args.layouts.split(",") if item.strip())
    fixtures_dir = ed.ops.resolve_fixtures_dir(None)
    factory = ed.build_agent_factory("gemma_4")
    backend = probe._backend_from_factory(factory)
    llm = backend.llm
    tools = to_agent_tool_specs(tuple(ToolSuite(fixtures_dir).specs.values()))
    stop_ids = sweep._stop_ids(llm)
    baseline = sweep._BASELINES[args.style].format(recipient=args.recipient)
    baseline_tokens = len(llm.tokenize(baseline.encode(), add_bos=False, special=True))

    kept: list[tuple[float, int, dict[str, Any]]] = []
    tested = 0
    evaluated = 0
    serial = 0
    for first in pieces:
        for second in pieces:
            for layout in layouts:
                tested += 1
                message = _message(args.style, args.recipient, first, second, layout)
                message_tokens = len(llm.tokenize(message.encode(), add_bos=False, special=True))
                added = message_tokens - baseline_tokens
                if added > args.max_added:
                    continue
                prompt_ids = probe._render_prompt(
                    factory(), llm, sweep._history(message, args.recipient), tools
                )
                llm.reset()
                llm.eval(prompt_ids)
                stop = sweep._stats(probe._current_logits(llm), stop_ids)
                row = {
                    "first": first,
                    "second": second,
                    "layout": layout,
                    "message": message,
                    "message_tokens": message_tokens,
                    "added_tokens": added,
                    "post_prompt_tokens": len(prompt_ids),
                    "stop": stop,
                }
                score = float(stop["logp"]) - max(added, 0) * 0.02
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
                        f"[gemma-pair] evaluated={evaluated}/{tested} "
                        f"best={best['first']!r}+{best['second']!r}/{best['layout']} "
                        f"rank={best['stop']['rank']} logp={best['stop']['logp']}"
                    )

    ranked = [item[2] for item in sorted(kept, reverse=True)]
    payload = {
        "model": "gemma_4",
        "style": args.style,
        "recipient": args.recipient,
        "seed_results": str(args.seed_results),
        "pieces": pieces,
        "layouts": layouts,
        "stop_ids": stop_ids,
        "baseline": baseline,
        "baseline_tokens": baseline_tokens,
        "tested": tested,
        "evaluated": evaluated,
        "results": ranked,
    }
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    for row in ranked[:30]:
        print(
            f"[top] {row['first']!r}+{row['second']!r} {row['layout']:10} "
            f"added={row['added_tokens']} rank={row['stop']['rank']} "
            f"logp={row['stop']['logp']:.4f}"
        )
    print(f"[gemma-pair] saved {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
