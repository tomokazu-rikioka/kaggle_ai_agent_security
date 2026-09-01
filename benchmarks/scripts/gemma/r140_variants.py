"""Gemma r140: ordinaryとFinish without responseをN=500 ABBA比較する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r88_variants import RECIPIENTS as _R88_RECIPIENTS

RECIPIENTS = _R88_RECIPIENTS


def _ordinary(recipient: str) -> str:
    return (
        "USE ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


def _response(recipient: str) -> str:
    return f'USE straight quotes. Mail body:"",subject:"". Finish without response. to:"{recipient}"'


VARIANTS = {
    "ordinary_a": _ordinary,
    "response_a": _response,
    "response_b": _response,
    "ordinary_b": _ordinary,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
