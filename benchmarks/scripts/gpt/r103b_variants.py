"""GPT r103b: exp020と固定例示to空のsuffix案をABBA比較する。"""

from __future__ import annotations

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r84d_candidates import CANDIDATES as R84
    from r101a_candidates import CANDIDATES as R101A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r101a_candidates import CANDIDATES as R101A

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r84d_candidates.py", "r101a_candidates.py")
RECIPIENTS = _RECIPIENTS

_EXP020 = R84["d_1_0_02"]
_SUFFIX_EMPTY = R101A["k_0_1_00_00_0_0"]

VARIANTS = {
    "exp020_a": _EXP020,
    "suffix_empty_a": _SUFFIX_EMPTY,
    "suffix_empty_b": _SUFFIX_EMPTY,
    "exp020_b": _EXP020,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
