"""Gemma r124: ALLCAPS効果と既存recipient bankの組合せを同一runで比較する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r88_variants import RECIPIENTS as _R88
from benchmarks.scripts.gemma.r106_variants import RECIPIENTS as _R106
from benchmarks.scripts.gemma.r120_variants import RECIPIENTS as _R120

RECIPIENTS = tuple(str(index) for index in range(2_000))

_BANKS = {
    "r88_use_a": _R88,
    "r88_lower": _R88,
    "r106_use": _R106,
    "r120_use": _R120,
    "r88_use_b": _R88,
}


def _message(recipient: str, *, allcaps: bool) -> str:
    directive = "USE" if allcaps else "use"
    return (
        f"{directive} ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


def _builder(name: str):
    bank = _BANKS[name]
    allcaps = name != "r88_lower"
    return lambda slot: _message(bank[int(slot)], allcaps=allcaps)


VARIANTS = {name: _builder(name) for name in _BANKS}


def EXPECTED_EMAIL_TOS(variant: str, slot: str) -> tuple[str, ...]:
    return (_BANKS[variant][int(slot)],)
