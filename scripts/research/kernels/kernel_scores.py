"""公開カーネルの LB スコア（bestPublicScore）を Kaggle 内部の検索 API から取得する。

`kaggle kernels list`（公式 CLI）はスコアを返さないため、Web 画面が使う検索 API の
`kernelDocument.bestPublicScore` を読む。検索はコンペ横断なので、
「どのカーネルがこのコンペのものか」は公式 CLI の `--competition` 一覧で担保し、
ここで作るのは ref → スコアの対応表だけにする。

認証は discussions 側と同じ内部 API セッションを使い回す（**非公式なので予告なく壊れ得る**）。
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.research.common.config import KAGGLE_API  # noqa: E402
from scripts.research.discussions.fetcher_internal import _post, make_session  # noqa: E402

__all__ = ["KernelScore", "fetch_score_map", "make_session"]


@dataclass
class KernelScore:
    """検索 API が返す公開カーネルのスコア情報。"""

    ref: str
    title: str
    score: float | None
    votes: int
    is_private: bool


def _document_ref(doc: dict[str, Any]) -> str | None:
    owner = doc.get("ownerUser") or {}
    username = owner.get("userName") or str(owner.get("url", "")).lstrip("/")
    slug = doc.get("slug")
    return f"{username}/{slug}" if username and slug else None


def _to_score(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def fetch_score_map(
    session: Any,
    query: str,
    *,
    page_size: int = 100,
    max_pages: int = 20,
    sleep_s: float = 0.8,
) -> dict[str, KernelScore]:
    """検索 API をページ送りして ref → KernelScore の対応表を作る。"""
    url = f"{KAGGLE_API}/v1/search.SearchApiService/ListEntities"
    scores: dict[str, KernelScore] = {}
    page_token: str | None = None
    for _ in range(max_pages):
        body: dict[str, Any] = {
            "filters": {
                "query": query,
                "documentTypes": ["DOCUMENT_TYPE_KERNEL"],
                "kernelFilters": {},
            },
            "pageSize": page_size,
            "canonicalOrderBy": "LIST_SEARCH_CONTENT_ORDER_BY_VOTES",
        }
        if page_token:
            body["pageToken"] = page_token
        payload = _post(session, url, body)
        for doc in payload.get("documents", []):
            ref = _document_ref(doc)
            if not ref or ref in scores:
                continue
            kd = doc.get("kernelDocument") or {}
            scores[ref] = KernelScore(
                ref=ref,
                title=str(doc.get("title") or doc.get("slug") or ""),
                score=_to_score(kd.get("bestPublicScore")),
                votes=int(doc.get("votes") or 0),
                is_private=bool(doc.get("isPrivate")),
            )
        page_token = payload.get("nextPageToken") or ""
        if not page_token:
            break
        time.sleep(sleep_s)
    return scores
