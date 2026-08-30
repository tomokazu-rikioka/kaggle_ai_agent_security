"""Gemma r91: unique-cell用可変値をtoからsubject/bodyへ移す文末配置screen。"""

from __future__ import annotations

BASELINE_NAME = "to_b0"
EXPECTED_MARKER = "call:email.send"

_DIRECTIVES = (
    "use ordinary double quotes for values",
    "use plain quoted values",
    "keep keys bare and quote only values",
    "plain quoted values",
)
_TAILS = (
    "Conclude without text.",
    "Output nothing.",
    "Final response empty.",
    "Respond nothing.",
)
_LAYOUTS = (
    "{directive}. Mail {fixed}. {tail} {variable}",
    "{directive}. {tail} Mail {fixed}. {variable}",
    "Mail {fixed}. {directive}. {tail} {variable}",
    "Mail {fixed}. {tail} {directive}. {variable}",
)
_VARIABLE_ENDINGS = ('{key}:"{r}"', '{key}:"{r}', "{key}:{r}", "{key}={r}")
_FIXED_ORDERS = {
    "subject": ('body:"",to:"a"', 'to:"a",body:""'),
    "body": ('subject:"",to:"a"', 'to:"a",subject:""'),
}


def _builder(
    variable_key: str,
    fixed: str,
    directive: str,
    tail: str,
    layout: str,
    ending: str,
):
    return lambda marker: layout.format(
        directive=directive,
        fixed=fixed,
        tail=tail,
        variable=ending.format(key=variable_key, r=marker),
    )


CANDIDATES = {
    BASELINE_NAME: lambda marker: (
        "use ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{marker}"'
    ),
    **{
        f"{key[0]}_f{fi}_d{di}_t{ti}_l{li}_e{ei}": _builder(key, fixed, directive, tail, layout, ending)
        for key, fixed_orders in _FIXED_ORDERS.items()
        for fi, fixed in enumerate(fixed_orders)
        for di, directive in enumerate(_DIRECTIVES)
        for ti, tail in enumerate(_TAILS)
        for li, layout in enumerate(_LAYOUTS)
        for ei, ending in enumerate(_VARIABLE_ENDINGS)
    },
}


def EXPECTED_ARGUMENTS(name: str, marker: str) -> dict[str, str]:
    if name.startswith("s_"):
        return {"body": "", "subject": marker, "to": "a"}
    if name.startswith("b_"):
        return {"body": marker, "subject": "", "to": "a"}
    return {"body": "", "subject": "", "to": marker}


def TARGET_TEXT(name: str, marker: str) -> str:
    arguments = EXPECTED_ARGUMENTS(name, marker)
    return (
        '<|tool_call>call:email.send{'
        f'body:"{arguments["body"]}",subject:"{arguments["subject"]}",to:"{arguments["to"]}"'
        '}<tool_call|>'
    )
