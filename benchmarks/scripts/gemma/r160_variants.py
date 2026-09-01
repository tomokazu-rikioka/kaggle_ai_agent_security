"""Gemma r160: r88全2,000中の6長出力recipientを実生成16-token値へ交換する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r88_variants import RECIPIENTS as _R88_RECIPIENTS

_RECIPIENTS = list(_R88_RECIPIENTS)
_REPLACEMENTS = {
    265: "CND",  # EK
    590: "ARC",  # LZ
    1583: "ADD",  # nM
    1647: "AIS",  # pO
    1777: "AKA",  # uZ
    1988: "AKE",  # AFP
}
for _index, _replacement in _REPLACEMENTS.items():
    _RECIPIENTS[_index] = _replacement
RECIPIENTS = tuple(_RECIPIENTS)

if len(RECIPIENTS) != 2_000 or len(set(RECIPIENTS)) != 2_000:
    raise RuntimeError("r160 recipient bank must contain 2,000 unique labels")


def _double16(recipient: str) -> str:
    return f'USE double quotes. body:"",subject:"" Finish without text. to:"{recipient}"'


VARIANTS = {"double16_replaced6": _double16}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
