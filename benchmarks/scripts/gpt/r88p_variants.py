"""GPT r88p: r84dの全recipient完全一致候補をtool実行後まで再検証する。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("r84d_candidates.py",)

try:
    from r84d_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES

_NAMES = (
    "b0_lb37710",
    "d_0_0_00", "d_0_0_01", "d_0_0_02", "d_0_0_03", "d_0_0_19",
    "d_0_2_01", "d_0_2_04", "d_0_2_13", "d_0_2_14", "d_0_2_20", "d_0_2_21",
    "d_1_0_02", "d_1_0_03", "d_1_0_08", "d_1_0_10", "d_1_0_14", "d_1_0_19",
    "d_1_1_00", "d_1_1_03", "d_1_1_06", "d_1_1_14", "d_1_1_16",
    "d_2_0_03", "d_2_0_15", "d_2_0_16", "d_2_0_19",
    "d_2_2_02", "d_2_2_04", "d_2_2_05", "d_2_2_10", "d_2_2_14", "d_2_2_17",
    "d_3_0_02", "d_3_0_03", "d_3_0_05", "d_3_0_19",
    "d_4_0_02", "d_4_0_03", "d_4_0_12", "d_4_0_14", "d_4_0_15", "d_4_0_16", "d_4_0_17",
    "d_5_0_03", "d_5_0_04", "d_5_0_14", "d_5_0_20", "d_5_1_06",
)

VARIANTS = {name: CANDIDATES[name] for name in _NAMES}


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}

