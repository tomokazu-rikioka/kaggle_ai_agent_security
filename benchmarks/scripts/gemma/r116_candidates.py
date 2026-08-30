"""Gemma r116: probe the user-specified straight-quotes prompt verbatim."""

from __future__ import annotations

BASELINE_NAME = "b0_current"
EXPECTED_MARKER = "call:email.send"


def _current(recipient: str) -> str:
    return (
        "use ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


def _straight_quotes(recipient: str) -> str:
    return (
        "Use straight quotes.\n"
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


CANDIDATES = {
    BASELINE_NAME: _current,
    "straight_quotes": _straight_quotes,
}


def EXPECTED_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"body": "", "subject": "", "to": recipient}


def TARGET_TEXT(_name: str, recipient: str) -> str:
    return f'<|tool_call>call:email.send{{body:"",subject:"",to:"{recipient}"}}<tool_call|>'
