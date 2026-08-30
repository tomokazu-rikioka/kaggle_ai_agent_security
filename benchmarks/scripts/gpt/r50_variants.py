"""GPT r50: N=30 ABBA replay of r47a's three shortest user-role candidates."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r47a_candidates.py")

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from lb37710_baseline import message
    from r47a_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r47a_candidates import CANDIDATES

RECIPIENTS = _RECIPIENTS

_TOP = (
    "f_0_0_01_00_0",
    "f_0_0_02_00_0",
    "f_0_0_03_00_0",
)

VARIANTS = {"b0_baseline_a": message}
VARIANTS.update((f"g_{name}_a", CANDIDATES[name]) for name in _TOP)
VARIANTS.update((f"g_{name}_b", CANDIDATES[name]) for name in reversed(_TOP))
VARIANTS["b0_baseline_b"] = message


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
