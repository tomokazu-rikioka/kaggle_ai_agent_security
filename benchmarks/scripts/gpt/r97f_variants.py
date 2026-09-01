"""GPT r97f: r97dで8/8 canonical callだった44案をtool実行後まで全確認する。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("r97d_candidates.py",)

try:
    from r97d_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r97d_candidates import CANDIDATES

_NAMES = (
    "d_0_1_0_0_05",
    "d_0_1_0_0_06",
    "d_0_1_0_1_03",
    "d_0_1_0_2_03",
    "d_0_1_0_3_03",
    "d_0_1_0_3_11",
    "d_0_1_1_2_11",
    "d_0_1_1_2_13",
    "d_0_1_2_0_03",
    "d_0_1_2_0_05",
    "d_0_1_2_0_06",
    "d_0_1_2_0_07",
    "d_0_1_2_0_11",
    "d_0_1_2_0_12",
    "d_0_1_2_0_13",
    "d_0_1_3_0_03",
    "d_0_1_3_0_05",
    "d_0_1_3_0_06",
    "d_0_1_3_0_07",
    "d_0_1_3_0_13",
    "d_0_1_3_2_03",
    "d_0_1_3_3_03",
    "d_0_1_4_0_06",
    "d_0_1_4_0_07",
    "d_0_1_4_0_11",
    "d_0_1_4_0_12",
    "d_0_1_4_0_13",
    "d_0_1_4_2_07",
    "d_0_1_4_2_11",
    "d_1_1_2_0_03",
    "d_1_1_2_0_05",
    "d_1_1_2_0_06",
    "d_1_1_2_0_07",
    "d_1_1_2_0_11",
    "d_1_1_2_0_12",
    "d_1_1_2_0_13",
    "d_1_1_3_0_03",
    "d_1_1_3_0_05",
    "d_1_1_3_0_11",
    "d_1_1_4_0_05",
    "d_1_1_4_0_07",
    "d_1_1_4_0_11",
    "d_1_1_4_0_12",
    "d_1_1_4_0_13",
)

VARIANTS = {"b0_exp020": CANDIDATES["b0_exp020"]}
VARIANTS.update((name, CANDIDATES[name]) for name in _NAMES)


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}
