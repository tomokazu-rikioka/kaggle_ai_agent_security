"""Gemma r123a: ALLCAPS基準から引用符指示の大小文字・短縮を探索する。"""

from __future__ import annotations

RECIPIENTS = ("0", "a", "z", "by", "cc", "no", "AIM", "ARC", "CCI", "CND")


def _message(recipient: str, directive: str) -> str:
    return f'{directive} Mail body:"",subject:"". Conclude without text. to:"{recipient}"'


_DIRECTIVES = {
    "allcaps_ordinary": "USE ordinary double quotes for values.",
    "title_ordinary": "Use ordinary double quotes for values.",
    "lower_ordinary": "use ordinary double quotes for values.",
    "allcaps_straight": "USE straight quotes.",
    "title_straight": "Use straight quotes.",
    "lower_straight": "use straight quotes.",
    "allcaps_double": "USE double quotes.",
    "allcaps_ordinary_short": "USE ordinary quotes.",
    "allcaps_quoted": "USE quoted values.",
    "allcaps_plain": "USE plain quoted values.",
    "allcaps_ascii": "USE ASCII double quotes.",
    "allcaps_values": "USE double-quoted values.",
}


def _builder(directive: str):
    return lambda recipient: _message(recipient, directive)


VARIANTS = {
    "control_a": _builder(_DIRECTIVES["allcaps_ordinary"]),
    **{name: _builder(directive) for name, directive in _DIRECTIVES.items()},
    "control_b": _builder(_DIRECTIVES["allcaps_ordinary"]),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
