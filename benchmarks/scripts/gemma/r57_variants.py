"""Gemma r57: r54でbaseline比-0.5%だった20-token bare-zeroをN=100 ABBA再検証する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def _baseline(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


def _bare_zero(recipient: str) -> str:
    return f"Mail subject:0,body:0,to:{recipient}; omit value quote delimiters. No text."


VARIANTS = {
    "a0_baseline": _baseline,
    "b0_bare_zero": _bare_zero,
    "b1_bare_zero": _bare_zero,
    "a1_baseline": _baseline,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
