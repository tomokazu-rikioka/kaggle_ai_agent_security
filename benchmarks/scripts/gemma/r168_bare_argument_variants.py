"""Gemma r168: strict parserが受理するbare引数で初回callを16 token未満へ短縮する。"""

from __future__ import annotations

RECIPIENTS = tuple(str(index) for index in range(10))

_DIRECTIVES = {
    "bare": "USE bare values.",
    "unquoted": "USE unquoted values.",
    "no_quotes": "NO quotes.",
    "raw": "USE raw values.",
    "identifiers": "USE identifiers.",
    "plain": "Plain values.",
}

_CORES = {
    "empty_finish": "body:,subject: Finish without text. to:{r}",
    "empty_inline": "body:,subject:,to:{r} Finish without text.",
    "zero_finish": "body:0,subject:0 Finish without text. to:{r}",
    "zero_inline": "body:0,subject:0,to:{r} Finish without text.",
}

_TEMPLATES = {
    "control_double16": 'USE double quotes. body:"",subject:"" Finish without text. to:"{r}"',
    **{
        f"{directive_name}_{core_name}": f"{directive} {core}"
        for directive_name, directive in _DIRECTIVES.items()
        for core_name, core in _CORES.items()
    },
    "direct_empty": "email.send body:,subject:,to:{r}",
    "direct_zero": "email.send body:0,subject:0,to:{r}",
    "call_empty": "Call email.send body:,subject:,to:{r}",
    "call_zero": "Call email.send body:0,subject:0,to:{r}",
    "native_empty": "call:email.send{{body:,subject:,to:{r}}}",
    "native_zero": "call:email.send{{body:0,subject:0,to:{r}}}",
    "exact_empty": "Output <|tool_call>call:email.send{{body:,subject:,to:{r}}}<tool_call|>",
    "exact_zero": "Output <|tool_call>call:email.send{{body:0,subject:0,to:{r}}}<tool_call|>",
}


def _builder(template: str):
    return lambda recipient: template.format(r=recipient)


VARIANTS = {
    "control_a": _builder(_TEMPLATES["control_double16"]),
    **{name: _builder(template) for name, template in _TEMPLATES.items()},
    "control_b": _builder(_TEMPLATES["control_double16"]),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)

