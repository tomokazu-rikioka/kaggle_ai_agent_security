"""GPT r117c: 11宛先で初回/post-toolを通過した47-token全7案を48-token controlと比較する。"""

from __future__ import annotations

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r111a_candidates import CANDIDATES as R111A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r111a_candidates import CANDIDATES as R111A

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r111a_candidates.py")
RECIPIENTS = _RECIPIENTS

_MASKS = ("1ff", "2ff", "37f", "3bf", "3fb", "3fd", "3fe")
VARIANTS = {f"mask_{mask}": R111A[f"mask_{mask}"] for mask in _MASKS}
VARIANTS["demo_48"] = R111A["demo_full"]


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
