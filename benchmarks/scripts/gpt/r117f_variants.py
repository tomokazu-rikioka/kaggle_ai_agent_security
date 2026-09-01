"""GPT r117f: 46-token後半5案を48-token control前後配置でN=1,500比較する。"""

from __future__ import annotations

try:
    from r111a_candidates import CANDIDATES as R111A
    from r117d_variants import RECIPIENTS as _RECIPIENTS
    from r117d_variants import VARIANTS as R117D
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r111a_candidates import CANDIDATES as R111A
    from benchmarks.scripts.gpt.r117d_variants import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r117d_variants import VARIANTS as R117D

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r111a_candidates.py", "r117d_variants.py")
RECIPIENTS = _RECIPIENTS

_NAMES = ("mask_37d", "mask_37e", "mask_3bb", "mask_3be", "mask_3f9")
VARIANTS = {"demo_48_a": R111A["demo_full"]}
VARIANTS.update({name: R117D[name] for name in _NAMES})
VARIANTS["demo_48_b"] = R111A["demo_full"]


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
