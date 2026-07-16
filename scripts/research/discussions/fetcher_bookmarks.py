"""案B: Bookmarks.json の URL 群を対象に、事前取得した JSON を読み込む（新トークン不要）。

対象スレッドの集合は docs/discussions/Bookmarks.json（`.../discussion/<id>` の配列）から取る。
各スレッドの本文 JSON（GetForumTopicById 相当）は事前に data/discussions_raw/<topic_id>.json へ
保存しておく前提。保存は案A の内部 API 取得（`discussion_ingest.py --source internal --save-raw`）で
生成される。JSON 形は案A と同一なので、parser.py 以降は完全共通。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.research.common.config import BOOKMARKS_JSON, DISCUSSIONS_RAW_DIR  # noqa: E402

_ID_RE = re.compile(r"/discussion/(\d+)")


def load_bookmark_ids(path: Path = BOOKMARKS_JSON) -> list[int]:
    """Bookmarks.json の URL 配列から topic_id を抽出する（重複除去・順序保持）。"""
    if not path.exists():
        return []
    urls = json.loads(path.read_text(encoding="utf-8"))
    ids: list[int] = []
    seen: set[int] = set()
    for url in urls:
        m = _ID_RE.search(str(url))
        if m:
            tid = int(m.group(1))
            if tid not in seen:
                seen.add(tid)
                ids.append(tid)
    return ids


def load_prefetched(topic_id: int, raw_dir: Path = DISCUSSIONS_RAW_DIR) -> dict[str, Any]:
    """data/discussions_raw/<topic_id>.json を読む。無ければ FileNotFoundError。"""
    path = raw_dir / f"{topic_id}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"事前取得 JSON が無い: {path}."
            f" 案A（discussion_ingest.py --source internal --save-raw）で先に生成すること。"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def topic_ids_source(path: Path = BOOKMARKS_JSON) -> list[int]:
    """収集対象の topic_id 一覧（Bookmarks.json 起点）。"""
    return load_bookmark_ids(path)
