"""CLI: discussions.db を検索・フィルタして一覧表示する（kernel_query と対称）。

使い方:
    uv run python scripts/research/discussions/discussion_query.py <comp>
        [--search TERM] [--min-votes N] [--author NAME] [--limit N] [--as-json]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.research.common.config import COMPETITION_SLUG, DISCUSSIONS_DB  # noqa: E402
from scripts.research.common.db import connect  # noqa: E402


def query(
    comp: str,
    *,
    search: str | None,
    min_votes: int,
    author: str | None,
    limit: int,
) -> list[sqlite3.Row]:
    """条件に合うスレッド行を votes 降順で返す。"""
    sql = ["SELECT * FROM discussions WHERE competition_id = ?"]
    params: list[object] = [comp]
    if search:
        sql.append("AND title LIKE ?")
        params.append(f"%{search}%")
    if min_votes > 0:
        sql.append("AND total_votes >= ?")
        params.append(min_votes)
    if author:
        sql.append("AND author = ?")
        params.append(author)
    sql.append("ORDER BY total_votes DESC LIMIT ?")
    params.append(limit)
    conn = connect(DISCUSSIONS_DB)
    try:
        return conn.execute(" ".join(sql), params).fetchall()
    finally:
        conn.close()


def format_rows(rows: list[sqlite3.Row], *, as_json: bool) -> str:
    """行を表示用テキストに整形する。"""
    if as_json:
        return json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2)
    if not rows:
        return "(該当なし)"
    lines = [f"{'votes':>6}  {'id':>8}  title"]
    for r in rows:
        lines.append(f"{r['total_votes']:>6}  {r['topic_id']:>8}  {r['title']}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="discussions.db を検索")
    ap.add_argument("comp", nargs="?", default=COMPETITION_SLUG, help="コンペ slug")
    ap.add_argument("--search", help="title の部分一致")
    ap.add_argument("--min-votes", type=int, default=0)
    ap.add_argument("--author")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--as-json", action="store_true")
    args = ap.parse_args()

    rows = query(
        args.comp,
        search=args.search,
        min_votes=args.min_votes,
        author=args.author,
        limit=args.limit,
    )
    print(format_rows(rows, as_json=args.as_json))


if __name__ == "__main__":
    main()
