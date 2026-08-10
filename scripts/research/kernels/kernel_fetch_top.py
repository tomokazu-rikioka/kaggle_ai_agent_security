"""CLI: LB スコア上位 N 件の公開カーネル本文を取得してキャッシュする。

kernels.db の `best_public_score` 降順で N 件を選び、`kaggle kernels pull` で
`data/notebooks/<comp>/<owner>__<slug>/` に .ipynb を落とす。読むのは
`make research-kernel-read REF=owner/slug`（キャッシュがあれば再取得しない）。

使い方:
    uv run python scripts/research/kernels/kernel_fetch_top.py [comp] [--top 30] [--force]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.research.common.config import COMPETITION_SLUG, KERNELS_DB  # noqa: E402
from scripts.research.common.db import connect  # noqa: E402
from scripts.research.kernels.kernel_read import cache_dir_for, pull_kernel  # noqa: E402

PULL_INTERVAL_S = 2.0
PULL_RETRIES = 3


def top_kernels(comp: str, *, top: int) -> list[tuple[str, float, str]]:
    """スコアが付いているカーネルを降順に N 件返す（ref, score, title）。"""
    conn = connect(KERNELS_DB)
    try:
        rows = conn.execute(
            "select kernel_ref, best_public_score, title from kernels "
            "where competition_id = ? and best_public_score is not null "
            "order by best_public_score desc limit ?",
            (comp, top),
        ).fetchall()
    finally:
        conn.close()
    return [(r[0], r[1], r[2]) for r in rows]


def fetch_top(comp: str, *, top: int, force: bool) -> int:
    """上位 N 件の本文を取得する。取得できた件数を返す。"""
    targets = top_kernels(comp, top=top)
    if not targets:
        print("[research] スコア付きのカーネルが無い。先に kernel_ingest.py を実行すること。")
        return 0

    fetched = 0
    for i, (ref, score, title) in enumerate(targets, 1):
        dest = cache_dir_for(comp, ref)
        for attempt in range(1, PULL_RETRIES + 1):
            try:
                pull_kernel(ref, dest, force=force)
                fetched += 1
                print(f"[research] {i:2d}. score={score:>7} {ref}  {title[:40]}")
                break
            except RuntimeError as exc:
                if attempt == PULL_RETRIES:
                    print(f"[research] {i:2d}. score={score:>7} {ref} の取得に失敗: {exc}")
                else:
                    wait = PULL_INTERVAL_S * attempt * 5
                    print(f"[research]     pull 失敗、{wait:.0f}s 待って再試行 {attempt}/{PULL_RETRIES - 1}")
                    time.sleep(wait)
        time.sleep(PULL_INTERVAL_S)  # 連続 pull はレート制限に当たりやすい
    print(f"\n[research] {fetched}/{len(targets)} 件の本文を {KERNELS_DB.parent}/notebooks に取得した。")
    return fetched


def main() -> None:
    ap = argparse.ArgumentParser(description="LB スコア上位 N 件のカーネル本文を取得")
    ap.add_argument("comp", nargs="?", default=COMPETITION_SLUG, help="コンペ slug")
    ap.add_argument("--top", type=int, default=30, help="取得する件数")
    ap.add_argument("--force", action="store_true", help="キャッシュを無視して再取得")
    args = ap.parse_args()
    fetch_top(args.comp, top=args.top, force=args.force)


if __name__ == "__main__":
    main()
