"""GPT r104a: r101aの42-token正準callと41-token欠落例を11宛先で検証する。"""

from __future__ import annotations

try:
    from r84d_candidates import CANDIDATES as R84
    from r101a_candidates import CANDIDATES as R101A
    from r101a_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from r101a_candidates import EXPECTED_MARKER as _EXPECTED_MARKER
    from r101a_candidates import TARGET_TEXT as _TARGET_TEXT
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r101a_candidates import CANDIDATES as R101A
    from benchmarks.scripts.gpt.r101a_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from benchmarks.scripts.gpt.r101a_candidates import EXPECTED_MARKER as _EXPECTED_MARKER
    from benchmarks.scripts.gpt.r101a_candidates import TARGET_TEXT as _TARGET_TEXT

EXTRA_CANDIDATE_FILES = ("r84d_candidates.py", "r101a_candidates.py")
BASELINE_NAME = "b0_exp020"
EXPECTED_ARGUMENTS = _EXPECTED_ARGUMENTS
EXPECTED_MARKER = _EXPECTED_MARKER
TARGET_TEXT = _TARGET_TEXT

_NAMES = (
    "k_0_0_00_00_2_1",
    "k_0_0_00_01_2_1",
    "k_0_0_01_00_2_1",
    "k_0_0_01_01_2_1",
    "k_0_0_02_00_2_1",
    "k_0_0_02_01_2_1",
    "k_0_0_03_00_2_1",
    "k_0_0_04_00_2_1",
    "k_0_0_04_01_2_1",
    "k_0_0_10_00_2_1",
    "k_0_1_00_00_2_0",
    "k_0_2_00_00_2_0",
    "k_0_2_00_01_2_0",
)

CANDIDATES = {BASELINE_NAME: R84["d_1_0_02"]}
CANDIDATES.update((name, R101A[name]) for name in _NAMES)
