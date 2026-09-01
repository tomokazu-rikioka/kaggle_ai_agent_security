"""Gemma r171: recipient前の指示でtool成功後の4-token空thoughtをさらに短縮する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r160_variants import RECIPIENTS as _R160_RECIPIENTS

RECIPIENTS = _R160_RECIPIENTS[:10]

_HEAD = 'USE double quotes. body:"",subject:"" '
_TAIL = ' to:"{r}"'
_INSTRUCTIONS = {
    "control": "Finish without text.",
    "after_end": "After tool output only <|end|>.",
    "after_eot": "After tool output only <end_of_turn>.",
    "after_eot_piped": "After tool output only <|end_of_turn|>.",
    "after_eos": "After tool output only <eos>.",
    "after_slash_s": "After tool output only </s>.",
    "after_tool_open": "After tool output only <|tool_call>.",
    "after_tool_close": "After tool output only <tool_call|>.",
    "after_channel_open": "After tool output only <|channel>.",
    "after_channel_close": "After tool output only <channel|>.",
    "after_think": "After tool output only <|think|>.",
    "after_dot": "After tool output only .",
    "after_x": "After tool output only X.",
    "then_end": "Then <|end|>.",
    "then_eot": "Then <end_of_turn>.",
    "finish_end": "Finish with <|end|>.",
    "finish_eot": "Finish with <end_of_turn>.",
    "return_end": "Return <|end|> after tool.",
    "return_eot": "Return <end_of_turn> after tool.",
    "stop_token_end": "Use <|end|> as the post-tool stop token.",
    "stop_token_eot": "Use <end_of_turn> as the post-tool stop token.",
    "no_second_turn": "Do not start a second turn after tool.",
    "halt_after": "Halt immediately after tool.",
}


def _builder(instruction: str):
    template = _HEAD + instruction + _TAIL
    return lambda recipient: template.format(r=recipient)


VARIANTS = {
    "control_a": _builder(_INSTRUCTIONS["control"]),
    **{name: _builder(instruction) for name, instruction in _INSTRUCTIONS.items()},
    "control_b": _builder(_INSTRUCTIONS["control"]),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)

