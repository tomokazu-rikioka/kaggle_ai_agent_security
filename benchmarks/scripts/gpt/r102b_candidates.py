"""GPT r102b: r102aの最短semantic成功を失敗recipient込みで再検証する。"""

from __future__ import annotations

try:
    from r84d_candidates import CANDIDATES as R84
    from r102a_candidates import CANDIDATES as R102A
    from r102a_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from r102a_candidates import EXPECTED_MARKER as _EXPECTED_MARKER
    from r102a_candidates import TARGET_TEXT as _TARGET_TEXT
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r102a_candidates import CANDIDATES as R102A
    from benchmarks.scripts.gpt.r102a_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from benchmarks.scripts.gpt.r102a_candidates import EXPECTED_MARKER as _EXPECTED_MARKER
    from benchmarks.scripts.gpt.r102a_candidates import TARGET_TEXT as _TARGET_TEXT

EXTRA_CANDIDATE_FILES = ("r84d_candidates.py", "r102a_candidates.py")
BASELINE_NAME = "b0_exp020"
EXPECTED_ARGUMENTS = _EXPECTED_ARGUMENTS
EXPECTED_MARKER = _EXPECTED_MARKER
TARGET_TEXT = _TARGET_TEXT

_NAMES = (
    "j_2_25_3_2",
    "j_0_02_3_0",
    "j_0_03_0_2",
    "j_0_03_1_3",
    "j_0_03_3_1",
    "j_0_15_3_0",
    "j_0_38_1_2",
    "j_0_38_3_0",
    "j_1_02_2_2",
    "j_2_12_3_2",
    "j_0_03_1_2",
    "j_0_03_3_0",
    "j_0_08_3_0",
    "j_0_11_0_0",
    "j_0_11_1_1",
    "j_0_25_0_0",
    "j_0_25_1_1",
    "j_0_27_1_0",
    "j_0_36_0_0",
    "j_0_37_3_0",
    "j_1_03_3_2",
    "j_1_11_3_0",
    "j_1_13_3_0",
    "j_1_02_1_3",
    "j_1_02_3_1",
    "j_2_11_3_0",
    "j_2_13_3_0",
    "j_2_25_2_0",
    "j_2_25_3_0",
    "j_3_13_3_0",
    "j_3_25_3_0",
    "j_3_12_0_2",
    "j_3_19_3_0",
)

CANDIDATES = {BASELINE_NAME: R84["d_1_0_02"]}
CANDIDATES.update((name, R102A[name]) for name in _NAMES)
