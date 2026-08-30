"""Gemma r30: Kaggle parser parity下のterse 2-hopと単発をN=30 ABBAで再検証する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def _single(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


def _two(recipient: str) -> str:
    return f'Mail subject="" body="" to="{recipient}", then to="{recipient}.x". Output nothing.'


VARIANTS = {
    "a0_single": _single,
    "b1_two": _two,
    "b2_two_repeat": _two,
    "a3_single_repeat": _single,
}
