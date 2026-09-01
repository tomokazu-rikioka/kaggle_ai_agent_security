"""GPT r132: current 47-token one-hop versus two identical messages, ABBA."""

from __future__ import annotations

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from r111a_candidates import CANDIDATES as _CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r111a_candidates import CANDIDATES as _CANDIDATES

RECIPIENTS = _RECIPIENTS


def _one(recipient: str) -> str:
    return _CANDIDATES["mask_2ff"](recipient)


def _two(recipient: str) -> tuple[str, str]:
    message = _one(recipient)
    return message, message


VARIANTS = {
    "single_a": _one,
    "two_messages_a": _two,
    "two_messages_b": _two,
    "single_b": _one,
}


def EXPECTED_EMAIL_TOS(variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,) if variant.startswith("single_") else (recipient, recipient)
