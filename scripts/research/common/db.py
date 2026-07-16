"""SQLite の共通ヘルパ（接続・スキーマ初期化・追加または更新（upsert））。

kernels.db / discussions.db の双方で使う薄い層。ORM は使わず sqlite3 標準ライブラリだけを使う。
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from pathlib import Path


def connect(db_path: Path) -> sqlite3.Connection:
    """DB へ接続する。親ディレクトリが無ければ作成し、Row factory と外部キーを有効化する。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection, ddl: str) -> None:
    """CREATE TABLE IF NOT EXISTS 群（テーブル定義（DDL）。繰り返し実行しても安全（冪等））を実行する。"""
    conn.executescript(ddl)
    conn.commit()


def upsert(
    conn: sqlite3.Connection,
    table: str,
    row: dict[str, object],
    pk: Sequence[str],
) -> None:
    """1 行を INSERT し、主キーが衝突したら非キー列だけを UPDATE する（追加または更新（upsert））。

    Args:
        conn: 接続。
        table: テーブル名。
        row: 列名 → 値の dict。
        pk: 主キー列名の並び（衝突判定に使う ON CONFLICT の対象）。
    """
    cols = list(row.keys())
    placeholders = ", ".join(["?"] * len(cols))
    col_list = ", ".join(cols)
    update_cols = [c for c in cols if c not in pk]
    if update_cols:
        set_clause = ", ".join(f"{c}=excluded.{c}" for c in update_cols)
        conflict = f"ON CONFLICT({', '.join(pk)}) DO UPDATE SET {set_clause}"
    else:
        conflict = f"ON CONFLICT({', '.join(pk)}) DO NOTHING"
    sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) {conflict}"
    conn.execute(sql, [row[c] for c in cols])
