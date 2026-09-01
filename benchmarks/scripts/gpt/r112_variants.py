"""GPT r112: exp020 と空final履歴をpublic N=2,000 ABBAで比較する。"""

from __future__ import annotations

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r84d_candidates import CANDIDATES as R84
    from r109a_candidates import CANDIDATES as R109A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r109a_candidates import CANDIDATES as R109A

EXTRA_VARIANT_FILES = (
    "lb37710_baseline.py",
    "r84d_candidates.py",
    "r109a_candidates.py",
)
RECIPIENTS = _RECIPIENTS

_EXP020 = R84["d_1_0_02"]
_DEMO_END_Z = R109A["demo_0_0_0_1_1"]

VARIANTS = {
    "exp020_a": _EXP020,
    "demo_end_z_a": _DEMO_END_Z,
    "demo_end_z_b": _DEMO_END_Z,
    "exp020_b": _EXP020,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
