"""GPT r134: actual recipient-bank ABCCBA comparison of second-message finalists."""

from __future__ import annotations

try:
    from r131_second_message_variants import RECIPIENTS as _RECIPIENTS
    from r131_second_message_variants import VARIANTS as _VARIANTS
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r131_second_message_variants import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r131_second_message_variants import VARIANTS as _VARIANTS

RECIPIENTS = _RECIPIENTS


VARIANTS = {
    "single_a": _VARIANTS["single_a"],
    "repeat_head_a": _VARIANTS["two_repeat_head"],
    "head_fields_a": _VARIANTS["two_head_fields"],
    "head_fields_b": _VARIANTS["two_head_fields"],
    "repeat_head_b": _VARIANTS["two_repeat_head"],
    "single_b": _VARIANTS["single_b"],
}


def EXPECTED_EMAIL_TOS(variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,) if variant.startswith("single_") else (recipient, recipient)
