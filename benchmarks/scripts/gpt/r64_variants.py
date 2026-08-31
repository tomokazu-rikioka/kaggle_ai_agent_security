"""GPT r64: N=30 ABBA replay of the 42-token r49d winners."""

from __future__ import annotations

EXTRA_VARIANT_FILES = (
    "lb37710_baseline.py",
    "r47a_candidates.py",
    "r49d_candidates.py",
)

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from lb37710_baseline import message
    from r47a_candidates import CANDIDATES as R47
    from r49d_candidates import CANDIDATES as R49
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r47a_candidates import CANDIDATES as R47
    from benchmarks.scripts.gpt.r49d_candidates import CANDIDATES as R49

RECIPIENTS = _RECIPIENTS

_TOP = ("p_13f0", "p_19f0", "p_15f0", "p_11f8", "p_0bf0")

VARIANTS = {"b0_baseline_a": message, "r50_ascii_a": R47["f_0_0_01_00_0"]}
VARIANTS.update((f"r49_{name}_a", R49[name]) for name in _TOP)
VARIANTS.update((f"r49_{name}_b", R49[name]) for name in reversed(_TOP))
VARIANTS["r50_ascii_b"] = R47["f_0_0_01_00_0"]
VARIANTS["b0_baseline_b"] = message


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
