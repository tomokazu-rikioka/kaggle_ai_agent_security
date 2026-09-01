"""GPT r110: exp020、suffix-0、空final履歴3案をpublic N=100で比較する。"""

from __future__ import annotations

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r84d_candidates import CANDIDATES as R84
    from r97b_candidates import CANDIDATES as R97B
    from r109a_candidates import CANDIDATES as R109A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r97b_candidates import CANDIDATES as R97B
    from benchmarks.scripts.gpt.r109a_candidates import CANDIDATES as R109A

EXTRA_VARIANT_FILES = (
    "lb37710_baseline.py",
    "r84d_candidates.py",
    "r97b_candidates.py",
    "r109a_candidates.py",
)
RECIPIENTS = _RECIPIENTS

_EXP020 = R84["d_1_0_02"]
_SUFFIX0 = R97B["b_3_5_0_2_0_0"]
_DEMO_END_Z = R109A["demo_0_0_0_1_1"]
_DEMO_CALL_Z = R109A["demo_0_1_1_1_1"]
_DEMO_END_EMPTY = R109A["demo_1_0_0_1_0"]

VARIANTS = {
    "exp020_a": _EXP020,
    "suffix0_a": _SUFFIX0,
    "demo_end_z_a": _DEMO_END_Z,
    "demo_call_z_a": _DEMO_CALL_Z,
    "demo_end_empty_a": _DEMO_END_EMPTY,
    "demo_end_empty_b": _DEMO_END_EMPTY,
    "demo_call_z_b": _DEMO_CALL_Z,
    "demo_end_z_b": _DEMO_END_Z,
    "suffix0_b": _SUFFIX0,
    "exp020_b": _EXP020,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
