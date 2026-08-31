"""GPT r89: r87mの完全な2-call継続候補を実際の8-hopで比較する。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r83m_variants.py", "r87m_variants.py")

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from lb37710_baseline import message
    from r87m_variants import VARIANTS as _R87_VARIANTS
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r87m_variants import VARIANTS as _R87_VARIANTS

RECIPIENTS = _RECIPIENTS

VARIANTS = {
    "b0_single_baseline": message,
    "z1_exact18": _R87_VARIANTS["z_1_2_01"],
    "z2_exact18": _R87_VARIANTS["z_2_2_01"],
}


def EXPECTED_EMAIL_TOS(variant: str, recipient: str) -> tuple[str, ...]:
    count = 1 if variant == "b0_single_baseline" else 8
    return (recipient,) * count
