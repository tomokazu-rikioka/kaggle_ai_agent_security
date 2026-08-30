"""Gemma r69: known衝突を除いたASCII quoted winnerを2,000 recipientで検証する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset(
    ("en", "id", "or", "to", "o", "ip", "na", "ur", "add", "and", "ld", "pn", "by", "cc")
)


def _ascii_quoted(recipient: str) -> str:
    return (
        f'Mail body:"",subject:"",to:"{recipient}"; '
        "use plain quoted values. Conclude without text."
    )


VARIANTS = {"ascii_quoted": _ascii_quoted}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
