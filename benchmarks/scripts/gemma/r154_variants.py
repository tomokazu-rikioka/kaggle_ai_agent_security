"""Gemma r154: 16-token本命の2長出力recipientを既知の短出力値へ交換する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r88_variants import RECIPIENTS as _R88_RECIPIENTS

_RECIPIENTS = list(_R88_RECIPIENTS)
_RECIPIENTS[265] = "CND"  # EK: r152で17>4、CND: r144で16>4を確認済み。
_RECIPIENTS[590] = "ARC"  # LZ: r152で17>4、ARC: r144で16>4を確認済み。
RECIPIENTS = tuple(_RECIPIENTS)

if len(RECIPIENTS) != 2_000 or len(set(RECIPIENTS)) != 2_000:
    raise RuntimeError("r154 recipient bank must contain 2,000 unique labels")


def _double16(recipient: str) -> str:
    return f'USE double quotes. body:"",subject:"" Finish without text. to:"{recipient}"'


VARIANTS = {"double16_replaced": _double16}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
