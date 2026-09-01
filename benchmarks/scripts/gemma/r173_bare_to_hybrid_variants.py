"""Gemma r173: 空文字2引数はquotedのまま、numeric toだけbareにする混合形式。"""

from __future__ import annotations

RECIPIENTS = tuple(str(index) for index in range(10))

_TEMPLATES = {
    "control": 'USE double quotes. body:"",subject:"" Finish without text. to:"{r}"',
    "except_to": 'USE double quotes except to. body:"",subject:"" Finish without text. to:{r}',
    "bare_to": 'USE double quotes; bare to. body:"",subject:"" Finish without text. to:{r}',
    "unquoted_to": 'USE double quotes; unquoted to. body:"",subject:"" Finish without text. to:{r}',
    "quote_fields_bare_to": 'Quote body,subject; bare to. body:"",subject:"" Finish without text. to:{r}',
    "quote_fields_not_to": 'Quote body,subject, not to. body:"",subject:"" Finish without text. to:{r}',
    "double_fields_bare_to": 'Double-quote body,subject; bare to. body:"",subject:"" Finish without text. to:{r}',
    "values_except_to": 'USE double quotes for values except to. body:"",subject:"" Finish without text. to:{r}',
    "bare_to_first": 'Bare to; double quotes otherwise. body:"",subject:"" Finish without text. to:{r}',
    "to_as_number": 'USE double quotes. body:"",subject:"" Finish without text. numeric to:{r}',
    "to_as_integer": 'USE double quotes. body:"",subject:"" Finish without text. integer to:{r}',
    "to_raw": 'USE double quotes. body:"",subject:"" Finish without text. raw to:{r}',
    "to_bare": 'USE double quotes. body:"",subject:"" Finish without text. bare to:{r}',
    "compact_bare": 'USE mixed quotes. body:"",subject:"" Finish without text. to:{r}',
    "minimal_bare": 'body:"",subject:"" Finish without text. bare to:{r}',
    "minimal_numeric": 'body:"",subject:"" Finish without text. numeric to:{r}',
    "mail_bare": 'Mail body:"",subject:"" Finish without text. bare to:{r}',
    "ordinary_except_to": (
        'USE ordinary double quotes except to. Mail body:"",subject:"". '
        'Conclude without text. to:{r}'
    ),
}


def _builder(template: str):
    return lambda recipient: template.format(r=recipient)


VARIANTS = {
    "control_a": _builder(_TEMPLATES["control"]),
    **{name: _builder(template) for name, template in _TEMPLATES.items()},
    "control_b": _builder(_TEMPLATES["control"]),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)

