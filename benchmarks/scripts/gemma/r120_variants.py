"""Gemma r120: final straight-quotes pool with two format-stable replacements."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("r106_variants.py",)

try:
    from r106_variants import RECIPIENTS as _R106_RECIPIENTS
except ModuleNotFoundError:
    from benchmarks.scripts.gemma.r106_variants import RECIPIENTS as _R106_RECIPIENTS

_REPLACEMENTS = {"ARC": "CNR", "CCI": "CNS"}
RECIPIENTS = tuple(_REPLACEMENTS.get(recipient, recipient) for recipient in _R106_RECIPIENTS)
assert len(RECIPIENTS) == len(set(RECIPIENTS)) == 2_000


def _straight_quotes(recipient: str) -> str:
    return (
        "Use straight quotes.\n"
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


VARIANTS = {"final_straight_pool": _straight_quotes}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
