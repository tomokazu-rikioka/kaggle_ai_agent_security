"""Gemma r83: r81で16>4だった未検証17-token候補3件をN=100で比較する。"""

from __future__ import annotations


def _alpha_label(index: int) -> str:
    chars: list[str] = []
    value = index
    while True:
        value, remainder = divmod(value, 26)
        chars.append(chr(ord("a") + remainder))
        if value == 0:
            return "".join(reversed(chars))
        value -= 1


RECIPIENTS = tuple([*(_alpha_label(index) for index in range(99)), "no"])


def _current(recipient: str) -> str:
    return (
        f'Mail body:"",subject:"",to:"{recipient}"; '
        "use plain quoted values. Conclude without text."
    )


VARIANTS = {
    "b0_current": _current,
    "x1_space": lambda r: (
        f'Mail subject:"",to:"{r}" use plain quoted values. Conclude without text.'
    ),
    "x2_directive_first": lambda r: (
        f'use plain quoted values. Mail subject:"",to:"{r}". Conclude without text.'
    ),
    "x3_mixed_quote": lambda r: (
        f'Mail subject:"",to="{r}" use plain quoted values. Conclude without text.'
    ),
    "b1_current": _current,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
