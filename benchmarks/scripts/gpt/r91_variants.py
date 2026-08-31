"""GPT r91: 総入力最短ではなくrecipient後KV suffix最短の1-hop案を比較する。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r82k_candidates.py", "r84d_candidates.py")

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from lb37710_baseline import message
    from r82k_candidates import CANDIDATES as _R82_CANDIDATES
    from r84d_candidates import CANDIDATES as _R84_CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r82k_candidates import CANDIDATES as _R82_CANDIDATES
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as _R84_CANDIDATES

RECIPIENTS = _RECIPIENTS
_SUFFIX0 = _R82_CANDIDATES["k_0_09_1_4_00"]
_SUFFIX9 = _R84_CANDIDATES["d_1_0_02"]

VARIANTS = {
    "b0_baseline_a": message,
    "suffix0_a": _SUFFIX0,
    "suffix9_a": _SUFFIX9,
    "suffix9_b": _SUFFIX9,
    "suffix0_b": _SUFFIX0,
    "b0_baseline_b": message,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)

