"""GPT r105a: r009/r010通過案のtool後finalを比較する。"""

from __future__ import annotations

try:
    from r84d_candidates import CANDIDATES as R84
    from r101a_candidates import CANDIDATES as R101A
    from r102a_candidates import CANDIDATES as R102A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r101a_candidates import CANDIDATES as R101A
    from benchmarks.scripts.gpt.r102a_candidates import CANDIDATES as R102A

EXTRA_VARIANT_FILES = ("r84d_candidates.py", "r101a_candidates.py", "r102a_candidates.py")

VARIANTS = {
    "exp020": R84["d_1_0_02"],
    "no_example_15_23": R102A["j_0_02_3_0"],
    "fixed_to_42_18": R101A["k_0_0_10_00_2_1"],
    "empty_to_43_18": R101A["k_0_1_00_00_2_0"],
    "missing_to_41_20": R101A["k_0_2_00_00_2_0"],
}


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}
