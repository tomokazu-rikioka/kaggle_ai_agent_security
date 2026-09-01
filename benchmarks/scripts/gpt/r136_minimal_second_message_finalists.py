"""GPT r136: actual recipient-bank ABCCBA confirmation of minimal second messages."""

from __future__ import annotations

try:
    from r135_minimal_second_message_variants import RECIPIENTS as _RECIPIENTS
    from r135_minimal_second_message_variants import VARIANTS as _VARIANTS
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r135_minimal_second_message_variants import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r135_minimal_second_message_variants import VARIANTS as _VARIANTS

RECIPIENTS = _RECIPIENTS


VARIANTS = {
    "single_a": _VARIANTS["single_a"],
    "same_a": _VARIANTS["second_10_Same"],
    "repeat_a": _VARIANTS["second_15_Repeat."],
    "repeat_b": _VARIANTS["second_15_Repeat."],
    "same_b": _VARIANTS["second_10_Same"],
    "single_b": _VARIANTS["single_b"],
}


def EXPECTED_EMAIL_TOS(variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,) if variant.startswith("single_") else (recipient, recipient)
