"""GPT r97e: r97bのsuffix-0完全call 3案をtool実行後まで確認する。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("r84d_candidates.py", "r97b_candidates.py")

try:
    from r84d_candidates import CANDIDATES as R84
    from r97b_candidates import CANDIDATES as R97B
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r97b_candidates import CANDIDATES as R97B

_NAMES = (
    "b_3_5_0_1_0_1",
    "b_0_5_0_1_0_1",
    "b_3_5_0_2_0_0",
)

VARIANTS = {"b0_exp020": R84["d_1_0_02"]}
VARIANTS.update((name, R97B[name]) for name in _NAMES)


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}
