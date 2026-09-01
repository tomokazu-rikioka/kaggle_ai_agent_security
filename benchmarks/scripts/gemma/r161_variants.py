"""Gemma r161: 16-token FinishとEndを交換済みbankでN=500 ABBA比較する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r160_variants import RECIPIENTS as _R160_RECIPIENTS

RECIPIENTS = _R160_RECIPIENTS


def _builder(template: str):
    return lambda recipient: template.format(r=recipient)


_FINISH = 'USE double quotes. body:"",subject:"" Finish without text. to:"{r}"'
_END = 'USE double quotes. body:"",subject:"" End without text. to:"{r}"'

VARIANTS = {
    "finish_a": _builder(_FINISH),
    "end_a": _builder(_END),
    "end_b": _builder(_END),
    "finish_b": _builder(_FINISH),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
