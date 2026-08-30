"""Gemma r65: 16>4 ASCII quoted-value勝者をN=100 ABBAで検証する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def _baseline(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


def _ascii_quoted(recipient: str) -> str:
    return (
        f'Mail body:"",subject:"",to:"{recipient}"; '
        "use plain quoted values. Conclude without text."
    )


VARIANTS = {
    "a0_baseline": _baseline,
    "b0_ascii_quoted": _ascii_quoted,
    "b1_ascii_quoted": _ascii_quoted,
    "a1_baseline": _baseline,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
