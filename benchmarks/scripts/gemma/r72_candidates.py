"""Gemma r72: body/subject明記を省いて16-token ASCII quoted callを維持する短文探索。"""

from __future__ import annotations

BASELINE_NAME = "b0_existing"
EXPECTED_MARKER = "call:email.send"

_ARGS = (
    'to:"{r}"',
    'blank,to:"{r}"',
    'empty,to:"{r}"',
    'blank fields,to:"{r}"',
    'empty fields,to:"{r}"',
    'subject/body blank,to:"{r}"',
    'body:"",to:"{r}"',
    'subject:"",to:"{r}"',
)
_DIRECTIVES = (
    "plain quoted values",
    "use plain quoted values",
    "keys bare, values quoted",
    "keep keys bare and quote only values",
    "ordinary double quotes",
)
_TAILS = (
    "Conclude without text.",
    "Conclude silently.",
    "Output nothing.",
    "No final text.",
)


def _builder(arguments: str, directive: str, tail: str):
    return lambda recipient: f"Mail {arguments.format(r=recipient)}; {directive}. {tail}"


CANDIDATES = {
    BASELINE_NAME: lambda r: f'Mail subject="" body="". Output nothing. to="{r}"',
    **{
        f"a{args_idx}_d{directive_idx}_t{tail_idx}": _builder(arguments, directive, tail)
        for args_idx, arguments in enumerate(_ARGS)
        for directive_idx, directive in enumerate(_DIRECTIVES)
        for tail_idx, tail in enumerate(_TAILS)
    },
}


def EXPECTED_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"body": "", "subject": "", "to": recipient}


def TARGET_TEXT(name: str, recipient: str) -> str:
    if name == BASELINE_NAME:
        return f'<|tool_call>call:email.send{{body:<|"|><|"|>,subject:<|"|><|"|>,to:<|"|>{recipient}<|"|>}}<tool_call|>'
    return f'<|tool_call>call:email.send{{body:"",subject:"",to:"{recipient}"}}<tool_call|>'
