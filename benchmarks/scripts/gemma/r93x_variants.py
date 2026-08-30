"""Gemma r93x: extended語彙で静的15-tokenとなった4 recipientを実生成検証する。"""

from __future__ import annotations

RECIPIENTS = (")", ";", "))", ");")


def _recipient_last(recipient: str) -> str:
    return (
        "use ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


VARIANTS = {"extended_15_token": _recipient_last}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
