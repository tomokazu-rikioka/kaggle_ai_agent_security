"""r192の候補別N=3測定について、順序をまたぐ再現性を解析する。"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path


def _ranks(values: list[float]) -> list[float]:
    """同値へ平均順位を与える。"""

    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + end - 1) / 2 + 1
        for index in order[start:end]:
            ranks[index] = rank
        start = end
    return ranks


def _correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return math.nan
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True))
    left_sum = sum((x - left_mean) ** 2 for x in left)
    right_sum = sum((y - right_mean) ** 2 for y in right)
    denominator = math.sqrt(left_sum * right_sum)
    return numerator / denominator if denominator else math.nan


def _spearman(left: list[float], right: list[float]) -> float:
    return _correlation(_ranks(left), _ranks(right))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranked", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    ranked_payload = json.loads(args.ranked.read_text())
    ranked = ranked_payload["ranked"]
    per_order = {
        order_name: [
            next(float(item["seconds"]) for item in row["measurements"] if item["order"] == order_name)
            for row in ranked
        ]
        for order_name in ranked_payload["measurement_orders"]
    }
    main_stable = {row["recipient"] for row in ranked if row["stable"]}

    pairwise = {}
    order_names = list(per_order)
    for left_index, left_name in enumerate(order_names):
        for right_name in order_names[left_index + 1 :]:
            left = per_order[left_name]
            right = per_order[right_name]
            pairwise[f"{left_name}_vs_{right_name}"] = {
                "pearson": round(_correlation(left, right), 6),
                "spearman": round(_spearman(left, right), 6),
                "fastest_set_overlap": {
                    str(count): len(
                        set(sorted(range(len(left)), key=left.__getitem__)[:count])
                        & set(sorted(range(len(right)), key=right.__getitem__)[:count])
                    )
                    for count in (50, 100, 250, 500, 1_000)
                },
            }

    means = [float(row["mean_s"]) for row in ranked]
    fastest_n3 = [row["recipient"] for row in sorted(ranked, key=lambda row: row["mean_s"])]

    result = {
        "model": ranked_payload["model"],
        "recipients": len(ranked),
        "stable_main_n3": len(main_stable),
        "pairwise_run_reproducibility": pairwise,
        "n3_mean_seconds": round(statistics.fmean(means), 6),
        "n3_min_seconds": round(min(means), 6),
        "n3_max_seconds": round(max(means), 6),
        "fastest_n3_top20": fastest_n3[:20],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
