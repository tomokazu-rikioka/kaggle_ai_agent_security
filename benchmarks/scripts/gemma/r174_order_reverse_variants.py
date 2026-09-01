"""Gemma r174: original/reverse候補順をABBAで再比較する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r160_variants import RECIPIENTS as _R160_RECIPIENTS

_BANK = tuple(_R160_RECIPIENTS[:500])
RECIPIENTS = tuple(str(index) for index in range(len(_BANK)))


def _message(recipient: str) -> str:
    return f'USE double quotes. body:"",subject:"" Finish without text. to:"{recipient}"'


def _original(index: str) -> str:
    return _message(_BANK[int(index)])


def _reverse(index: str) -> str:
    return _message(_BANK[-1 - int(index)])


VARIANTS = {
    "original_a": _original,
    "reverse_a": _reverse,
    "reverse_b": _reverse,
    "original_b": _original,
}


def EXPECTED_EMAIL_TOS(variant: str, index: str) -> tuple[str, ...]:
    bank_index = -1 - int(index) if variant.startswith("reverse") else int(index)
    return (_BANK[bank_index],)

