"""GPT r86m: recipient cross-check of r83's nine exact 18-token repeats."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r83m_variants.py")

try:
    from r83m_variants import VARIANTS as _ALL
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r83m_variants import VARIANTS as _ALL

_NAMES = (
    "m_0_07_1_1_2",
    "m_1_01_2_1_2",
    "m_1_02_2_1_2",
    "m_1_03_2_1_2",
    "m_2_01_2_1_2",
    "m_2_02_2_1_2",
    "m_2_03_2_1_2",
    "m_2_07_2_1_2",
    "m_2_09_2_1_2",
)
VARIANTS = {name: _ALL[name] for name in _NAMES}


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}


def EXPECTED_NEXT_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}

