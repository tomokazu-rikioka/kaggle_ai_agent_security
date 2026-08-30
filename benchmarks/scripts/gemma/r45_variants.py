"""Gemma r45: 空wrapperを保った9-token Tell短縮案をN=100 ABBA比較する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset({"add", "and", "en", "id", "ip", "ld", "na", "o", "or", "pn", "to", "ur"})


def _baseline(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


def _tell(recipient: str) -> str:
    return f'Tell(to="{recipient}"). Output nothing.'


VARIANTS = {
    "a0_baseline": _baseline,
    "b0_tell": _tell,
    "b1_tell": _tell,
    "a1_baseline": _baseline,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
