"""Shared, deterministic primitives for the private-guardrail hypotheses."""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any, Final

from aicomp_sdk.core.predicates import SECRET_MARKER, is_protected_secret_path
from aicomp_sdk.core.tools.http import PRIVATE_NET_RE
from aicomp_sdk.guardrails.base import GuardrailBase

UNTRUSTED_SOURCES: Final[frozenset[str]] = frozenset({"web", "email"})
SIDE_EFFECTING: Final[frozenset[str]] = frozenset({"WRITE", "EXEC", "SHARE", "AUTH"})
EXTERNAL_TOOLS: Final[frozenset[str]] = frozenset({"http.post", "email.send"})

_SENSITIVE_TOKEN_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<![a-z0-9])(?:api[_-]?key|secret|password|token|credential|private|confidential)(?![a-z0-9])",
    re.IGNORECASE,
)
_ENGLISH_WORD_RE: Final[re.Pattern[str]] = re.compile(r"[a-z]+")

_INTENT_WORDS: Final[dict[str, frozenset[str]]] = {
    "READ": frozenset({"read", "open", "show", "list", "search", "find", "inspect", "summarize"}),
    "WRITE": frozenset({"write", "save", "store", "create", "update", "edit", "overwrite", "delete", "remove"}),
    "EXEC": frozenset({"run", "execute", "shell", "command"}),
    "SHARE": frozenset({"send", "email", "mail", "share", "upload", "post", "forward", "reply"}),
    "AUTH": frozenset({"login", "authenticate", "authorize", "grant", "permission"}),
}
_INTENT_JA: Final[dict[str, tuple[str, ...]]] = {
    "READ": ("読む", "読ん", "開く", "開い", "表示", "一覧", "検索", "探す", "要約"),
    "WRITE": ("書く", "書き", "保存", "作成", "更新", "編集", "上書き", "削除"),
    "EXEC": ("実行", "コマンド", "シェル"),
    "SHARE": ("送信", "メール", "共有", "投稿", "アップロード", "転送", "返信"),
    "AUTH": ("ログイン", "認証", "許可", "権限"),
}


def iter_arg_strings(value: Any) -> Iterable[str]:
    """Yield every scalar string from nested tool arguments."""
    if isinstance(value, Mapping):
        for nested in value.values():
            yield from iter_arg_strings(nested)
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for nested in value:
            yield from iter_arg_strings(nested)
        return
    if value is None:
        return
    if isinstance(value, str):
        yield value
        return
    try:
        yield json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        yield str(value)


def all_args_text(tool_args: Mapping[str, Any]) -> str:
    return "\n".join(iter_arg_strings(tool_args))


def contains_sensitive_token(value: Any) -> bool:
    return any(_SENSITIVE_TOKEN_RE.search(text) for text in iter_arg_strings(value))


def contains_secret_marker(value: Any) -> bool:
    marker = SECRET_MARKER.casefold()
    return any(marker in text.casefold() for text in iter_arg_strings(value))


def path_arg(tool_args: Mapping[str, Any]) -> str:
    return str(tool_args.get("path", "") or "")


def is_sensitive_path(path: Any) -> bool:
    return is_protected_secret_path(path) or contains_sensitive_token(path)


def is_private_network_call(tool_name: str, tool_args: Mapping[str, Any]) -> bool:
    if tool_name != "http.post":
        return False
    return bool(PRIVATE_NET_RE.search(str(tool_args.get("url", "") or "")))


def has_recent_untrusted(context: Mapping[str, Any], *, include_files: bool = False) -> bool:
    sources = {str(source) for source in (context.get("recent_sources") or [])}
    untrusted = set(UNTRUSTED_SOURCES)
    if include_files:
        untrusted.add("file")
    return bool(sources & untrusted)


def has_explicit_intent(last_user: Any, side_effect: Any) -> bool:
    """Cheap task-alignment proxy based only on the harness-visible last user turn."""
    text = str(last_user or "").casefold()
    effect = str(side_effect or "").upper()
    english_words = set(_ENGLISH_WORD_RE.findall(text))
    return bool(english_words & _INTENT_WORDS.get(effect, frozenset())) or any(
        token in text for token in _INTENT_JA.get(effect, ())
    )


def primary_target(tool_name: str, tool_args: Mapping[str, Any]) -> str:
    key = {
        "email.send": "to",
        "http.post": "url",
        "fs.read": "path",
        "fs.write": "path",
        "fs.delete": "path",
        "shell.run": "cmd",
    }.get(tool_name)
    return str(tool_args.get(key, "") or "").strip() if key else ""


def target_is_user_bound(tool_name: str, tool_args: Mapping[str, Any], last_user: Any) -> bool:
    """Require an exact target to occur in the trusted user turn.

    This intentionally treats action-open requests (for example, "email the address in
    that page") as requiring confirmation: attacker-controlled data must not choose the
    authority-bearing target.
    """
    target = primary_target(tool_name, tool_args).casefold()
    return bool(target) and target in str(last_user or "").casefold()


def redact_secret_markers(tool_args: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return args with explicit scorer sentinels redacted, or None if unchanged."""
    sanitized = dict(tool_args)
    changed = False
    for key in ("data", "body", "content", "subject"):
        value = sanitized.get(key)
        if not isinstance(value, str) or SECRET_MARKER.casefold() not in value.casefold():
            continue
        sanitized[key] = re.sub(re.escape(SECRET_MARKER), "[REDACTED]", value, flags=re.IGNORECASE)
        changed = True
    return sanitized if changed else None


class StatefulGuardrail(GuardrailBase):
    """Small auditable state machine shared by stateful variants."""

    def __init__(self) -> None:
        super().__init__()
        self.ever_untrusted = False
        self.low_integrity = False
        self.confidential = False
        self.attempt_counts: Counter[str] = Counter()

    def observe_context(self, context: Mapping[str, Any], *, include_files: bool = False) -> None:
        if has_recent_untrusted(context, include_files=include_files):
            self.ever_untrusted = True
            self.low_integrity = True

    def note_attempt(self, tool_name: str) -> None:
        self.attempt_counts[tool_name] += 1

    def note_allowed_read(self, tool_name: str, tool_args: Mapping[str, Any], *, include_files: bool = False) -> None:
        if tool_name in {"web.search", "web.open", "email.list", "email.read"}:
            self.ever_untrusted = True
            self.low_integrity = True
        if tool_name == "fs.read":
            if include_files:
                self.ever_untrusted = True
                self.low_integrity = True
            if is_sensitive_path(path_arg(tool_args)):
                self.confidential = True

    def snapshot_state(self) -> Any:
        return {
            "ever_untrusted": self.ever_untrusted,
            "low_integrity": self.low_integrity,
            "confidential": self.confidential,
            "attempt_counts": dict(self.attempt_counts),
        }

    def restore_state(self, snapshot: Any) -> None:
        if not isinstance(snapshot, Mapping):
            return
        self.ever_untrusted = bool(snapshot.get("ever_untrusted", False))
        self.low_integrity = bool(snapshot.get("low_integrity", False))
        self.confidential = bool(snapshot.get("confidential", False))
        raw_counts = snapshot.get("attempt_counts", {})
        self.attempt_counts = Counter(raw_counts if isinstance(raw_counts, Mapping) else {})
