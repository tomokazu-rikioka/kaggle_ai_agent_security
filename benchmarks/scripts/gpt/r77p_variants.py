"""GPT r77p: post-tool screen for r71's two 6/6 exact 18-token winners."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r71e_candidates.py")

try:
    from lb37710_baseline import message
    from r71e_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r71e_candidates import CANDIDATES

VARIANTS = {
    "b0_baseline": message,
    "e_3_0_02_0_0": CANDIDATES["e_3_0_02_0_0"],
    "e_3_2_06_0_0": CANDIDATES["e_3_2_06_0_0"],
}
