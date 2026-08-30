"""Gemma r96: 15-token値の終端記号を一意IDへ付け、ASCII生成安定率を比較する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset(("by", "cc", "no"))

_SUFFIXES = {
    "regular": "",
    "close_paren": ")",
    "semicolon": ";",
    "double_paren": "))",
    "paren_semicolon": ");",
}


def _builder(suffix: str):
    return lambda recipient: (
        "use ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}{suffix}"'
    )


VARIANTS = {name: _builder(suffix) for name, suffix in _SUFFIXES.items()}


def EXPECTED_EMAIL_TOS(variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient + _SUFFIXES[variant],)
