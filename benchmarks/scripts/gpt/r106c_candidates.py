"""GPT r106c: r013でraw成功があった全head maskを11宛先へ拡張する。"""

from __future__ import annotations

try:
    from r106a_candidates import CANDIDATES as R106A
    from r106a_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from r106a_candidates import EXPECTED_MARKER as _EXPECTED_MARKER
    from r106a_candidates import TARGET_TEXT as _TARGET_TEXT
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r106a_candidates import CANDIDATES as R106A
    from benchmarks.scripts.gpt.r106a_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from benchmarks.scripts.gpt.r106a_candidates import EXPECTED_MARKER as _EXPECTED_MARKER
    from benchmarks.scripts.gpt.r106a_candidates import TARGET_TEXT as _TARGET_TEXT

BASELINE_NAME = "b0_exp020"
EXPECTED_ARGUMENTS = _EXPECTED_ARGUMENTS
EXPECTED_MARKER = _EXPECTED_MARKER
TARGET_TEXT = _TARGET_TEXT
EXTRA_CANDIDATE_FILES = ("r106a_candidates.py",)

_MASKS = (0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F)

CANDIDATES = {BASELINE_NAME: R106A[BASELINE_NAME]}
for placeholder_index in range(6):
    for task_index in range(2):
        for head_mask in _MASKS:
            for payload_style in range(2):
                name = f"h_{placeholder_index}_{task_index}_{head_mask:02x}_{payload_style}"
                CANDIDATES[name] = R106A[name]
