"""GPT r52a: targeted screen for dynamic-recipient synthetic examples."""

from __future__ import annotations

EXTRA_CANDIDATE_FILES = ("r52d_candidates.py",)

try:
    from r52d_candidates import CANDIDATES as _ALL_CANDIDATES
    from r52d_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from r52d_candidates import EXPECTED_MARKER as _EXPECTED_MARKER
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r52d_candidates import CANDIDATES as _ALL_CANDIDATES
    from benchmarks.scripts.gpt.r52d_candidates import EXPECTED_ARGUMENTS as _EXPECTED_ARGUMENTS
    from benchmarks.scripts.gpt.r52d_candidates import EXPECTED_MARKER as _EXPECTED_MARKER

BASELINE_NAME = "b0_lb37710"
EXPECTED_ARGUMENTS = _EXPECTED_ARGUMENTS
EXPECTED_MARKER = _EXPECTED_MARKER


def _targeted(name: str) -> bool:
    if name == BASELINE_NAME:
        return True
    parts = name.split("_")
    # Current header, user continuation, compact JSON or equals arguments.
    return parts[1] == "0" and parts[3] in {"0", "2"} and parts[5] == "0"


CANDIDATES = {name: builder for name, builder in _ALL_CANDIDATES.items() if _targeted(name)}
