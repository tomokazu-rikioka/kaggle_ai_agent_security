"""GPT r119a: 47/46-token最終2案を48-token前後controlでN=1,500比較する。"""

from __future__ import annotations

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r111a_candidates import CANDIDATES as R111A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r111a_candidates import CANDIDATES as R111A

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r111a_candidates.py")
RECIPIENTS = _RECIPIENTS

# A-B-C-C-B-A配置で線形な時間ドリフトを相殺する。
VARIANTS = {
    "demo_48_a": R111A["demo_full"],
    "mask_2ff_a": R111A["mask_2ff"],
    "mask_2fb_a": R111A["mask_2fb"],
    "mask_2fb_b": R111A["mask_2fb"],
    "mask_2ff_b": R111A["mask_2ff"],
    "demo_48_b": R111A["demo_full"],
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
