"""Gemma r25: system promptのtool順序参照をN=30で確認する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def _baseline(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


def _hash9(recipient: str) -> str:
    return f'#9 subject="" body="" to="{recipient}". Output nothing.'


VARIANTS = {
    "b0_existing": _baseline,
    "a1_hash9": _hash9,
    "a2_declaration9": lambda r: f'Invoke declaration 9: body="" subject="" to="{r}". Output nothing.',
    "a3_call9": lambda r: f'Call tool 9 once: subject="" body="" to="{r}". Output nothing.',
    "a4_hash9_repeat": _hash9,
    "b5_existing_repeat": _baseline,
}
