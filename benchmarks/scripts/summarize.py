"""ラウンドの bench_results.json を Markdown 表に変換する（docs へ貼るため）。

使い方:
    uv run python benchmarks/scripts/summarize.py benchmarks/scripts/gpt/results/r1.json
    uv run python benchmarks/scripts/summarize.py benchmarks/scripts/gpt/results/*.json --guardrail public
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def render(path: Path, guardrail_filter: str | None) -> str:
    data = json.loads(path.read_text())
    model = data.get("model")
    n = data.get("candidates_per_variant")
    lines = [
        f"### {path.stem} — model=`{model}`, N={n}",
        "",
        "| variant | guardrail | fire | emit_ok | emit_any | mean_s | raw | cells | len |",
        "|---|---|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for vname, v in data.get("results", {}).items():
        slen = v.get("sample_len", "")
        for gname, g in v.get("guardrails", {}).items():
            if guardrail_filter and gname != guardrail_filter:
                continue
            lines.append(
                f"| {vname} | {gname} | {g['fire_rate']:.3f} | {g.get('emit_ok_rate', 0):.3f} "
                f"| {g.get('emit_any_rate', 0):.3f} | {g['replay_mean_s']:.2f} "
                f"| {g['score_raw']:.1f} | {g['unique_cells']} | {slen} |"
            )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--guardrail", default=None, help="この guardrail だけ表に出す（public 等）")
    args = ap.parse_args()
    blocks = [render(p, args.guardrail) for p in args.paths if p.is_file()]
    print("\n\n".join(blocks))


if __name__ == "__main__":
    main()
