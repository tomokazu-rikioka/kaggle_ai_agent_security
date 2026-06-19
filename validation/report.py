"""検証結果のレポート整形。

提出 CSV を模した `{agent}_{guardrail}` 行のスコア表に加え、述語内訳・cell 数・
raw/正規化を表示する。score_attack / summarize_attack_findings（SDK）の値を使う。
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

PREDICATE_ORDER = [
    "EXFILTRATION",
    "UNTRUSTED_TO_ACTION",
    "DESTRUCTIVE_WRITE",
    "CONFUSED_DEPUTY",
]


def predicate_breakdown(findings: Sequence[Mapping[str, Any]]) -> Counter:
    """findings 全体の述語名ごとの発火回数。"""
    counter: Counter = Counter()
    for f in findings:
        for p in f.get("predicates", []):
            counter[p.get("predicate", "?")] += 1
    return counter


def format_report(
    *,
    agent: str,
    n_candidates: int,
    seed: int,
    env_selection: str,
    rows: Sequence[Mapping[str, Any]],
) -> str:
    """rows: 各要素 {guardrail, summary(dict), breakdown(Counter)}。整形済み文字列を返す。"""
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("ローカル検証レポート — AI Agent Security")
    lines.append("=" * 72)
    lines.append(f"agent={agent}  candidates={n_candidates}  seed={seed}  env={env_selection}")
    lines.append("")

    # --- スコア表（提出 CSV 形式の行 id） ---
    header = f"{'row id':28} {'score':>9} {'raw':>10} {'findings':>9} {'cells':>7}"
    lines.append(header)
    lines.append("-" * len(header))
    for r in rows:
        gr = r["guardrail"]
        s = r["summary"]
        row_id = f"{agent}_{gr}"
        lines.append(
            f"{row_id:28} {s['score']:>9.3f} {s['score_raw']:>10.1f} "
            f"{s['findings_count']:>9} {s['unique_cells']:>7}"
        )
    lines.append("")

    # --- 述語内訳（ガードレール別） ---
    lines.append("述語内訳（発火回数）:")
    pred_header = f"{'guardrail':12}" + "".join(f"{p[:14]:>16}" for p in PREDICATE_ORDER)
    lines.append(pred_header)
    lines.append("-" * len(pred_header))
    for r in rows:
        bd = r["breakdown"]
        cells = f"{r['guardrail']:12}"
        cells += "".join(f"{bd.get(p, 0):>16}" for p in PREDICATE_ORDER)
        lines.append(cells)
    lines.append("")

    # --- 解釈ガイド ---
    if any(r["guardrail"] in ("strict", "provenance") for r in rows):
        lines.append(
            "ヒント: public は公開 LB と相関する本命。strict/provenance は非公開汎化の代理 — "
        )
        lines.append(
            "        public で出て strict/provenance で消える攻撃は overfit の疑い。"
        )
    lines.append("=" * 72)
    return "\n".join(lines)
