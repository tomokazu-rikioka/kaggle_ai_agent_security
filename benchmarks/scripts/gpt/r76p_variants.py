"""GPT r76p: post-tool screen for every r69 6/6, 18-token winner."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r69u_candidates.py")

try:
    from lb37710_baseline import message
    from r69u_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r69u_candidates import CANDIDATES

_WINNERS = (
    "u_0_1_19_5",
    "u_0_2_19_5",
    "u_0_0_22_5",
    "u_4_1_15_5",
    "u_0_0_19_5",
    "u_0_0_20_5",
    "u_4_0_19_5",
    "u_0_0_16_5",
    "u_3_0_16_5",
    "u_4_0_15_5",
    "u_4_0_16_5",
    "u_0_0_14_5",
    "u_4_0_14_5",
)

VARIANTS = {"b0_baseline": message}
VARIANTS.update({name: CANDIDATES[name] for name in _WINNERS})
