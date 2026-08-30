"""Gemma r93y: 15-token記号4値をrecipient後置directiveでliteralとして再検証する。"""

from __future__ import annotations

RECIPIENTS = (")", ";", "))", ");")


def _recipient_before_directive(recipient: str) -> str:
    return (
        f'Mail body:"",subject:"",to:"{recipient}"; '
        "use plain quoted values. Conclude without text."
    )


VARIANTS = {"extended_15_token_literal": _recipient_before_directive}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
