"""Gemma r78: recipient末尾かつ16>4のx13をN=100 ABBAで現行候補と比較する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def _alpha_label(index: int) -> str:
    chars: list[str] = []
    value = index
    while True:
        value, remainder = divmod(value, 26)
        chars.append(chr(ord("a") + remainder))
        if value == 0:
            return "".join(reversed(chars))
        value -= 1


# 既定先頭100件のby/ccに加えて、r69で見つかったnoも含める。
RECIPIENTS = tuple([*(_alpha_label(index) for index in range(99)), "no"])


def _baseline(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


def _current(recipient: str) -> str:
    return (
        f'Mail body:"",subject:"",to:"{recipient}"; '
        "use plain quoted values. Conclude without text."
    )


def _recipient_last(recipient: str) -> str:
    return (
        'Mail body:"",subject:""; keep keys bare and quote only values. '
        f'Conclude without text. to:"{recipient}"'
    )


VARIANTS = {
    "a0_baseline": _baseline,
    "b0_current": _current,
    "c0_recipient_last": _recipient_last,
    "c1_recipient_last": _recipient_last,
    "b1_current": _current,
    "a1_baseline": _baseline,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
