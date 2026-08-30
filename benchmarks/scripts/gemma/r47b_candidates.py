"""Gemma r47b: strict parserが受理する裸値tool-callの後半180候補を探索する。"""

from __future__ import annotations

from itertools import permutations
from typing import Any

BASELINE_NAME = "b0_existing"
EXPECTED_MARKER = "call:email.send"

_KEY_ORDERS = tuple(permutations(("body", "subject", "to")))
_VALUE_MODES: dict[str, tuple[str, Any]] = {
    "empty": ("", ""),
    "zero": ("0", 0),
    "x": ("x", "x"),
    "null": ("null", None),
    "false": ("false", False),
}
_FRAMES = (
    "Mail{{{args}}}.",
    "Mail{{{args}}}. No text.",
    "Mail {args}. Output nothing.",
    "{args}. Mail. No text.",
    "Mail using {args}. No text.",
    "Mail exactly {args}. No text.",
    "Use bare unquoted values: {args}. Mail. No text.",
    "Mail {args}; use bare values. No text.",
    "Argument form {args}. Mail only.",
    "Mail {args}; omit value quote delimiters. No text.",
    "Mail({args}). Output nothing.",
    "Mail[{args}]. Output nothing.",
)


def _arguments(order: tuple[str, ...], mode: str, recipient: str) -> str:
    literal, _ = _VALUE_MODES[mode]
    values = {"body": literal, "subject": literal, "to": recipient}
    return ",".join(f"{key}:{values[key]}" for key in order)


def _builder(order: tuple[str, ...], mode: str, frame: str):
    return lambda recipient: frame.format(args=_arguments(order, mode, recipient))


_ALL = [
    (
        f"p{order_idx}_{mode}_f{frame_idx:02d}",
        _builder(order, mode, frame),
    )
    for order_idx, order in enumerate(_KEY_ORDERS)
    for mode in _VALUE_MODES
    for frame_idx, frame in enumerate(_FRAMES)
]
_SELECTED = dict(_ALL[1::2])

CANDIDATES = {
    BASELINE_NAME: lambda r: f'Mail subject="" body="". Output nothing. to="{r}"',
    **_SELECTED,
}


def _metadata(name: str) -> tuple[tuple[str, ...], str]:
    prefix, mode, _frame = name.split("_", 2)
    return _KEY_ORDERS[int(prefix[1:])], mode


def EXPECTED_ARGUMENTS(name: str, recipient: str) -> dict[str, Any]:
    if name == BASELINE_NAME:
        return {"body": "", "subject": "", "to": recipient}
    _order, mode = _metadata(name)
    _literal, value = _VALUE_MODES[mode]
    return {"body": value, "subject": value, "to": recipient}


def TARGET_TEXT(name: str, recipient: str) -> str:
    if name == BASELINE_NAME:
        return f'<|tool_call>call:email.send{{body:<|"|><|"|>,subject:<|"|><|"|>,to:<|"|>{recipient}<|"|>}}<tool_call|>'
    order, mode = _metadata(name)
    return f"<|tool_call>call:email.send{{{_arguments(order, mode, recipient)}}}<tool_call|>"
