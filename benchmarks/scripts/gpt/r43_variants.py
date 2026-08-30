"""GPT r43: post-tool sweep over r32a layout × ending/action combinations."""

from __future__ import annotations

from collections.abc import Callable

EXTRA_VARIANT_FILES = ("r32a_candidates.py",)

try:
    from r32a_candidates import BASELINE_NAME, CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r32a_candidates import BASELINE_NAME, CANDIDATES

VARIANTS: dict[str, Callable[[str], str]] = {"b0_baseline_a": CANDIDATES[BASELINE_NAME]}
VARIANTS.update(
    (name, builder) for name, builder in CANDIDATES.items() if name.startswith(("le_", "al_"))
)
VARIANTS["b9_baseline_b"] = CANDIDATES[BASELINE_NAME]
