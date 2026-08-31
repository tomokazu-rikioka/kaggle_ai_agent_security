"""GPT r79: public N=2,000 ABBA of baseline versus r49 p_19f0."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r49d_candidates.py")

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from lb37710_baseline import message
    from r49d_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r49d_candidates import CANDIDATES

RECIPIENTS = _RECIPIENTS
_R49 = CANDIDATES["p_19f0"]

VARIANTS = {
    "b0_baseline_a": message,
    "r49_p_19f0_a": _R49,
    "r49_p_19f0_b": _R49,
    "b0_baseline_b": message,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
