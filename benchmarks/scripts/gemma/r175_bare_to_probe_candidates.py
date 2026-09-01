"""Gemma r175: quoted空文字とbare numeric toを両立する指示文を系統探索する。"""

from __future__ import annotations

from typing import Any

BASELINE_NAME = "control_quoted"
EXPECTED_MARKER = "call:email.send"

_DIRECTIVES = (
    "Quote strings; leave numeric to unquoted",
    "Double-quote strings; leave to unquoted",
    "Use JSON scalar syntax: strings quoted, numbers bare",
    "Use quoted body and subject but bare numeric to",
    "Use double quotes only for body and subject",
    "Do not quote the numeric to value",
    "Keep to as a bare integer",
    "Treat to as an unquoted number",
    "Render body and subject as strings, to as integer",
    "Mixed values: body and subject strings, to integer",
    "Exact types: body string, subject string, to integer",
    "body and subject are quoted strings; to is a bare number",
)
_FRAMES = (
    '{directive}. body:"",subject:"" Finish without text. to:{r}',
    '{directive}. Mail body:"",subject:"". Finish without text. to:{r}',
    '{directive}: body:"",subject:"". Conclude without text. to:{r}',
)


def _builder(template: str, directive: str):
    return lambda recipient: template.format(directive=directive, r=recipient)


CANDIDATES = {
    BASELINE_NAME: lambda recipient: (
        f'USE double quotes. body:"",subject:"" Finish without text. to:"{recipient}"'
    ),
    **{
        f"d{directive_index:02d}_f{frame_index}": _builder(frame, directive)
        for directive_index, directive in enumerate(_DIRECTIVES)
        for frame_index, frame in enumerate(_FRAMES)
    },
}


def EXPECTED_ARGUMENTS(name: str, recipient: str) -> dict[str, Any]:
    to: str | int = recipient if name == BASELINE_NAME else int(recipient)
    return {"body": "", "subject": "", "to": to}


def TARGET_TEXT(name: str, recipient: str) -> str:
    to = f'"{recipient}"' if name == BASELINE_NAME else recipient
    return f'<|tool_call>call:email.send{{body:"",subject:"",to:{to}}}<tool_call|>'

