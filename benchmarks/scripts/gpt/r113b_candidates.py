"""GPT r113b: r113aの42–43 input-token成功案を11宛先で検証する。"""

from __future__ import annotations

try:
    from r113a_candidates import CANDIDATES as ALL_CANDIDATES
    from r113a_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from r113a_candidates import EXPECTED_MARKER as _EXPECTED_MARKER
    from r113a_candidates import TARGET_TEXT as _TARGET_TEXT
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r113a_candidates import CANDIDATES as ALL_CANDIDATES
    from benchmarks.scripts.gpt.r113a_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from benchmarks.scripts.gpt.r113a_candidates import EXPECTED_MARKER as _EXPECTED_MARKER
    from benchmarks.scripts.gpt.r113a_candidates import TARGET_TEXT as _TARGET_TEXT

EXPECTED_ARGUMENTS = _EXPECTED_ARGUMENTS
EXPECTED_MARKER = _EXPECTED_MARKER
TARGET_TEXT = _TARGET_TEXT
BASELINE_NAME = "v_0_0_0_2_0"

_NAMES = (
    "v_0_0_0_2_0",
    "v_0_0_0_2_2",
    "v_0_0_17_2_0",
    "v_0_0_19_2_0",
    "v_0_0_1_2_0",
    "v_0_0_21_2_0",
    "v_0_0_23_2_0",
    "v_0_0_25_2_0",
    "v_0_0_2_2_0",
    "v_0_0_3_2_0",
    "v_0_0_5_2_0",
    "v_0_0_7_2_0",
    "v_0_1_0_2_0",
    "v_0_1_0_2_2",
    "v_0_1_17_2_0",
    "v_0_1_19_2_0",
    "v_0_1_23_2_0",
    "v_0_1_2_2_0",
    "v_0_1_3_2_0",
    "v_0_1_5_2_0",
    "v_0_1_7_2_0",
    "v_1_0_0_2_0",
    "v_1_0_11_2_0",
    "v_1_0_5_2_0",
    "v_1_1_5_2_0",
)

CANDIDATES = {name: ALL_CANDIDATES[name] for name in _NAMES}
