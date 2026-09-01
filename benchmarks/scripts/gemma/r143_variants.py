"""Gemma r143: recipient束縛記法と末尾suffixをN=10探索する。"""

from __future__ import annotations

RECIPIENTS = ("0", "a", "z", "by", "cc", "no", "AIM", "ARC", "CCI", "CND")

_HEADS = {
    "ordinary": 'USE ordinary double quotes for values. Mail body:"",subject:"". Conclude without text.',
    "double17": 'USE double quotes. Mail body:"",subject:"" Finish without text.',
}

_BINDINGS = {
    "colon_quote": 'to:"{r}"',
    "colon_bare": "to:{r}",
    "equal_quote": 'to="{r}"',
    "equal_bare": "to={r}",
    "space_quote": 'to "{r}"',
    "space_bare": "to {r}",
    "recipient_colon": "recipient:{r}",
    "recipient_space": "recipient {r}",
    "address_colon": "address:{r}",
    "address_space": "address {r}",
    "destination_colon": "destination:{r}",
    "for_bare": "for {r}",
    "arrow": "to->{r}",
    "gt": ">{r}",
}


def _builder(head: str, binding: str):
    template = f"{head} {binding}"
    return lambda recipient: template.format(r=recipient)


VARIANTS = {
    "control_a": _builder(_HEADS["double17"], _BINDINGS["colon_quote"]),
    **{
        f"{head_name}_{binding_name}": _builder(head, binding)
        for head_name, head in _HEADS.items()
        for binding_name, binding in _BINDINGS.items()
    },
    "control_b": _builder(_HEADS["double17"], _BINDINGS["colon_quote"]),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
