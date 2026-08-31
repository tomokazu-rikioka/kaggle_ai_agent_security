"""GPT r96: r93の8-call率最良chainをpublic N=500で最終確認する。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = (
    "lb37710_baseline.py",
    "r82k_candidates.py",
    "r84d_candidates.py",
    "r93_variants.py",
)

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r93_variants import VARIANTS as _R93_VARIANTS
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r93_variants import VARIANTS as _R93_VARIANTS

RECIPIENTS = _RECIPIENTS
VARIANTS = {"same_suffix0_8": _R93_VARIANTS["same_suffix0_8"]}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,) * 8

