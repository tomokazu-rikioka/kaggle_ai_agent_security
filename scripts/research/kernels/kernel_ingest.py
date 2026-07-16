"""CLI: 公式 kaggle CLI でコンペの公開カーネル一覧を収集し kernels.db へ保存する。

使い方:
    uv run python scripts/research/kernels/kernel_ingest.py <comp> [--max-pages N]
        [--sort-by voteCount|hotness|dateRun|...] [--page-size N]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.research.common.config import COMPETITION_SLUG, KERNELS_DB  # noqa: E402
from scripts.research.common.db import connect, init_db, upsert  # noqa: E402
from scripts.research.common.kaggle_cli import kaggle_list_csv  # noqa: E402
from scripts.research.kernels.schema import KERNELS_DDL  # noqa: E402


def list_kernels(comp: str, *, sort_by: str, page_size: int, max_pages: int) -> list[dict[str, str]]:
    """`kaggle kernels list` をページングして CSV 行を集める。空ページで打ち切る。"""
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        args = [
            "kernels",
            "list",
            "--competition",
            comp,
            "--sort-by",
            sort_by,
            "--page-size",
            str(page_size),
            "--page",
            str(page),
        ]
        page_rows = kaggle_list_csv(args)
        if not page_rows:
            break
        new = [r for r in page_rows if r.get("ref") and r["ref"] not in seen]
        if not new:
            break
        for r in new:
            seen.add(r["ref"])
        rows.extend(new)
        if len(page_rows) < page_size:
            break
    return rows


def _to_int(value: str | None) -> int:
    """CSV 文字列を安全に int 化する（空/非数は 0）。"""
    try:
        return int(float(value)) if value not in (None, "") else 0
    except (TypeError, ValueError):
        return 0


def ingest(comp: str, *, sort_by: str, page_size: int, max_pages: int) -> int:
    """一覧を取得して kernels テーブルへ追加または更新（upsert）する。取り込み件数を返す。"""
    rows = list_kernels(comp, sort_by=sort_by, page_size=page_size, max_pages=max_pages)
    now = datetime.now(UTC).isoformat()
    conn = connect(KERNELS_DB)
    try:
        init_db(conn, KERNELS_DDL)
        for r in rows:
            ref = r.get("ref", "")
            author = ref.split("/", 1)[0] if "/" in ref else r.get("author", "")
            upsert(
                conn,
                "kernels",
                {
                    "competition_id": comp,
                    "kernel_ref": ref,
                    "title": r.get("title", ""),
                    "author": author,
                    "total_votes": _to_int(r.get("totalVotes")),
                    "last_run_time": r.get("lastRunTime", ""),
                    "is_private": 0,
                    "ingested_at": now,
                },
                pk=("competition_id", "kernel_ref"),
            )
        _upsert_competition(conn, comp, now)
        conn.commit()
    finally:
        conn.close()
    return len(rows)


def _upsert_competition(conn: sqlite3.Connection, comp: str, now: str) -> None:
    """competition_info を最小限更新する。"""
    upsert(
        conn,
        "competition_info",
        {"competition_id": comp, "title": comp, "updated_at": now},
        pk=("competition_id",),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="公開カーネル一覧を収集し kernels.db に保存")
    ap.add_argument("comp", nargs="?", default=COMPETITION_SLUG, help="コンペ slug")
    ap.add_argument("--sort-by", default="voteCount", help="kaggle kernels list --sort-by の値")
    ap.add_argument("--page-size", type=int, default=100, help="1 ページの件数（~100 上限）")
    ap.add_argument("--max-pages", type=int, default=5, help="最大ページ数")
    args = ap.parse_args()

    count = ingest(
        args.comp,
        sort_by=args.sort_by,
        page_size=args.page_size,
        max_pages=args.max_pages,
    )
    print(f"[research] {count} 件のカーネルを {KERNELS_DB} に保存した。")


if __name__ == "__main__":
    main()
