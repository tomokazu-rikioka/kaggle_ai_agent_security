"""GPT r113c: 43-token空final案を48-token原型・exp020とpost-tool比較する。"""

from __future__ import annotations

try:
    from r84d_candidates import CANDIDATES as R84
    from r109a_candidates import CANDIDATES as R109A
    from r113a_candidates import CANDIDATES as R113A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r109a_candidates import CANDIDATES as R109A
    from benchmarks.scripts.gpt.r113a_candidates import CANDIDATES as R113A

EXTRA_VARIANT_FILES = ("r84d_candidates.py", "r109a_candidates.py", "r113a_candidates.py")

VARIANTS = {
    "exp020": R84["d_1_0_02"],
    "demo_48": R109A["demo_0_0_0_1_1"],
    "demo_43": R113A["v_0_0_0_2_2"],
}


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}
