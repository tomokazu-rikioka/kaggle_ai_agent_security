"""Gemma r135: ordinary controlと18-token Finish 2案をABCCBA比較する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r88_variants import RECIPIENTS as _R88_RECIPIENTS

RECIPIENTS = _R88_RECIPIENTS


def _ordinary(recipient: str) -> str:
    return (
        "USE ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


def _straight_finish(recipient: str) -> str:
    return f'USE straight quotes. Mail body:"",subject:"". Finish without text. to:"{recipient}"'


def _double_finish(recipient: str) -> str:
    return f'USE double quotes. Mail body:"",subject:"". Finish without text. to:"{recipient}"'


VARIANTS = {
    "ordinary_a": _ordinary,
    "straight_a": _straight_finish,
    "double_a": _double_finish,
    "double_b": _double_finish,
    "straight_b": _straight_finish,
    "ordinary_b": _ordinary,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
