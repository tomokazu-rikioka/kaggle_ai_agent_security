"""Gemma r122: ABBA replay of newline versus single-space separation."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("r117_variants.py",)

try:
    from r117_variants import RECIPIENTS as _R117_RECIPIENTS
except ModuleNotFoundError:
    from benchmarks.scripts.gemma.r117_variants import RECIPIENTS as _R117_RECIPIENTS

RECIPIENTS = _R117_RECIPIENTS


def _message(recipient: str, separator: str) -> str:
    return (
        f"Use straight quotes.{separator}"
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


VARIANTS = {
    "newline_a": lambda recipient: _message(recipient, "\n"),
    "space_a": lambda recipient: _message(recipient, " "),
    "space_b": lambda recipient: _message(recipient, " "),
    "newline_b": lambda recipient: _message(recipient, "\n"),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
