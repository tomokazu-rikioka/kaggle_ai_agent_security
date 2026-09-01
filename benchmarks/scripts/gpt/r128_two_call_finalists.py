"""GPT r128: normally generate the r126 target-NLL finalists."""

from __future__ import annotations

try:
    from r30_variants import VARIANTS as _R30
    from r122_two_call_history_variants import VARIANTS as _R122
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r30_variants import VARIANTS as _R30
    from benchmarks.scripts.gpt.r122_two_call_history_variants import VARIANTS as _R122

_SELECTED = (
    "h_1_2_06_0",
    "h_2_2_10_0",
    "h_2_2_06_0",
    "h_2_2_01_0",
    "h_2_2_11_0",
    "h_1_2_10_0",
    "h_2_2_00_0",
    "h_1_2_01_0",
    "h_1_2_00_0",
    "h_2_2_17_0",
    "h_2_2_08_0",
    "h_1_2_07_0",
    "h_1_2_25_0",
    "h_1_2_08_0",
    "h_1_2_11_0",
    "h_2_2_25_0",
    "h_2_2_24_0",
    "h_1_2_24_0",
    "h_1_2_03_0",
    "h_1_2_02_0",
)

VARIANTS = {
    "single_control": _R122["b0_single"],
    "stable_r30": _R30["b1_two"],
    **{name: _R122[name] for name in _SELECTED},
}


def EXPECTED_EMAIL_TOS(variant: str, recipient: str) -> tuple[str, ...]:
    if variant == "single_control":
        return (recipient,)
    if variant == "stable_r30":
        return (recipient, f"{recipient}.x")
    return (recipient, recipient)
