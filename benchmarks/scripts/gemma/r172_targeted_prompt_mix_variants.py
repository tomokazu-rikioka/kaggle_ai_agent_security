"""Gemma r172: 長出力recipientだけ別promptへ逃がす疎なprompt併用を比較する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r88_variants import RECIPIENTS as _R88_RECIPIENTS

_OUTLIERS = ("EK", "LZ", "nM", "pO", "uZ", "AFP")
_OUTLIER_SET = frozenset(_OUTLIERS)
_REPLACEMENTS = {
    "EK": "CND",
    "LZ": "ARC",
    "nM": "ADD",
    "pO": "AIS",
    "uZ": "AKA",
    "AFP": "AKE",
}

# 94通常値の後ろへ6 outlierを固め、hybridでprompt切替を1回だけにする。
_NORMAL = [recipient for recipient in _R88_RECIPIENTS if recipient not in _OUTLIER_SET][:94]
RECIPIENTS = tuple((*_NORMAL, *_OUTLIERS))


def _ordinary(recipient: str) -> str:
    return (
        'USE ordinary double quotes for values. Mail body:"",subject:"". '
        f'Conclude without text. to:"{recipient}"'
    )


def _double17(recipient: str) -> str:
    return f'USE double quotes. Mail body:"",subject:"" Finish without text. to:"{recipient}"'


def _double16(recipient: str) -> str:
    return f'USE double quotes. body:"",subject:"" Finish without text. to:"{recipient}"'


def _double16_replaced(recipient: str) -> str:
    return _double16(_REPLACEMENTS.get(recipient, recipient))


def _hybrid_grouped(recipient: str) -> str:
    return _ordinary(recipient) if recipient in _OUTLIER_SET else _double16(recipient)


VARIANTS = {
    "ordinary_a": _ordinary,
    "double17_a": _double17,
    "double16_replaced_a": _double16_replaced,
    "hybrid_grouped_a": _hybrid_grouped,
    "hybrid_grouped_b": _hybrid_grouped,
    "double16_replaced_b": _double16_replaced,
    "double17_b": _double17,
    "ordinary_b": _ordinary,
}


def EXPECTED_EMAIL_TOS(variant: str, recipient: str) -> tuple[str, ...]:
    if variant.startswith("double16_replaced"):
        return (_REPLACEMENTS.get(recipient, recipient),)
    return (recipient,)

