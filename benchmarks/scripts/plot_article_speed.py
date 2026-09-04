"""記事用のGPT/Gemma累積raw/s散布図を生成する。"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D

GPT_STAGES = (
    "s0_direct",
    "s1_model_format",
    "s2_analysis_tail",
    "s3_article_final",
    "s4_first_place",
)
GPT_LABELS = (
    "Direct CD",
    "+ Harmony / no final",
    "+ Analysis tail",
    "+ KV-tail (ours)",
    "1st prompt\n(shared recipients)",
)
GEMMA_STAGES = (
    "s0_direct",
    "s1_no_final",
    "s2_quote_control",
    "s3_article_final",
    "s4_first_place",
)
GEMMA_LABELS = (
    "Direct CD",
    "+ No final",
    "+ Quotes / recipient tail",
    "+ Short completion (ours)",
    "1st prompt\n(shared recipients)",
)
OUR_COLOR = "#2F6FB0"
FIRST_COLOR = "#D1495B"
GRID_COLOR = "#D9E1EA"
TEXT_COLOR = "#213547"
MUTED_COLOR = "#65758B"
GPT_PROBE_ALIASES = {
    "s0_direct": "s1_explicit_one_hop",
    "s1_model_format": "s2_model_format",
    "s2_analysis_tail": "p7_analysis",
    "s3_article_final": "s4_article_final",
    "s4_first_place": "ref_first_place",
}
GEMMA_PROBE_ALIASES = {
    "s0_direct": "s1_explicit_one_hop",
    "s1_no_final": "s2_no_final",
    "s2_quote_control": "s3_quote_control",
    "s3_article_final": "s4_article_final",
    "s4_first_place": "s5_first_place",
}


def _load(path: Path, expected_stages: tuple[str, ...], expected_n: int, probe_aliases: dict[str, str]) -> dict:
    payload = json.loads(path.read_text())
    if payload.get("candidates_per_variant") != expected_n:
        raise ValueError(f"N must be {expected_n}: {path}")
    if tuple(payload["results"]) != expected_stages:
        try:
            payload["results"] = {
                stage: payload["results"][probe_aliases.get(stage, stage)] for stage in expected_stages
            }
        except KeyError as error:
            raise ValueError(f"unexpected stage set: {path}: {tuple(payload['results'])}") from error
    return payload


def _rows(payload: dict, stages: tuple[str, ...]) -> list[dict[str, float]]:
    rows = []
    for stage in stages:
        result = payload["results"][stage]
        metrics = result.get("public") or result["guardrails"]["public"]
        stats = metrics["candidate_raw_per_s_stats"]
        rates = [float(value) for value in metrics.get("candidate_raw_per_s", [])]
        row = {name: float(stats[name]) for name in ("min", "max", "mean", "median")}
        row["std"] = statistics.stdev(rates) if len(rates) > 1 else float("nan")
        rows.append(row)
    return rows


def _panel(
    ax: plt.Axes,
    payload: dict,
    title: str,
    stages: tuple[str, ...],
    labels: tuple[str, ...],
    ours_count: int,
    spread: str,
) -> None:
    rows = _rows(payload, stages)
    x = list(range(len(rows)))
    means = [row["mean"] for row in rows]
    if spread == "std":
        if any(row["std"] != row["std"] for row in rows):
            raise ValueError("candidate-level raw/s values are required for standard-deviation whiskers")
        lower_errors = [row["std"] for row in rows]
        upper_errors = [row["std"] for row in rows]
    else:
        lower_errors = [row["mean"] - row["min"] for row in rows]
        upper_errors = [row["max"] - row["mean"] for row in rows]
    errors = [lower_errors, upper_errors]

    ax.errorbar(
        x[:ours_count],
        means[:ours_count],
        yerr=[lower_errors[:ours_count], upper_errors[:ours_count]],
        fmt="none",
        ecolor=OUR_COLOR,
        elinewidth=2.0,
        capsize=5,
        capthick=2.0,
        alpha=0.35,
        zorder=1,
    )
    ax.plot(
        x[:ours_count],
        means[:ours_count],
        color=OUR_COLOR,
        linewidth=2.8,
        marker="o",
        markeredgecolor="white",
        markeredgewidth=1.8,
        markersize=9,
        zorder=3,
    )
    if ours_count < len(x):
        ax.errorbar(
            x[ours_count:],
            means[ours_count:],
            yerr=[lower_errors[ours_count:], upper_errors[ours_count:]],
            fmt="none",
            ecolor=FIRST_COLOR,
            elinewidth=2.0,
            capsize=5,
            capthick=2.0,
            alpha=0.4,
            zorder=1,
        )
        ax.scatter(
            x[ours_count:],
            means[ours_count:],
            color=FIRST_COLOR,
            edgecolor="white",
            linewidth=1.6,
            s=115,
            marker="X",
            zorder=4,
        )

    upper = [mean + error for mean, error in zip(means, errors[1], strict=True)]
    lower = [max(0.0, mean - error) for mean, error in zip(means, errors[0], strict=True)]
    span = max(upper) - min(lower)
    label_offset = max(span * 0.035, max(upper) * 0.012, 0.12)
    for index, value in enumerate(means):
        color = OUR_COLOR if index < ours_count else FIRST_COLOR
        ax.text(
            index,
            upper[index] + label_offset,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            color=color,
            fontsize=9.5,
            fontweight="bold",
        )

    if ours_count < len(x):
        article_mean = means[ours_count - 1]
        first_mean = means[ours_count]
        gap = ((first_mean / article_mean) - 1.0) * 100 if article_mean else 0.0
        ax.text(
            0.985,
            0.62,
            f"1st prompt vs ours: {gap:+.1f}%",
            transform=ax.transAxes,
            color=FIRST_COLOR,
            fontsize=9,
            fontweight="bold",
            ha="right",
            va="bottom",
        )
    else:
        ax.text(
            0.98,
            0.03,
            "No separate reference prompt",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            color=FIRST_COLOR,
            fontsize=8.5,
        )
    ax.axvline(ours_count - 0.5, color=GRID_COLOR, linewidth=1.1, linestyle=(0, (3, 4)), zorder=0)
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=14)
    ax.set_xticks(x, labels)
    ax.tick_params(axis="x", labelrotation=0, pad=9, labelsize=9)
    ax.set_ylabel("Mean raw / second", color=TEXT_COLOR, labelpad=10)
    ax.set_xlim(-0.4, len(x) - 0.6)
    ax.set_ylim(bottom=min(-0.02 * max(upper), 0.0))
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8, alpha=0.75)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.tick_params(axis="y", colors=MUTED_COLOR, length=0)
    ax.margins(y=0.19)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpt", type=Path, required=True)
    parser.add_argument("--gemma", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-n", type=int, default=2_000)
    parser.add_argument("--spread", choices=("std", "range"), default="std")
    args = parser.parse_args()

    gpt = _load(args.gpt, GPT_STAGES, args.expected_n, GPT_PROBE_ALIASES)
    gemma = _load(args.gemma, GEMMA_STAGES, args.expected_n, GEMMA_PROBE_ALIASES)
    sns.set_theme(style="white", context="notebook")
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": "white", "axes.facecolor": "#F8FAFC"})
    figure, axes = plt.subplots(2, 1, figsize=(12.8, 10.2), constrained_layout=True, sharey=True)
    _panel(axes[0], gpt, "GPT-OSS 20B", GPT_STAGES, GPT_LABELS, ours_count=4, spread=args.spread)
    _panel(axes[1], gemma, "Gemma 4 26B-A4B-it", GEMMA_STAGES, GEMMA_LABELS, ours_count=4, spread=args.spread)
    figure.suptitle(
        f"Prompt optimization compounds into higher throughput  ·  N={args.expected_n:,}",
        fontsize=17,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    figure.legend(
        handles=(
            Line2D([0], [0], color=OUR_COLOR, marker="o", label="Our cumulative stages (mean)"),
            Line2D(
                [0],
                [0],
                color=FIRST_COLOR,
                marker="X",
                linestyle="none",
                label="1st-place prompt (mean)",
            ),
            Line2D(
                [0],
                [0],
                color=OUR_COLOR,
                alpha=0.35,
                marker="|",
                markersize=14,
                label="±1 standard deviation" if args.spread == "std" else "Observed min–max",
            ),
        ),
        loc="outside lower center",
        ncol=3,
        frameon=False,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.out, dpi=200, bbox_inches="tight")
    figure.savefig(args.out.with_suffix(".svg"), bbox_inches="tight")
    print(f"saved {args.out} and {args.out.with_suffix('.svg')}")


if __name__ == "__main__":
    main()
