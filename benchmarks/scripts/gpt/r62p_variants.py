"""GPT r62p: post-tool screen for r49d and r47b+ASCII 42-token candidates."""

from __future__ import annotations

EXTRA_VARIANT_FILES = (
    "lb37710_baseline.py",
    "r49d_candidates.py",
    "r55l_candidates.py",
)

try:
    from lb37710_baseline import message
    from r49d_candidates import CANDIDATES as R49
    from r55l_candidates import CANDIDATES as R55
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r49d_candidates import CANDIDATES as R49
    from benchmarks.scripts.gpt.r55l_candidates import CANDIDATES as R55

_R49_TOP = ("p_13f0", "p_19f0", "p_15f0", "p_11f8", "p_0bf0")
_R55_TOP = ("s_1_0", "s_1_1", "s_2_0", "s_2_1", "s_3_0", "s_3_1")

VARIANTS = {"b0_baseline": message}
VARIANTS.update({f"d_{name}": R49[name] for name in _R49_TOP})
VARIANTS.update({f"a_{name}": R55[name] for name in _R55_TOP})
