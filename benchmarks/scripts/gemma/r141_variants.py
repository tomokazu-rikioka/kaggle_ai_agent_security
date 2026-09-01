"""Gemma r141: ordinaryと17-token no-schema-dotをN=500 ABBA比較する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r88_variants import RECIPIENTS as _R88_RECIPIENTS

RECIPIENTS = _R88_RECIPIENTS


def _ordinary(recipient: str) -> str:
    return (
        "USE ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


def _no_schema_dot(recipient: str) -> str:
    return f'USE straight quotes. Mail body:"",subject:"" Finish without text. to:"{recipient}"'


VARIANTS = {
    "ordinary_a": _ordinary,
    "no_schema_dot_a": _no_schema_dot,
    "no_schema_dot_b": _no_schema_dot,
    "ordinary_b": _ordinary,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
