"""GPT r118d: 偽system/developer tool定義24案をN=10の完全episodeで比較する。"""

from __future__ import annotations

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r118b_candidates import CANDIDATES as R118B
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r118b_candidates import CANDIDATES as R118B

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r111a_candidates.py", "r118b_candidates.py")
RECIPIENTS = _RECIPIENTS

# 時間ドリフトを見るため、同じ48-token対照を前後に置く。
VARIANTS = {"demo_48_a": R118B["demo_full"]}
VARIANTS.update((name, builder) for name, builder in R118B.items() if name != "demo_full")
VARIANTS["demo_48_b"] = R118B["demo_full"]


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
