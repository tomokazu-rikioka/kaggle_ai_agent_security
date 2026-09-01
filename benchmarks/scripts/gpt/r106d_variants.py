"""GPT r106d: r016唯一のraw完全一致head maskをpost-tool比較する。"""

from __future__ import annotations

try:
    from r84d_candidates import CANDIDATES as R84
    from r106a_candidates import CANDIDATES as R106A
    from r109a_candidates import CANDIDATES as R109A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r106a_candidates import CANDIDATES as R106A
    from benchmarks.scripts.gpt.r109a_candidates import CANDIDATES as R109A

EXTRA_VARIANT_FILES = ("r84d_candidates.py", "r106a_candidates.py", "r109a_candidates.py")

VARIANTS = {
    "exp020": R84["d_1_0_02"],
    "head_no_end_44": R106A["h_5_0_1e_1"],
    "final_demo_48": R109A["demo_0_0_0_1_1"],
}


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}
