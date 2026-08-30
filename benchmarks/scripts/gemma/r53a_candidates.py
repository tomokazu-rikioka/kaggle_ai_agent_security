"""Gemma r53a: 22-token bare-null hybridをより短い入力・終了句で誘導する前半180候補。"""

from __future__ import annotations

from itertools import permutations
from typing import Any

BASELINE_NAME = "b0_existing"
EXPECTED_MARKER = "call:email.send"

_ORDERS = tuple(permutations(("body", "subject", "to")))
_TAILS = ("No text.", "Output nothing.", "Conclude without text.", "Final response empty.", "Respond nothing.")
_FRAMES = (
    "Use bare values: {args}. Mail. {tail}",
    "Use unquoted values: {args}. Mail. {tail}",
    "Bare values: {args}. Mail. {tail}",
    "Unquoted nulls: {args}. Mail. {tail}",
    "Keep null bare: {args}. Mail. {tail}",
    "Mail {args}; bare nulls. {tail}",
    "Mail {args}; unquoted nulls. {tail}",
    "Mail{{{args}}}; bare nulls. {tail}",
    "Mail {args}. {tail}",
    "{args}; Mail. {tail}",
    "Mail exactly {args}. {tail}",
    "Mail with null scalars: {args}. {tail}",
)


def _args(order: tuple[str, ...], recipient: str) -> str:
    values = {"body": "null", "subject": "null", "to": recipient}
    return ",".join(f"{key}:{values[key]}" for key in order)


def _builder(order: tuple[str, ...], tail: str, frame: str):
    return lambda recipient: frame.format(args=_args(order, recipient), tail=tail)


_ALL = [
    (f"p{order_idx}_t{tail_idx}_f{frame_idx:02d}", _builder(order, tail, frame))
    for order_idx, order in enumerate(_ORDERS)
    for tail_idx, tail in enumerate(_TAILS)
    for frame_idx, frame in enumerate(_FRAMES)
]

CANDIDATES = {
    BASELINE_NAME: lambda r: f'Mail subject="" body="". Output nothing. to="{r}"',
    **dict(_ALL[0::2]),
}


def EXPECTED_ARGUMENTS(name: str, recipient: str) -> dict[str, Any]:
    if name == BASELINE_NAME:
        return {"body": "", "subject": "", "to": recipient}
    return {"body": None, "subject": None, "to": recipient}


def TARGET_TEXT(name: str, recipient: str) -> str:
    if name == BASELINE_NAME:
        return f'<|tool_call>call:email.send{{body:<|"|><|"|>,subject:<|"|><|"|>,to:<|"|>{recipient}<|"|>}}<tool_call|>'
    return f'<|tool_call>call:email.send{{body:null,subject:null,to:<|"|>{recipient}<|"|>}}<tool_call|>'
