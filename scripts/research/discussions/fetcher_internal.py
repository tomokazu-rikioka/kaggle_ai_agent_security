"""案A（内部 API 方式）: 非公式の Kaggle 内部 API でディスカッションを取得する。

requests + Kaggle 内部認証トークン（KGAT bearer）+ CSRF 対策トークン（XSRF）を使う。

Kaggle の公開 API はディスカッションを提供しないため、Web 画面が内部で使うエンドポイントを直接叩く。
- 一覧: POST {KAGGLE_API}/v1/search.SearchApiService/ListEntities
- 本文: POST {KAGGLE_WEB}/api/i/discussions.DiscussionsService/GetForumTopicById

認証は環境変数 KAGGLE_API_TOKEN（KGAT）を Bearer に載せ、加えて www.kaggle.com を GET して
得た Cookie の XSRF-TOKEN を X-XSRF-TOKEN ヘッダに付ける。**非公式なので予告なく壊れ得る**。
"""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.research.common.config import (  # noqa: E402
    COMPETITION_TITLE,
    HTTP_TIMEOUT_S,
    KAGGLE_API,
    KAGGLE_WEB,
    TOKEN_ENV,
)


def get_token() -> str:
    """KAGGLE_API_TOKEN（KGAT）を返す。未設定ならはっきりエラーを出す。"""
    token = os.environ.get(TOKEN_ENV)
    if not token:
        raise RuntimeError(
            f"{TOKEN_ENV} が未設定。内部 API（--source internal）には KGAT トークンが必要。"
            f" Kaggle にログインしたブラウザの DevTools で discussion ページの XHR を開き、"
            f" Authorization ヘッダの Bearer 値を `export {TOKEN_ENV}=...` で渡すこと。"
            f"（--source bookmarks は過去に --save-raw で貯めた JSON の読み直し専用なので、"
            f" data/discussions_raw/ が空なら代替にならない）"
        )
    return token


def make_session() -> Any:
    """Bearer と XSRF ヘッダを設定した requests.Session を作る。"""
    import requests

    session = requests.Session()
    token = get_token()
    session.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    # XSRF-TOKEN Cookie を取得してヘッダに写す
    try:
        session.get(KAGGLE_WEB, timeout=HTTP_TIMEOUT_S)
        xsrf = session.cookies.get("XSRF-TOKEN", "")
        if xsrf:
            session.headers["X-XSRF-TOKEN"] = xsrf
    except requests.RequestException as exc:  # noqa: BLE001
        print(f"[research] XSRF 取得に失敗（続行）: {exc}")
    return session


def _post(session: Any, url: str, body: dict[str, Any]) -> dict[str, Any]:
    import requests

    resp = session.post(url, json=body, timeout=HTTP_TIMEOUT_S)
    if resp.status_code in (401, 403):
        raise RuntimeError(
            f"認証エラー {resp.status_code}: KGAT トークンが失効/不正の可能性。"
            f" ブラウザから取り直して {TOKEN_ENV} を更新すること。"
        )
    resp.raise_for_status()
    try:
        return resp.json()
    except (ValueError, requests.JSONDecodeError):  # type: ignore[attr-defined]
        return {}


def list_entities(session: Any, *, query: str, page_token: str | None, page_size: int = 20) -> dict[str, Any]:
    """ディスカッション一覧を検索する（1 ページ分）。"""
    body: dict[str, Any] = {
        "filters": {
            "query": query,
            "documentTypes": ["DOCUMENT_TYPE_TOPIC"],
            "discussionFilters": {"sourceType": "SEARCH_DISCUSSIONS_SOURCE_TYPE_COMPETITION"},
        },
        "pageSize": page_size,
        "canonicalOrderBy": "LIST_SEARCH_CONTENT_ORDER_BY_HOTNESS",
    }
    if page_token:
        body["pageToken"] = page_token
    return _post(session, f"{KAGGLE_API}/v1/search.SearchApiService/ListEntities", body)


def get_forum_topic(session: Any, topic_id: int) -> dict[str, Any]:
    """スレッド本文＋コメントを取得する。"""
    body = {"forumTopicId": topic_id, "includeComments": True}
    return _post(session, f"{KAGGLE_WEB}/api/i/discussions.DiscussionsService/GetForumTopicById", body)


def iter_topics(session: Any, *, query: str = COMPETITION_TITLE, max_pages: int = 3) -> Iterator[dict[str, Any]]:
    """ListEntities をページ送りしながら、生レスポンスを順に yield する。"""
    page_token: str | None = None
    for _ in range(max_pages):
        payload = list_entities(session, query=query, page_token=page_token)
        yield payload
        page_token = payload.get("nextPageToken") or payload.get("nextPageToken", "")
        if not page_token:
            break
        time.sleep(0.5)
