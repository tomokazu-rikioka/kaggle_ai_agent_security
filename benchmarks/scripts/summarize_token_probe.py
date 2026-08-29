"""token probe JSONをtarget NLL順のMarkdown表へ変換する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def render(path: Path, limit: int | None) -> str:
    data = json.loads(path.read_text())
    marker = data.get("expected_marker", "")
    if marker == "to=functions.email_send":  # r13 GPTの旧表示用。実Harmony名はdot形式。
        marker = "to=functions.email.send"
    rows = sorted(data.get("results", {}).items(), key=lambda item: item[1]["target_mean_nll"])
    if limit is not None:
        rows = rows[:limit]
    lines = [
        f"### {path.stem} — model=`{data.get('model')}`, target_tokens={data.get('target_token_count')}",
        "",
        (
            "| candidate | input | edit_norm | desired out | target NLL | first logp | "
            "mean rank | preview max | exact rate |"
        ),
        "|---|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for name, result in rows:
        exact_rate = result.get("preview_exact_rate")
        if exact_rate is None:  # r16以前の互換表示
            exact = result.get("preview_exact_email")
            if exact is None:
                exact = bool(marker and marker in result.get("preview_text", ""))
            exact_rate = float(exact)
        preview_max = result.get("preview_token_count_max", result["preview_token_count"])
        desired_out = result.get("desired_target_token_count", data.get("target_token_count"))
        lines.append(
            f"| {name} | {result['message_token_count']} | {result['baseline_token_edit_normalized']:.3f} "
            f"| {desired_out} | {result['target_mean_nll']:.5f} | {result['target_first_logp']:.5f} "
            f"| {result['target_rank_mean']:.2f} "
            f"| {preview_max} | {exact_rate:.3f} |"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    print("\n\n".join(render(path, args.limit) for path in args.paths if path.is_file()))


if __name__ == "__main__":
    main()
