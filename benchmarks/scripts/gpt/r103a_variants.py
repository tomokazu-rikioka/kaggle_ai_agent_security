"""GPT r103a: suffix-0の固定例示値を空にした案をtool後まで比較する。"""

from __future__ import annotations

try:
    from r84d_candidates import CANDIDATES as R84
    from r99a_candidates import CANDIDATES as R99A
    from r101a_candidates import CANDIDATES as R101A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r99a_candidates import CANDIDATES as R99A
    from benchmarks.scripts.gpt.r101a_candidates import CANDIDATES as R101A

EXTRA_VARIANT_FILES = ("r84d_candidates.py", "r99a_candidates.py", "r101a_candidates.py")

VARIANTS = {
    "exp020": R84["d_1_0_02"],
    "suffix_fixed_z": R99A["q_0_24_2_0"],
    "suffix_empty": R101A["k_0_1_00_00_0_0"],
}


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}
