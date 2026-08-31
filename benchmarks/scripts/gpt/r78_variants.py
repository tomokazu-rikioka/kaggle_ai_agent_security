"""GPT r78: unified ABBA raw/s bench for every full-hop Pareto candidate."""

from __future__ import annotations

EXTRA_VARIANT_FILES = (
    "lb37710_baseline.py",
    "r49d_candidates.py",
    "r63n_candidates.py",
)

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from lb37710_baseline import message
    from r49d_candidates import CANDIDATES as R49
    from r63n_candidates import CANDIDATES as R63
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r49d_candidates import CANDIDATES as R49
    from benchmarks.scripts.gpt.r63n_candidates import CANDIDATES as R63

RECIPIENTS = _RECIPIENTS

_CANDIDATES = (
    ("r49_p_13f0", R49["p_13f0"]),
    ("r49_p_19f0", R49["p_19f0"]),
    ("r49_p_15f0", R49["p_15f0"]),
    ("r63_empty_a", R63["n_6_02_4"]),
    ("r63_empty_b", R63["n_6_04_1"]),
)

VARIANTS = {"b0_baseline_a": message}
VARIANTS.update((f"{name}_a", builder) for name, builder in _CANDIDATES)
VARIANTS.update((f"{name}_b", builder) for name, builder in reversed(_CANDIDATES))
VARIANTS["b0_baseline_b"] = message


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
