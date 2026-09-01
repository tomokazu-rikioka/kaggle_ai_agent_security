"""GPT r98: exp020とr97のKV Pareto 2案をpublic N=30 ABBA比較する。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = (
    "lb37710_baseline.py",
    "r84d_candidates.py",
    "r97b_candidates.py",
    "r97d_candidates.py",
)

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r84d_candidates import CANDIDATES as R84
    from r97b_candidates import CANDIDATES as R97B
    from r97d_candidates import CANDIDATES as R97D
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r97b_candidates import CANDIDATES as R97B
    from benchmarks.scripts.gpt.r97d_candidates import CANDIDATES as R97D

_EXP020 = R84["d_1_0_02"]
_SUFFIX0 = R97B["b_3_5_0_2_0_0"]
_SUFFIX7 = R97D["d_1_1_2_0_05"]
RECIPIENTS = _RECIPIENTS

VARIANTS = {
    "exp020_a": _EXP020,
    "suffix0_a": _SUFFIX0,
    "suffix7_a": _SUFFIX7,
    "suffix7_b": _SUFFIX7,
    "suffix0_b": _SUFFIX0,
    "exp020_b": _EXP020,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
