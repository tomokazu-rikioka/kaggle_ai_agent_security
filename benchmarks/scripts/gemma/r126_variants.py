"""Gemma r126: r123aの引用符指示をr88先頭100 recipientへ拡張する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r88_variants import RECIPIENTS as _R88_RECIPIENTS
from benchmarks.scripts.gemma.r123a_variants import VARIANTS as _R123A_VARIANTS

RECIPIENTS = _R88_RECIPIENTS
VARIANTS = _R123A_VARIANTS


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
