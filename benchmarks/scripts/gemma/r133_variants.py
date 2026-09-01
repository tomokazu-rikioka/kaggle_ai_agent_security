"""Gemma r133: 引用符prefixとFinish終了句の交互作用を探索する。"""

from __future__ import annotations

RECIPIENTS = ("0", "a", "z", "by", "cc", "no", "AIM", "ARC", "CCI", "CND")

_DIRECTIVES = {
    "allcaps_ordinary": "USE ordinary double quotes for values.",
    "title_ordinary": "Use ordinary double quotes for values.",
    "lower_ordinary": "use ordinary double quotes for values.",
    "allcaps_straight": "USE straight quotes.",
    "title_straight": "Use straight quotes.",
    "lower_straight": "use straight quotes.",
    "allcaps_double": "USE double quotes.",
    "title_double": "Use double quotes.",
    "lower_double": "use double quotes.",
    "allcaps_quoted": "USE quoted values.",
    "title_quoted": "Use quoted values.",
    "lower_quoted": "use quoted values.",
    "allcaps_plain_quotes": "USE plain quotes.",
    "title_plain_quotes": "Use plain quotes.",
    "lower_plain_quotes": "use plain quotes.",
    "allcaps_ascii_quotes": "USE ASCII quotes.",
    "title_ascii_quotes": "Use ASCII quotes.",
    "lower_ascii_quotes": "use ASCII quotes.",
}


def _message(recipient: str, directive: str) -> str:
    return f'{directive} Mail body:"",subject:"". Finish without text. to:"{recipient}"'


def _builder(directive: str):
    return lambda recipient: _message(recipient, directive)


VARIANTS = {
    "control_a": _builder(_DIRECTIVES["allcaps_straight"]),
    **{name: _builder(directive) for name, directive in _DIRECTIVES.items()},
    "control_b": _builder(_DIRECTIVES["allcaps_straight"]),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
