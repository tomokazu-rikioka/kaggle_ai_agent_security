"""内部 API / 事前取得 JSON を共通の形に整える層（案A=内部 API 方式／案B=事前取得 JSON 方式の両方で使う）。

`GetForumTopicById` 相当の JSON（`forumTopic{firstMessage, comments[](replies ネスト), totalMessages}`）を
入れ子のない Topic + Comment 群へ変換する。内部 API は非公式でキー名が変わり得るため、候補キーを順に試す
守りの堅い抽出にしている（キーが無ければ飛ばし、例外は投げない方針）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Topic:
    """ディスカッションのスレッド見出し。"""

    topic_id: int
    title: str
    author: str
    total_votes: int
    total_messages: int
    post_date: str
    url: str


@dataclass
class Comment:
    """スレッド内の 1 メッセージ（親投稿・コメント・返信を入れ子なしに並べたもの）。"""

    comment_id: int
    parent_id: int | None
    depth: int
    author: str
    author_tier: str
    votes: int
    post_date: str
    content: str


def _first(node: dict[str, Any], keys: list[str], default: Any = "") -> Any:
    """候補キーを順に試し、最初に見つかった None でない値を返す。"""
    for k in keys:
        if k in node and node[k] is not None:
            return node[k]
    return default


def _to_int(value: Any) -> int:
    """安全に int へ変換する（変換に失敗したら 0）。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _author_name(node: dict[str, Any]) -> str:
    author = _first(node, ["author", "user"], {})
    if isinstance(author, dict):
        return str(_first(author, ["displayName", "userName", "name"], ""))
    return str(_first(node, ["authorName", "displayName"], ""))


def _author_tier(node: dict[str, Any]) -> str:
    author = _first(node, ["author", "user"], {})
    if isinstance(author, dict):
        return str(_first(author, ["performanceTier", "tier"], ""))
    return str(_first(node, ["tier", "performanceTier"], ""))


def _votes(node: dict[str, Any]) -> int:
    votes = _first(node, ["votes"], None)
    if isinstance(votes, dict):
        return _to_int(_first(votes, ["totalVotes", "count"], 0))
    return _to_int(_first(node, ["totalVotes", "voteCount"], 0))


def _content(node: dict[str, Any]) -> str:
    return str(_first(node, ["rawMarkdown", "content", "message", "body"], ""))


def _replies(node: dict[str, Any]) -> list[dict[str, Any]]:
    reps = _first(node, ["replies", "comments", "children"], [])
    return reps if isinstance(reps, list) else []


def _forum_topic(payload: dict[str, Any]) -> dict[str, Any]:
    """payload が {forumTopic:{...}} でも、forumTopic 本体そのものでも受け取れるようにする。"""
    inner = payload.get("forumTopic")
    return inner if isinstance(inner, dict) else payload


def parse_forum_topic(payload: dict[str, Any], *, competition_id: str = "") -> tuple[Topic, list[Comment]]:
    """GetForumTopicById 相当の JSON を Topic と Comment 群へ変換する。"""
    ft = _forum_topic(payload)
    first = _first(ft, ["firstMessage", "firstPost"], {})
    first = first if isinstance(first, dict) else {}

    topic_id = _to_int(_first(ft, ["id", "forumTopicId", "topicId"], 0))
    title = str(_first(ft, ["title", "name"], ""))
    total_messages = _to_int(_first(ft, ["totalMessages", "totalReplies", "commentCount"], 0))
    url = str(_first(ft, ["url"], ""))

    comments: list[Comment] = []
    counter = {"n": 0}

    def walk(node: dict[str, Any], parent_id: int | None, depth: int) -> int:
        counter["n"] += 1
        cid = _to_int(_first(node, ["id", "messageId", "forumMessageId"], counter["n"])) or counter["n"]
        comments.append(
            Comment(
                comment_id=cid,
                parent_id=parent_id,
                depth=depth,
                author=_author_name(node),
                author_tier=_author_tier(node),
                votes=_votes(node),
                post_date=str(_first(node, ["postDate", "date", "createDate"], "")),
                content=_content(node),
            )
        )
        for child in _replies(node):
            if isinstance(child, dict):
                walk(child, cid, depth + 1)
        return cid

    # firstMessage を根（depth=0）として取り込む
    root_id: int | None = None
    if first:
        root_id = walk(first, None, 0)

    for c in _first(ft, ["comments", "messages"], []):
        if isinstance(c, dict):
            walk(c, root_id, 1)

    # スレッドのメタ情報は、正となる forumTopic 直下のフィールドを優先し、
    # 無ければ firstMessage 由来を代替（fallback）に使う。
    topic_author = str(_first(ft, ["authorUserDisplayName"], "")) or (_author_name(first) if first else "")
    topic_votes = _to_int(_first(ft, ["totalVotes"], None)) if "totalVotes" in ft else (_votes(first) if first else 0)
    topic_date = str(_first(ft, ["postDate"], "")) or (str(_first(first, ["postDate", "date"], "")) if first else "")
    topic = Topic(
        topic_id=topic_id,
        title=title,
        author=topic_author,
        total_votes=topic_votes,
        total_messages=total_messages or len(comments),
        post_date=topic_date,
        url=_absolutize(url) or _topic_url(competition_id, topic_id),
    )
    return topic, comments


def _absolutize(url: str) -> str:
    """相対 URL（/competitions/...）を絶対 URL に直す。"""
    if url.startswith("/"):
        return f"https://www.kaggle.com{url}"
    return url


def _topic_url(competition_id: str, topic_id: int) -> str:
    if competition_id and topic_id:
        return f"https://www.kaggle.com/competitions/{competition_id}/discussion/{topic_id}"
    return ""


def parse_topic_list(payload: dict[str, Any]) -> list[Topic]:
    """ListEntities 相当のレスポンスから Topic の見出し群を取り出す（案A＝内部 API 方式の一覧取得で使う）。"""
    entities = _first(payload, ["entities", "documents", "results", "items"], [])
    topics: list[Topic] = []
    if not isinstance(entities, list):
        return topics
    for e in entities:
        if not isinstance(e, dict):
            continue
        topic_id = _to_int(_first(e, ["id", "forumTopicId", "documentId"], 0))
        if not topic_id:
            continue
        topics.append(
            Topic(
                topic_id=topic_id,
                title=str(_first(e, ["title", "name"], "")),
                author=_author_name(e),
                total_votes=_votes(e),
                total_messages=_to_int(_first(e, ["totalMessages", "commentCount"], 0)),
                post_date=str(_first(e, ["postDate", "date"], "")),
                url=str(_first(e, ["url"], "")),
            )
        )
    return topics
