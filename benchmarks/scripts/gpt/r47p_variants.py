"""GPT r47p: post-tool continuation check for every r47b task encoding."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("r47b_candidates.py",)

try:
    from r47b_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r47b_candidates import CANDIDATES

VARIANTS = CANDIDATES
