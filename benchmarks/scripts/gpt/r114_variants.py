"""GPT r114: exp020と45-token空final履歴をN=1,500 ABBA比較する。"""

from __future__ import annotations

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r84d_candidates import CANDIDATES as R84
    from r111a_candidates import CANDIDATES as R111A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r111a_candidates import CANDIDATES as R111A

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r84d_candidates.py", "r111a_candidates.py")
RECIPIENTS = _RECIPIENTS

_EXP020 = R84["d_1_0_02"]
_DEMO_45 = R111A["mask_2f9"]

VARIANTS = {
    "exp020_a": _EXP020,
    "demo_45_a": _DEMO_45,
    "demo_45_b": _DEMO_45,
    "exp020_b": _EXP020,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
