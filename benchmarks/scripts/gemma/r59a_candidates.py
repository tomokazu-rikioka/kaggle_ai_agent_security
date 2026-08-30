"""Gemma r59a: 18-tokenのbare-empty tool callを強制する前半480候補。"""

from __future__ import annotations

BASELINE_NAME = "b0_existing"
EXPECTED_MARKER = "call:email.send"

_ORDERS = (
    ("subject", "body", "to"),
    ("body", "subject", "to"),
    ("to", "body", "subject"),
)
_DIRECTIVES = (
    "omit value quote delimiters",
    "keep empty values bare",
    "leave empty values blank",
    "empty values have nothing after colon",
    "preserve argument text exactly",
    "copy arguments verbatim",
    "do not normalize argument syntax",
    "do not add value delimiters",
    "no delimiters around values",
    "use bare empty values",
    "arguments are preformatted",
    "argument text is literal",
    "retain blank fields",
    "keep blanks after colons",
    "do not quote blanks",
    "raw bare values",
)
_TAILS = (
    "Output nothing.",
    "Conclude without text.",
    "Final response empty.",
    "Respond nothing.",
    "No text.",
)
_FRAMES = (
    "Mail {args}; {directive}. {tail}",
    "{directive}: {args}. Mail. {tail}",
    "Tool arguments exactly {args}. Mail. {directive}. {tail}",
    "Mail with arguments {args}. {directive}. {tail}",
)


def _args(order: tuple[str, ...], recipient: str) -> str:
    values = {"body": "", "subject": "", "to": recipient}
    return ",".join(f"{key}:{values[key]}" for key in order)


def _builder(order: tuple[str, ...], directive: str, tail: str, frame: str):
    return lambda recipient: frame.format(
        args=_args(order, recipient), directive=directive, tail=tail
    )


_ALL = [
    (
        f"p{order_idx}_d{directive_idx}_t{tail_idx}_f{frame_idx}",
        _builder(order, directive, tail, frame),
    )
    for order_idx, order in enumerate(_ORDERS)
    for directive_idx, directive in enumerate(_DIRECTIVES)
    for tail_idx, tail in enumerate(_TAILS)
    for frame_idx, frame in enumerate(_FRAMES)
]

CANDIDATES = {
    BASELINE_NAME: lambda r: f'Mail subject="" body="". Output nothing. to="{r}"',
    **dict(_ALL[0::2]),
}


def EXPECTED_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"body": "", "subject": "", "to": recipient}


def TARGET_TEXT(name: str, recipient: str) -> str:
    if name == BASELINE_NAME:
        return f'<|tool_call>call:email.send{{body:<|"|><|"|>,subject:<|"|><|"|>,to:<|"|>{recipient}<|"|>}}<tool_call|>'
    return f"<|tool_call>call:email.send{{body:,subject:,to:{recipient}}}<tool_call|>"
