"""GPT r129: compare one candidate containing one vs two stable user messages."""

from __future__ import annotations

from collections.abc import Sequence

try:
    from r128_two_call_finalists import VARIANTS as _FINALISTS
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r128_two_call_finalists import VARIANTS as _FINALISTS


def _one(recipient: str) -> str:
    return _FINALISTS["single_control"](recipient)


def _two(recipient: str) -> Sequence[str]:
    message = _one(recipient)
    return (message, message)


VARIANTS = {
    "single_control": _one,
    "two_messages": _two,
}


def EXPECTED_EMAIL_TOS(variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,) if variant == "single_control" else (recipient, recipient)
