"""GPT r127: high-N calibration of the closest r120 two-call wording."""

from __future__ import annotations

try:
    from r120_two_call_variants import VARIANTS as _R120_VARIANTS
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r120_two_call_variants import VARIANTS as _R120_VARIANTS

VARIANTS = {
    "single_control": _R120_VARIANTS["single_a"],
    "two_actions": _R120_VARIANTS["two_actions"],
    "two_after_result": _R120_VARIANTS["two_after_result"],
}


def EXPECTED_EMAIL_TOS(variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,) if variant == "single_control" else (recipient, recipient)
