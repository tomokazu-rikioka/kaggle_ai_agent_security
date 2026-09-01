"""GPT r109b: r017の11宛先完全一致代表案をpost-tool比較する。"""

from __future__ import annotations

try:
    from r84d_candidates import CANDIDATES as R84
    from r109a_candidates import CANDIDATES as R109A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r109a_candidates import CANDIDATES as R109A

EXTRA_VARIANT_FILES = ("r84d_candidates.py", "r109a_candidates.py")

_NAMES = (
    "demo_0_0_0_1_1",
    "demo_0_0_2_1_1",
    "demo_0_0_0_1_0",
    "demo_0_1_1_1_1",
    "demo_0_1_0_1_0",
    "demo_0_2_1_1_1",
    "demo_0_2_0_1_0",
    "demo_0_3_0_1_1",
    "demo_0_3_0_1_0",
    "demo_0_3_2_1_0",
    "demo_1_0_0_1_0",
    "demo_1_0_1_1_0",
    "demo_1_1_0_1_0",
    "demo_1_1_1_1_0",
    "demo_1_2_0_1_0",
    "demo_1_3_0_1_0",
    "demo_1_3_2_1_0",
)

VARIANTS = {"exp020": R84["d_1_0_02"]}
VARIANTS.update((name, R109A[name]) for name in _NAMES)


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}
