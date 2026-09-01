"""Measure whether per-recipient latency is stable enough to improve deadline ordering.

AB/BA benchmark files contain identical ``*_a``/``*_b`` variants over the same
recipient order.  The first copy is treated as training data and the second as
an independent test.  We compare original, train-latency-sorted, completion-
stability-sorted, and test-oracle ordering at several deadline fractions.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def _rank(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), dtype=float)
    ranks[order] = np.arange(len(values), dtype=float)
    return ranks


def _corr(left: np.ndarray, right: np.ndarray) -> float | None:
    if len(left) < 3 or np.std(left) == 0 or np.std(right) == 0:
        return None
    return float(np.corrcoef(left, right)[0, 1])


def _rolling_median_residual(values: np.ndarray, radius: int = 25) -> np.ndarray:
    residual = np.empty_like(values)
    for index in range(len(values)):
        lo = max(0, index - radius)
        hi = min(len(values), index + radius + 1)
        residual[index] = values[index] - np.median(values[lo:hi])
    return residual


def _completed(order: np.ndarray, seconds: np.ndarray, budget: float) -> int:
    cumulative = np.cumsum(seconds[order])
    return int(np.searchsorted(cumulative, budget, side="right"))


def _completion_cost(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.split(">"))
    except ValueError:
        return (10**9,)


def _analyse_pair(path: Path, stem: str, first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any] | None:
    left = first["guardrails"].get("public")
    right = second["guardrails"].get("public")
    if not left or not right:
        return None
    x = np.asarray(left.get("replay_seconds", ()), dtype=float)
    y = np.asarray(right.get("replay_seconds", ()), dtype=float)
    left_diag = left.get("recipient_diagnostics", ())
    right_diag = right.get("recipient_diagnostics", ())
    size = min(len(x), len(y), len(left_diag), len(right_diag))
    if size < 3:
        return None
    x = x[:size]
    y = y[:size]
    left_diag = left_diag[:size]
    right_diag = right_diag[:size]
    if any(a.get("recipient") != b.get("recipient") for a, b in zip(left_diag, right_diag, strict=True)):
        return None

    x_residual = _rolling_median_residual(x)
    y_residual = _rolling_median_residual(y)
    original = np.arange(size)
    latency_order = np.argsort(x_residual, kind="stable")
    stable_order = np.asarray(
        sorted(
            range(size),
            key=lambda i: (
                not bool(left_diag[i].get("fire")),
                not bool(left_diag[i].get("email_to_exact")),
                _completion_cost(str(left_diag[i].get("completion_tokens", ""))),
                x_residual[i],
            ),
        ),
        dtype=int,
    )
    oracle = np.argsort(y, kind="stable")
    deadlines: dict[str, Any] = {}
    for fraction in (0.5, 0.75, 0.9, 0.95, 0.99):
        budget = float(y.sum() * fraction)
        counts = {
            "original": _completed(original, y, budget),
            "train_latency": _completed(latency_order, y, budget),
            "train_stability": _completed(stable_order, y, budget),
            "oracle": _completed(oracle, y, budget),
        }
        deadlines[f"{fraction:.2f}"] = {
            "budget_s": round(budget, 6),
            **counts,
            "latency_delta": counts["train_latency"] - counts["original"],
            "stability_delta": counts["train_stability"] - counts["original"],
        }

    fastest = latency_order[: math.ceil(size * 0.8)]
    return {
        "file": str(path),
        "model": "gpt_oss" if path.name.startswith("gpt_") else "gemma_4",
        "variant": stem,
        "n": size,
        "raw_pearson": _corr(x, y),
        "raw_spearman": _corr(_rank(x), _rank(y)),
        "detrended_pearson": _corr(x_residual, y_residual),
        "detrended_spearman": _corr(_rank(x_residual), _rank(y_residual)),
        "test_mean_s": float(y.mean()),
        "train_fastest80_test_mean_s": float(y[fastest].mean()),
        "train_fastest80_test_delta_s": float(y[fastest].mean() - y.mean()),
        "train_noncanonical": sum(
            not row.get("fire") or not row.get("email_to_exact") for row in left_diag
        ),
        "test_noncanonical": sum(
            not row.get("fire") or not row.get("email_to_exact") for row in right_diag
        ),
        "deadlines": deadlines,
    }


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    weighted_n = sum(row["n"] for row in rows)
    return {
        "pairs": len(rows),
        "total_candidates": weighted_n,
        "weighted_detrended_spearman": (
            sum((row["detrended_spearman"] or 0.0) * row["n"] for row in rows) / weighted_n
            if weighted_n
            else None
        ),
        "deadline_deltas": {
            fraction: {
                "train_latency": sum(row["deadlines"][fraction]["latency_delta"] for row in rows),
                "train_stability": sum(row["deadlines"][fraction]["stability_delta"] for row in rows),
            }
            for fraction in ("0.50", "0.75", "0.90", "0.95", "0.99")
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    analyses: list[dict[str, Any]] = []
    for path in args.paths:
        payload = json.loads(path.read_text())
        results = payload.get("results", {})
        if not isinstance(results, dict):
            continue
        for name, first in results.items():
            if not isinstance(name, str) or not name.endswith("_a"):
                continue
            stem = name[:-2]
            second = results.get(stem + "_b")
            if second is None:
                continue
            row = _analyse_pair(path, stem, first, second)
            if row is not None:
                analyses.append(row)

    summary = {
        "all": _summarize(analyses),
        "gpt_oss": _summarize([row for row in analyses if row["model"] == "gpt_oss"]),
        "gemma_4": _summarize([row for row in analyses if row["model"] == "gemma_4"]),
        "canonical_n100": _summarize(
            [
                row
                for row in analyses
                if row["n"] >= 100
                and row["train_noncanonical"] == 0
                and row["test_noncanonical"] == 0
            ]
        ),
    }
    output = {"summary": summary, "analyses": analyses}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for row in analyses:
        print(
            f"[pair] {Path(row['file']).name}:{row['variant']} n={row['n']} "
            f"rho={row['detrended_spearman']!s} "
            f"fast80_delta={row['train_fastest80_test_delta_s']:+.6f}s"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
