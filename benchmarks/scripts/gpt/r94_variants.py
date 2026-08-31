"""GPT r94: KV suffixを11から9へ減らしたr91安定案のpublic N=2,000 ABBA。"""

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
_SUFFIX9 = CANDIDATES["d_1_0_02"]

VARIANTS = {
    "b0_baseline_a": message,
    "suffix9_a": _SUFFIX9,
    "suffix9_b": _SUFFIX9,
    "b0_baseline_b": message,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)

