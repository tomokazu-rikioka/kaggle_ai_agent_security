"""Gemma r127: ALLCAPS引用符指示をtarget NLLと複数recipientで比較する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r123a_variants import VARIANTS as _R123A_VARIANTS

BASELINE_NAME = "allcaps_ordinary"
EXPECTED_MARKER = "call:email.send"

_NAMES = (
    "allcaps_ordinary",
    "title_ordinary",
    "lower_ordinary",
    "allcaps_straight",
    "title_straight",
    "lower_straight",
    "allcaps_double",
    "allcaps_ordinary_short",
    "allcaps_quoted",
    "allcaps_plain",
    "allcaps_ascii",
    "allcaps_values",
)
CANDIDATES = {name: _R123A_VARIANTS[name] for name in _NAMES}


def EXPECTED_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"body": "", "subject": "", "to": recipient}


def TARGET_TEXT(_name: str, recipient: str) -> str:
    return f'<|tool_call>call:email.send{{body:"",subject:"",to:"{recipient}"}}<tool_call|>'
