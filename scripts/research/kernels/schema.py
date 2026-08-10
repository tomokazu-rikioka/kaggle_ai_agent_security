"""kernels.db のテーブル定義（DDL）。何度実行しても安全（冪等）に作れる。"""

from __future__ import annotations

KERNELS_DDL: str = """
CREATE TABLE IF NOT EXISTS kernels (
    competition_id TEXT    NOT NULL,
    kernel_ref     TEXT    NOT NULL,          -- "owner/kernel-slug"
    title          TEXT,
    author         TEXT,
    total_votes    INTEGER NOT NULL DEFAULT 0,
    last_run_time  TEXT,
    is_private     INTEGER NOT NULL DEFAULT 0,
    ingested_at    TEXT    NOT NULL,
    best_public_score REAL,                    -- 検索 API 由来の LB 公開スコア（未提出なら NULL）
    PRIMARY KEY (competition_id, kernel_ref)
);

CREATE TABLE IF NOT EXISTS competition_info (
    competition_id TEXT PRIMARY KEY,
    title          TEXT NOT NULL DEFAULT '',
    updated_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_kernels_votes
    ON kernels (competition_id, total_votes DESC);
"""

# 既存 DB に後から足した列（CREATE TABLE IF NOT EXISTS では増えないので ALTER で埋める）。
KERNELS_ADDED_COLUMNS: dict[str, str] = {"best_public_score": "REAL"}
