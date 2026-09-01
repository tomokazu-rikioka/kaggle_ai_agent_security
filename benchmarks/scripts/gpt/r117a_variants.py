"""GPT r117a: r003 suffix-0の固定例示値8種をN=1,500で比較する。"""

from __future__ import annotations

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r97b_candidates import CANDIDATES as R97B
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r97b_candidates import CANDIDATES as R97B

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r97b_candidates.py")
RECIPIENTS = _RECIPIENTS

_PLACEHOLDER_NAMES = ("x", "question", "underscore", "zero", "a", "z", "upper_x", "dest")

VARIANTS = {
    f"suffix_{label}": R97B[f"b_3_{index}_0_2_0_0"]
    for index, label in enumerate(_PLACEHOLDER_NAMES)
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
