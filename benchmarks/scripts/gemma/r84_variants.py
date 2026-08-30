"""Gemma r84: r82で16>4だったrecipient末尾6件をN=100 stress比較する。"""

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
    "x0_plain_semicolon": lambda r: (
        f'use plain quoted values; Conclude without text. Mail body:"",subject:"",to:"{r}"'
    ),
    "x1_plain_split": lambda r: (
        f'use plain quoted values. Mail body:"",subject:"". Conclude without text. to:"{r}"'
    ),
    "x2_ordinary_split": lambda r: (
        "use ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{r}"'
    ),
    "x3_json_respond": lambda r: (
        "use JSON-style values and bare keys. "
        f'Mail body:"",subject:"". Respond nothing. to:"{r}"'
    ),
    "x4_keys_split": lambda r: (
        f'Mail body:"",subject:"". keep keys bare and quote only values. '
        f'Conclude without text. to:"{r}"'
    ),
    "x5_json_final": lambda r: (
        "use JSON-style values and bare keys. "
        f'Mail body:"",subject:"". Final response empty. to:"{r}"'
    ),
    "b1_current": _current,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
