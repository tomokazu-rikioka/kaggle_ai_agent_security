"""GPT r80v: validate every r75 primary-success trade-off on six recipients."""

from __future__ import annotations

EXTRA_CANDIDATE_FILES = ("r75a_candidates.py",)

try:
    from r75a_candidates import CANDIDATES as R75
    from r75a_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from r75a_candidates import EXPECTED_MARKER as _EXPECTED_MARKER
    from r75a_candidates import TARGET_TEXT as _TARGET_TEXT
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r75a_candidates import CANDIDATES as R75
    from benchmarks.scripts.gpt.r75a_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from benchmarks.scripts.gpt.r75a_candidates import EXPECTED_MARKER as _EXPECTED_MARKER
    from benchmarks.scripts.gpt.r75a_candidates import TARGET_TEXT as _TARGET_TEXT

BASELINE_NAME = "b0_lb37710"
EXPECTED_ARGUMENTS = _EXPECTED_ARGUMENTS
EXPECTED_MARKER = _EXPECTED_MARKER
TARGET_TEXT = _TARGET_TEXT
_PRIMARY_SUCCESSES = (
    "a_0_15_1_1",
    "a_1_05_0_1",
    "a_1_14_0_1",
    "a_1_15_1_1",
    "a_2_06_1_1",
    "a_3_10_1_1",
    "a_4_14_1_0",
    "a_5_05_0_1",
    "a_6_00_1_0",
    "a_6_04_1_0",
    "a_6_05_0_1",
    "a_6_10_1_0",
    "a_6_11_1_1",
    "a_6_14_1_0",
)

CANDIDATES = {BASELINE_NAME: R75[BASELINE_NAME]}
CANDIDATES.update((name, R75[name]) for name in _PRIMARY_SUCCESSES)
