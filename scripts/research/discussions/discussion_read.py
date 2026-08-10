"""CLI: スレッド本文（コメントツリー）を表示し、任意で data/discussions_md/ へ md 出力する。

使い方:
    uv run python scripts/research/discussions/discussion_read.py <topic_id> [--raw] [--export-md]
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.research.common.config import DISCUSSIONS_DB, DISCUSSIONS_MD_DIR  # noqa: E402
from scripts.research.common.db import connect  # noqa: E402


def _fetch(conn: sqlite3.Connection, topic_id: int) -> tuple[sqlite3.Row | None, list[sqlite3.Row]]:
    topic = conn.execute("SELECT * FROM discussions WHERE topic_id = ?", (topic_id,)).fetchone()
    comments = conn.execute(
        "SELECT * FROM comments WHERE topic_id = ? ORDER BY depth, comment_id",
        (topic_id,),
    ).fetchall()
    return topic, comments


def render_thread(topic: sqlite3.Row, comments: list[sqlite3.Row], *, raw: bool = False) -> str:
    """スレッドを見出し＋インデント付きコメント列に整形する。"""
    header = (
        []
        if raw
        else [
            f"# {topic['title']}",
            f"- URL: {topic['url']}",
            f"- author: {topic['author']}  votes: {topic['total_votes']}  messages: {topic['total_messages']}",
            "",
        ]
    )
    body: list[str] = []
    for c in comments:
        indent = "    " * int(c["depth"])
        if raw:
            body.append(c["content"])
        else:
            meta = f"{indent}**{c['author']}** ({c['author_tier']}) · votes {c['votes']} · {c['post_date']}"
            text = "\n".join(indent + line for line in (c["content"] or "").splitlines())
            body.append(f"{meta}\n{text}")
    return "\n".join([*header, "\n\n".join(body)])


def _slugify(title: str) -> str:
    slug = re.sub(r"[^\w\-一-龠ぁ-んァ-ヶー]+", "-", title, flags=re.UNICODE).strip("-")
    return slug[:60] or "topic"


def export_markdown(topic: sqlite3.Row, comments: list[sqlite3.Row], dest_dir: Path = DISCUSSIONS_MD_DIR) -> Path:
    """スレッドを md ファイルとして data/discussions_md/ に書き出し、パスを返す。"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"thread-{topic['topic_id']}-{_slugify(topic['title'])}.md"
    path.write_text(render_thread(topic, comments), encoding="utf-8")
    return path


def read_topic(topic_id: int, *, raw: bool) -> str:
    conn = connect(DISCUSSIONS_DB)
    try:
        topic, comments = _fetch(conn, topic_id)
        if topic is None:
            return f"(topic {topic_id} は DB に無い。先に discussion_ingest で取り込むこと)"
        return render_thread(topic, comments, raw=raw)
    finally:
        conn.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="スレッド本文を表示")
    ap.add_argument("topic_id", type=int)
    ap.add_argument("--raw", action="store_true", help="整形せず本文のみ連結")
    ap.add_argument("--export-md", action="store_true", help="data/discussions_md/ に md 出力")
    args = ap.parse_args()

    conn = connect(DISCUSSIONS_DB)
    try:
        topic, comments = _fetch(conn, args.topic_id)
        if topic is None:
            print(f"(topic {args.topic_id} は DB に無い。先に discussion_ingest で取り込むこと)")
            return
        print(render_thread(topic, comments, raw=args.raw))
        if args.export_md:
            path = export_markdown(topic, comments)
            print(f"\n[research] md を書き出した: {path}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
