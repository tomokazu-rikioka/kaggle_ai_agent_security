"""GPT r81p: post-tool screen of all public 6/6, 18-call, suffix<=6 candidates."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("r55l_candidates.py", "r56t_candidates.py")

try:
    from r55l_candidates import BASELINE_NAME
    from r55l_candidates import CANDIDATES as R55
    from r56t_candidates import CANDIDATES as R56
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r55l_candidates import BASELINE_NAME
    from benchmarks.scripts.gpt.r55l_candidates import CANDIDATES as R55
    from benchmarks.scripts.gpt.r56t_candidates import CANDIDATES as R56

_R55_NAMES = (
    "l_0_6_6",
    "l_0_7_6",
    "l_0_10_5",
    "l_0_10_6",
    "l_0_11_5",
    "l_0_11_6",
    "l_0_12_5",
    "l_0_12_6",
    "l_0_13_6",
    "l_0_14_5",
    "l_0_14_6",
    "l_0_15_5",
    "l_0_15_6",
    "l_0_16_5",
    "l_0_16_6",
    "l_0_17_5",
    "l_0_17_6",
    "l_0_19_5",
    "l_0_19_6",
    "l_0_20_5",
    "l_0_22_5",
    "l_0_22_6",
    "l_1_7_6",
    "l_1_11_6",
    "l_1_14_5",
    "l_1_14_6",
    "l_1_15_5",
    "l_1_15_6",
    "l_1_16_5",
    "l_1_16_6",
    "l_1_17_5",
    "l_1_19_5",
    "l_1_19_6",
    "l_1_20_5",
    "l_1_22_5",
    "l_2_7_5",
    "l_2_7_6",
    "l_2_8_5",
    "l_2_11_5",
    "l_2_11_6",
    "l_2_14_5",
    "l_2_14_6",
    "l_2_15_5",
    "l_2_15_6",
    "l_2_16_5",
    "l_2_16_6",
    "l_2_17_5",
    "l_2_19_5",
    "l_2_19_6",
    "l_2_20_5",
    "l_2_20_6",
    "l_2_22_5",
    "l_3_7_5",
    "l_3_7_6",
    "l_3_11_5",
    "l_3_11_6",
    "l_3_14_5",
    "l_3_14_6",
    "l_3_15_5",
    "l_3_15_6",
    "l_3_16_5",
    "l_3_16_6",
    "l_3_17_5",
    "l_3_19_5",
    "l_3_19_6",
    "l_3_22_5",
)
_R56_NAMES = ("t_2_02_1_5", "t_2_13_1_5")

VARIANTS = {"b0_baseline": R55[BASELINE_NAME]}
VARIANTS.update((f"r55_{name}", R55[name]) for name in _R55_NAMES)
VARIANTS.update((f"r56_{name}", R56[name]) for name in _R56_NAMES)
