"""Gemma r125: r88 bankでALLCAPS ordinaryとALLCAPS straightをABBA比較する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r88_variants import RECIPIENTS as _R88_RECIPIENTS

RECIPIENTS = _R88_RECIPIENTS


def _ordinary(recipient: str) -> str:
    return (
        "USE ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


def _straight(recipient: str) -> str:
    return f'USE straight quotes. Mail body:"",subject:"". Conclude without text. to:"{recipient}"'


VARIANTS = {
    "ordinary_a": _ordinary,
    "straight_a": _straight,
    "straight_b": _straight,
    "ordinary_b": _ordinary,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
