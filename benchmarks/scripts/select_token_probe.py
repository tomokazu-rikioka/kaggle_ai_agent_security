"""複数token probe shardを統合し、完全一致候補のPareto前線と上位を保存する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    keys = ("message_token_count", "preview_token_count_max", "target_mean_nll")
    no_worse = all(float(left[key]) <= float(right[key]) for key in keys)
    strictly_better = any(float(left[key]) < float(right[key]) for key in keys)
    return no_worse and strictly_better


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--top", type=int, default=80)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    by_message: dict[str, dict[str, Any]] = {}
    for input_path in args.inputs:
        data = json.loads(Path(input_path).read_text())
        for name, result in data["results"].items():
            row = {"name": name, "source": input_path, **result}
            message = str(result["message"])
            previous = by_message.get(message)
            if previous is None or float(row["target_mean_nll"]) < float(previous["target_mean_nll"]):
                by_message[message] = row

    exact = [row for row in by_message.values() if row.get("preview_exact_rate") == 1.0]
    ordered = sorted(
        exact,
        key=lambda row: (
            int(row["preview_token_count_max"]),
            int(row["message_token_count"]),
            float(row["target_mean_nll"]),
            len(str(row["message"])),
        ),
    )
    pareto = [row for row in exact if not any(_dominates(other, row) for other in exact if other is not row)]
    pareto.sort(
        key=lambda row: (
            int(row["preview_token_count_max"]),
            int(row["message_token_count"]),
            float(row["target_mean_nll"]),
        )
    )

    def compact(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": row["name"],
            "source": row["source"],
            "message": row["message"],
            "message_token_count": row["message_token_count"],
            "preview_token_count": row["preview_token_count_max"],
            "target_mean_nll": row["target_mean_nll"],
            "target_first_logp": row["target_first_logp"],
            "baseline_token_edit": row["baseline_token_edit"],
        }

    payload = {
        "input_count": len(by_message),
        "exact_count": len(exact),
        "pareto_count": len(pareto),
        "pareto": [compact(row) for row in pareto],
        "top": [compact(row) for row in ordered[: args.top]],
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
