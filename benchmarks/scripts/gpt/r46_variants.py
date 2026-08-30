"""GPT r46: full ABBA replay for r43's two shortest low-NLL layouts."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r32a_candidates.py")

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from lb37710_baseline import message
    from r32a_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r32a_candidates import CANDIDATES

RECIPIENTS = _RECIPIENTS

VARIANTS = {
    "b0_baseline_a": message,
    "g_al_11_2_0_a": CANDIDATES["al_11_2_0"],
    "g_al_11_2_2_a": CANDIDATES["al_11_2_2"],
    "g_al_11_2_2_b": CANDIDATES["al_11_2_2"],
    "g_al_11_2_0_b": CANDIDATES["al_11_2_0"],
    "b0_baseline_b": message,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
