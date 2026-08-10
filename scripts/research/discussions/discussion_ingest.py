"""CLI: ディスカッションを収集して discussions.db へ保存する。取得のやり方を --source で切り替える。

使い方:
    # 案B（事前取得 JSON 方式・既定・新トークン不要）: Bookmarks.json 起点、保存済み JSON を取り込む
    uv run python scripts/research/discussions/discussion_ingest.py <comp> --source bookmarks
    # 案A（内部 API 方式・要 KAGGLE_API_TOKEN）: Kaggle 内部 API から自動収集
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

# スレッド本文取得の間隔。0.6s では 429 が頻発して大量に取りこぼしたため 1.5s に緩めた
# （429 自体は fetcher_internal._post 側でもバックオフ再試行する）。
SLEEP_BETWEEN_TOPICS_S = 1.5
# 取りこぼしたスレッドを再試行するまでの基本待ち時間（ラウンドごとに倍加）。
RETRY_ROUND_WAIT_S = 60

# 一覧 API は「コンペのスレッドを列挙する」ものではなく「検索語に当たったスレッドを返す」ものなので、
# 単一クエリ・単一並び順では取りこぼしが起きうる。複数の切り口で引いた和集合を候補にする。
DISCOVERY_ORDERS = (
    fetcher_internal.ORDER_HOTNESS,
    fetcher_internal.ORDER_CREATED,
    fetcher_internal.ORDER_UPDATED,
    fetcher_internal.ORDER_VOTES,
    fetcher_internal.ORDER_COMMENTS,
)


def _parent_slug(payload: dict) -> str:
    """スレッドが属するコンペの slug（forumTopic.parentName）を取り出す。"""
    ft = payload.get("forumTopic", payload)
    return str(ft.get("parentName") or "") if isinstance(ft, dict) else ""


def _store(conn: sqlite3.Connection, comp: str, topic: Topic, comments: list[Comment], now: str) -> None:
    """1 スレッドと、その配下のコメントを DB へ追加または更新（upsert）する。"""
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

    parser のフィールド対応の検証や、案B（事前取得 JSON 方式）のキャッシュとして再利用するために使う。
    """
    DISCUSSIONS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = DISCUSSIONS_RAW_DIR / f"{topic_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[research] 生レスポンスを保存: {path}")


def ingest(
    comp: str,
    *,
    source: str,
    max_pages: int,
    topic_ids: list[int] | None,
    save_raw: bool = False,
    rounds: int = 3,
    only_competition: bool = True,
) -> int:
    """指定した取得のやり方で収集して DB に保存する。取り込んだスレッド数を返す。"""
    conn = connect(DISCUSSIONS_DB)
    stored = 0
    now = datetime.now(UTC).isoformat()
    try:
        init_db(conn, DISCUSSIONS_DDL)
        if source == "internal":
            stored = _ingest_internal(
                conn,
                comp,
                max_pages=max_pages,
                topic_ids=topic_ids,
                now=now,
                save_raw=save_raw,
                rounds=rounds,
                only_competition=only_competition,
            )
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
    rounds: int = 3,
    only_competition: bool = True,
) -> int:
    """候補スレッドを取得して保存する。取りこぼしは間隔を空けてラウンド再試行する。"""
    session = fetcher_internal.make_session()
    ids = topic_ids or _discover_internal_ids(session, comp, max_pages=max_pages)
    print(f"[research] 候補 {len(ids)} スレッドを取得する")

    stored = 0
    skipped_other = 0
    pending = list(ids)
    failed: list[int] = []
    for round_no in range(1, rounds + 1):
        failed = []
        for tid in pending:
            try:
                payload = fetcher_internal.get_forum_topic(session, tid)
                if save_raw:
                    _save_raw(tid, payload)
                parent = _parent_slug(payload)
                if only_competition and parent and parent != comp:
                    skipped_other += 1
                    continue
                topic, comments = parse_forum_topic(payload, competition_id=comp)
                if not topic.topic_id:
                    topic.topic_id = tid
                _store(conn, comp, topic, comments, now)
                stored += 1
            except Exception as exc:  # noqa: BLE001 - 1 スレッドの取得が失敗しても全体は止めない
                print(f"[research] topic {tid} の取得に失敗: {exc}")
                failed.append(tid)
            time.sleep(SLEEP_BETWEEN_TOPICS_S)
        conn.commit()  # ラウンドごとに確定させ、途中で止まっても成果を残す
        if not failed:
            break
        if round_no < rounds:
            wait = RETRY_ROUND_WAIT_S * round_no
            print(f"[research] {len(failed)} 件が未取得。{wait}s 待って再試行（round {round_no + 1}/{rounds}）")
            time.sleep(wait)
            pending = failed

    if skipped_other:
        print(f"[research] 他コンペのスレッド {skipped_other} 件は対象外として除外した")
    if failed:
        print(f"[research] {rounds} ラウンド試して取得できなかった: {failed}")
    return stored


def _discover_internal_ids(session: object, comp: str, *, max_pages: int) -> list[int]:
    """複数のクエリ×並び順で一覧を引き、その和集合を候補 id とする。"""
    title = fetcher_internal.resolve_competition_title(comp)
    queries = [q for q in (title, COMPETITION_TITLE, comp) if q]
    queries = list(dict.fromkeys(queries))  # 重複除去（順序は維持）
    print(f"[research] 検索クエリ: {queries}")

    ids: list[int] = []
    seen: set[int] = set()
    for query in queries:
        for order in DISCOVERY_ORDERS:
            before = len(seen)
            try:
                for payload in fetcher_internal.iter_topics(session, query=query, max_pages=max_pages, order_by=order):
                    for topic in parse_topic_list(payload):
                        if topic.topic_id not in seen:
                            seen.add(topic.topic_id)
                            ids.append(topic.topic_id)
            except Exception as exc:  # noqa: BLE001 - 1 つの切り口が失敗しても他は続ける
                print(f"[research] 一覧取得に失敗（query={query!r} order={order}）: {exc}")
            print(f"[research]   query={query!r} order={order.rsplit('_', 1)[-1]}: 新規 {len(seen) - before} 件")
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
    ap.add_argument("--rounds", type=int, default=3, help="取りこぼしを再試行するラウンド数（間隔は倍加）")
    ap.add_argument(
        "--include-other-competitions",
        action="store_true",
        help="検索に紛れ込んだ他コンペのスレッドも保存する（既定は対象コンペのみ）",
    )
    args = ap.parse_args()

    count = ingest(
        args.comp,
        source=args.source,
        max_pages=args.max_pages,
        topic_ids=args.topic_id,
        save_raw=args.save_raw,
        rounds=args.rounds,
        only_competition=not args.include_other_competitions,
    )
    print(f"[research] {count} スレッドを {DISCUSSIONS_DB} に保存した（source={args.source}）。")


if __name__ == "__main__":
    main()
