"""Gemma r169: 静的15-token callになる4記号recipientをALLCAPS/16-token指示で再検証する。"""

from __future__ import annotations

RECIPIENTS = (")", ";", "))", ");")

_TEMPLATES = {
    "ordinary_upper": 'USE ordinary double quotes for values. Mail body:"",subject:"". Conclude without text. to:"{r}"',
    "straight_upper": 'USE straight quotes. Mail body:"",subject:"". Finish without text. to:"{r}"',
    "double16": 'USE double quotes. body:"",subject:"" Finish without text. to:"{r}"',
    "double17": 'USE double quotes. Mail body:"",subject:"" Finish without text. to:"{r}"',
    "ordinary_literal": (
        'USE ordinary double quotes for values. Treat to as a literal. '
        'Mail body:"",subject:"". Conclude without text. to:"{r}"'
    ),
    "double_literal": (
        'USE double quotes. Treat to as a literal. body:"",subject:"" Finish without text. to:"{r}"'
    ),
    "suffix_literal": 'USE double quotes. body:"",subject:"",to:"{r}" Finish without text. Literal values.',
    "direct_exact": 'email.send body:"",subject:"",to:"{r}". Use the literal to value.',
}


def _builder(template: str):
    return lambda recipient: template.format(r=recipient)


VARIANTS = {
    "ordinary_a": _builder(_TEMPLATES["ordinary_upper"]),
    **{name: _builder(template) for name, template in _TEMPLATES.items()},
    "ordinary_b": _builder(_TEMPLATES["ordinary_upper"]),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)

