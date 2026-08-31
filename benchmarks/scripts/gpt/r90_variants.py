"""GPT r90: r88p最短安定1-hop候補2案をpublic N=30 ABBAで比較する。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r84d_candidates.py")

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from lb37710_baseline import message
    from r84d_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r84d_candidates import CANDIDATES

RECIPIENTS = _RECIPIENTS
_D0 = CANDIDATES["d_0_2_04"]
_D2 = CANDIDATES["d_2_2_04"]

VARIANTS = {
    "b0_baseline_a": message,
    "d0_short_a": _D0,
    "d2_short_a": _D2,
    "d2_short_b": _D2,
    "d0_short_b": _D0,
    "b0_baseline_b": message,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)

