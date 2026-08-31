"""GPT r66p: post-tool screen for the r63 partial/no-example Pareto points."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r63n_candidates.py")

try:
    from lb37710_baseline import message
    from r63n_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r63n_candidates import CANDIDATES

VARIANTS = {
    "b0_baseline": message,
    "private_empty_example_a": CANDIDATES["n_6_02_4"],
    "private_empty_example_b": CANDIDATES["n_6_04_1"],
    "public_partial_header": CANDIDATES["n_2_04_3"],
    "public_no_example": CANDIDATES["n_0_04_1"],
}
