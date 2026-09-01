"""GPT r100: exp020とr97e suffix-0勝者をpublic N=2,000 ABBA確認する。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = (
    "lb37710_baseline.py",
    "r84d_candidates.py",
    "r97b_candidates.py",
)

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r84d_candidates import CANDIDATES as R84
    from r97b_candidates import CANDIDATES as R97B
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r97b_candidates import CANDIDATES as R97B

RECIPIENTS = _RECIPIENTS
_EXP020 = R84["d_1_0_02"]
_SUFFIX0 = R97B["b_3_5_0_2_0_0"]

VARIANTS = {
    "exp020_a": _EXP020,
    "suffix0_a": _SUFFIX0,
    "suffix0_b": _SUFFIX0,
    "exp020_b": _EXP020,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
