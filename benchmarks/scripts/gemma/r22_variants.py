"""Gemma r22: recipient token costをABBA順で比較し、線形GPU driftを相殺する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()

_LOW = (
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "p",
    "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "aa", "ab", "ac", "ad", "ae",
)
_HIGH = (
    "bxf", "bxg", "bxh", "bxi", "bxj", "bxk", "bxl", "bxm", "bxn", "bxo", "bxp", "bxq", "bxr", "bxs", "bxt",
    "bxu", "bxv", "bxw", "bxx", "bxy", "bxz", "bya", "byb", "byc", "byd", "byf", "byg", "byh", "byi", "byj",
)


def _index(label: str) -> int:
    value = 0
    for character in label:
        value = value * 26 + ord(character) - ord("a") + 1
    return value - 1


def _message(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


def _from(values: tuple[str, ...], label: str) -> str:
    return _message(values[_index(label) % len(values)])


VARIANTS = {
    "a0_high": lambda r: _from(_HIGH, r),
    "b1_low": lambda r: _from(_LOW, r),
    "b2_low_repeat": lambda r: _from(_LOW, r),
    "a3_high_repeat": lambda r: _from(_HIGH, r),
}
