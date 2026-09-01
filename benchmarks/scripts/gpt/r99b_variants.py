"""GPT r99b: r99aでcanonical 18-token callが8/8だった2案のtool後を確認する。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("r99a_candidates.py",)

try:
    from r99a_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r99a_candidates import CANDIDATES


_NAMES = (
    "q_0_24_2_0",
    "q_0_24_0_1",
)

VARIANTS = {"b0_suffix0": CANDIDATES["b0_r97e_suffix0"]}
VARIANTS.update((name, CANDIDATES[name]) for name in _NAMES)


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}
