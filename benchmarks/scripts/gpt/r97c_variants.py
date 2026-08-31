"""GPT r97c: exp020 prefix固定でpost-recipient suffix 31種を完全replayする。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r97a_candidates.py")

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r97a_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r97a_candidates import CANDIDATES

RECIPIENTS = _RECIPIENTS
_EXP020 = CANDIDATES["b0_exp020"]

VARIANTS = {"exp020_a": _EXP020}
VARIANTS.update(
    (f"suffix_{index:02}", CANDIDATES[f"a_3f_0_{index:02}"])
    for index in range(1, 31)
)
VARIANTS["exp020_b"] = _EXP020


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
