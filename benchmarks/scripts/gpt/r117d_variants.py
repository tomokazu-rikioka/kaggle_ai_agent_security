"""GPT r117d: 11宛先で初回/post-toolを通過した46-token全10案を比較する。"""

from __future__ import annotations

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r111a_candidates import CANDIDATES as R111A
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r111a_candidates import CANDIDATES as R111A

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r111a_candidates.py")
RECIPIENTS = _RECIPIENTS

_MASKS = ("1fd", "1fe", "27f", "2fb", "37b", "37d", "37e", "3bb", "3be", "3f9")
VARIANTS = {f"mask_{mask}": R111A[f"mask_{mask}"] for mask in _MASKS}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
