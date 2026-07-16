"""CLI: ディスカッションを収集して discussions.db へ保存する。取得層を --source で切替。

使い方:
    # 案B（既定・新トークン不要）: Bookmarks.json 起点、事前取得 JSON を取り込む
    uv run python scripts/research/discussions/discussion_ingest.py <comp> --source bookmarks
    # 案A（要 KAGGLE_API_TOKEN）: 内部 API から自動収集
    uv run python scripts/research/discussions/discussion_ingest.py <comp> --source internal --max-pages 3
    # 特定スレッドのみ
    uv run python scripts/research/discussions/discussion_ingest.py <comp> --topic-id 708034 --topic-id 708926
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.research.common.config import (  # noqa: E402
    COMPETITION_SLUG,
    COMPETITION_TITLE,
    DISCUSSIONS_DB,
    DISCUSSIONS_RAW_DIR,
)
from scripts.research.common.db import connect, init_db, upsert  # noqa: E402
from scripts.research.discussions import fetcher_bookmarks, fetcher_internal  # noqa: E402
from scripts.research.discussions.parser import Comment, Topic, parse_forum_topic, parse_topic_list  # noqa: E402
from scripts.research.discussions.schema import DISCUSSIONS_DDL  # noqa: E402


def _store(conn: sqlite3.Connection, comp: str, topic: Topic, comments: list[Comment], now: str) -> None:
    """1 スレッドと配下コメントを upsert する。"""
    upsert(
        conn,
        "discussions",
        {
            "competition_id": comp,
            "topic_id": topic.topic_id,
            "url": topic.url,
            "title": topic.title,
            "author": topic.author,
            "total_votes": topic.total_votes,
            "total_messages": topic.total_messages,
            "post_date": topic.post_date,
            "ingested_at": now,
        },
        pk=("competition_id", "topic_id"),
    )
    for c in comments:
        upsert(
            conn,
            "comments",
            {
                "topic_id": topic.topic_id,
                "comment_id": c.comment_id,
                "parent_id": c.parent_id,
                "depth": c.depth,
                "author": c.author,
                "author_tier": c.author_tier,
                "votes": c.votes,
                "post_date": c.post_date,
                "content": c.content,
            },
            pk=("topic_id", "comment_id"),
        )


def _save_raw(topic_id: int, payload: dict) -> None:
    """内部 API の生レスポンスを data/discussions_raw/<id>.json に保存する。

    parser のフィールドマッピング検証や、案B（bookmarks）キャッシュとしての再利用に使う。
    """
    DISCUSSIONS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = DISCUSSIONS_RAW_DIR / f"{topic_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[research] 生レスポンスを保存: {path}")


def ingest(comp: str, *, source: str, max_pages: int, topic_ids: list[int] | None, save_raw: bool = False) -> int:
    """指定ソースから収集して DB に保存する。取り込んだスレッド数を返す。"""
    conn = connect(DISCUSSIONS_DB)
    stored = 0
    now = datetime.now(UTC).isoformat()
    try:
        init_db(conn, DISCUSSIONS_DDL)
        if source == "internal":
            stored = _ingest_internal(conn, comp, max_pages=max_pages, topic_ids=topic_ids, now=now, save_raw=save_raw)
        elif source == "bookmarks":
            stored = _ingest_bookmarks(conn, comp, topic_ids=topic_ids, now=now)
        else:
            raise ValueError(f"未知の source: {source}")
        conn.commit()
    finally:
        conn.close()
    return stored


def _ingest_internal(
    conn: sqlite3.Connection,
    comp: str,
    *,
    max_pages: int,
    topic_ids: list[int] | None,
    now: str,
    save_raw: bool = False,
) -> int:
    session = fetcher_internal.make_session()
    ids = topic_ids or _discover_internal_ids(session, max_pages=max_pages)
    stored = 0
    for tid in ids:
        try:
            payload = fetcher_internal.get_forum_topic(session, tid)
            if save_raw:
                _save_raw(tid, payload)
            topic, comments = parse_forum_topic(payload, competition_id=comp)
            if not topic.topic_id:
                topic.topic_id = tid
            _store(conn, comp, topic, comments, now)
            stored += 1
        except Exception as exc:  # noqa: BLE001 - 1 スレッドの失敗で全体を止めない
            print(f"[research] topic {tid} の取得に失敗（skip）: {exc}")
        time.sleep(0.6)
    return stored


def _discover_internal_ids(session: object, *, max_pages: int) -> list[int]:
    ids: list[int] = []
    seen: set[int] = set()
    for payload in fetcher_internal.iter_topics(session, query=COMPETITION_TITLE, max_pages=max_pages):
        for topic in parse_topic_list(payload):
            if topic.topic_id not in seen:
                seen.add(topic.topic_id)
                ids.append(topic.topic_id)
    return ids


def _ingest_bookmarks(
    conn: sqlite3.Connection,
    comp: str,
    *,
    topic_ids: list[int] | None,
    now: str,
) -> int:
    ids = topic_ids or fetcher_bookmarks.topic_ids_source()
    stored = 0
    missing = 0
    for tid in ids:
        try:
            payload = fetcher_bookmarks.load_prefetched(tid)
        except FileNotFoundError:
            missing += 1
            continue
        topic, comments = parse_forum_topic(payload, competition_id=comp)
        if not topic.topic_id:
            topic.topic_id = tid
        _store(conn, comp, topic, comments, now)
        stored += 1
    if missing:
        print(f"[research] {missing} 件は事前取得 JSON が無くスキップ（data/discussions_raw/<id>.json を用意）。")
    return stored


def main() -> None:
    ap = argparse.ArgumentParser(description="ディスカッションを収集して discussions.db に保存")
    ap.add_argument("comp", nargs="?", default=COMPETITION_SLUG, help="コンペ slug")
    ap.add_argument("--source", choices=["bookmarks", "internal"], default="bookmarks", help="取得層")
    ap.add_argument("--max-pages", type=int, default=3, help="internal の一覧ページ数")
    ap.add_argument("--topic-id", type=int, action="append", help="対象スレッド id（複数可）")
    ap.add_argument(
        "--save-raw",
        action="store_true",
        help="internal 取得時に生レスポンスを data/discussions_raw/<id>.json へ保存（検証・案B 再利用用）",
    )
    args = ap.parse_args()

    count = ingest(
        args.comp,
        source=args.source,
        max_pages=args.max_pages,
        topic_ids=args.topic_id,
        save_raw=args.save_raw,
    )
    print(f"[research] {count} スレッドを {DISCUSSIONS_DB} に保存した（source={args.source}）。")


if __name__ == "__main__":
    main()
