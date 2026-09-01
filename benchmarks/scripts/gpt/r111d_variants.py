"""GPT r111d: r025の11宛先完全一致19案をpost-tool比較する。"""

from __future__ import annotations

try:
    from r84d_candidates import CANDIDATES as R84
    from r111a_candidates import CANDIDATES as R111A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES as R84
    from benchmarks.scripts.gpt.r111a_candidates import CANDIDATES as R111A

EXTRA_VARIANT_FILES = ("r84d_candidates.py", "r111a_candidates.py")

_NAMES = (
    "demo_full",
    "mask_1fd",
    "mask_1fe",
    "mask_1ff",
    "mask_27f",
    "mask_2f9",
    "mask_2fb",
    "mask_2ff",
    "mask_37b",
    "mask_37d",
    "mask_37e",
    "mask_37f",
    "mask_3bb",
    "mask_3be",
    "mask_3bf",
    "mask_3f9",
    "mask_3fb",
    "mask_3fd",
    "mask_3fe",
)

VARIANTS = {"exp020": R84["d_1_0_02"]}
VARIANTS.update((name, R111A[name]) for name in _NAMES)


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}
