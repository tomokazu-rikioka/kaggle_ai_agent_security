"""Gemma r110: test parser-valid single-quoted argument values."""

from __future__ import annotations

BASELINE_NAME = "b0_double_quote"
EXPECTED_MARKER = "call:email.send"

_DIRECTIVES = (
    "use ordinary single quotes for values",
    "use single-quoted values",
    "use plain single quotes for values",
    "keep keys bare and single-quote only values",
    "single quotes around values",
    "quote values with apostrophes",
)
_FIELDS = (
    "body:'',subject:''",
    "subject:'',body:''",
    'body:"",subject:""',
    'subject:"",body:""',
)
_STEMS = (
    "{directive}. Mail {fields}. Conclude without text. to:'{r}'",
    "Mail {fields}. {directive}. Conclude without text. to:'{r}'",
    "Mail {fields}. Conclude without text. {directive}. to:'{r}'",
)


def _builder(directive: str, fields: str, stem: str):
    return lambda recipient: stem.format(directive=directive, fields=fields, r=recipient)


CANDIDATES = {
    BASELINE_NAME: lambda recipient: (
        "use ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    ),
    **{
        f"d{di}_f{fi}_s{si}": _builder(directive, fields, stem)
        for di, directive in enumerate(_DIRECTIVES)
        for fi, fields in enumerate(_FIELDS)
        for si, stem in enumerate(_STEMS)
    },
}


def EXPECTED_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"body": "", "subject": "", "to": recipient}


def TARGET_TEXT(name: str, recipient: str) -> str:
    if name == BASELINE_NAME:
        return f'<|tool_call>call:email.send{{body:"",subject:"",to:"{recipient}"}}<tool_call|>'
    return f"<|tool_call>call:email.send{{body:'',subject:'',to:'{recipient}'}}<tool_call|>"
