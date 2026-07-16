"""discussions.db のスキーマ定義（テーブル定義（DDL）。繰り返し実行しても安全（冪等））。"""

from __future__ import annotations

DISCUSSIONS_DDL: str = """
CREATE TABLE IF NOT EXISTS discussions (
    competition_id TEXT    NOT NULL,
    topic_id       INTEGER NOT NULL,
    url            TEXT,
    title          TEXT,
    author         TEXT,
    total_votes    INTEGER NOT NULL DEFAULT 0,
    total_messages INTEGER NOT NULL DEFAULT 0,
    post_date      TEXT,
    ingested_at    TEXT    NOT NULL,
    PRIMARY KEY (competition_id, topic_id)
);

CREATE TABLE IF NOT EXISTS comments (
    topic_id    INTEGER NOT NULL,
    comment_id  INTEGER NOT NULL,          -- 元 id が無ければ walk 連番
    parent_id   INTEGER,                   -- ルートは NULL
    depth       INTEGER NOT NULL DEFAULT 0,
    author      TEXT,
    author_tier TEXT,
    votes       INTEGER NOT NULL DEFAULT 0,
    post_date   TEXT,
    content     TEXT,                      -- rawMarkdown 優先、無ければ content
    PRIMARY KEY (topic_id, comment_id)
);

CREATE INDEX IF NOT EXISTS idx_disc_votes
    ON discussions (competition_id, total_votes DESC);
CREATE INDEX IF NOT EXISTS idx_comments_topic
    ON comments (topic_id, parent_id);
"""
