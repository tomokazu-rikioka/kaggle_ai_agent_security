"""Gemma r130: 19-token straight形式を起点に終了句を総当たりする。"""

from __future__ import annotations

RECIPIENTS = ("0", "a", "z", "by", "cc", "no", "AIM", "ARC", "CCI", "CND")

_TAILS = {
    "conclude_without_text": "Conclude without text.",
    "conclude_no_text": "Conclude no text.",
    "conclude_empty": "Conclude empty.",
    "conclude_silently": "Conclude silently.",
    "finish_without_text": "Finish without text.",
    "finish_no_text": "Finish no text.",
    "finish_silently": "Finish silently.",
    "finish": "Finish.",
    "end_without_text": "End without text.",
    "end_no_text": "End no text.",
    "end_silently": "End silently.",
    "end": "End.",
    "stop_after_tool": "Stop after tool.",
    "after_tool_stop": "After tool, stop.",
    "then_stop": "Then stop.",
    "stop": "Stop.",
    "tool_only": "Tool only.",
    "tool_call_only": "Tool call only.",
    "call_only": "Call only.",
    "only_call": "Only call.",
    "output_nothing": "Output nothing.",
    "output_no_text": "Output no text.",
    "no_output": "No output.",
    "no_text": "No text.",
    "no_final_text": "No final text.",
    "no_answer": "No answer.",
    "no_response": "No response.",
    "no_reply": "No reply.",
    "do_not_answer": "Do not answer.",
    "do_not_respond": "Do not respond.",
    "do_not_reply": "Do not reply.",
    "dont_reply": "Don't reply.",
    "respond_nothing": "Respond nothing.",
    "reply_nothing": "Reply nothing.",
    "reply_empty": "Reply empty.",
    "final_empty": "Final empty.",
    "final_blank": "Final blank.",
    "silent": "Silent.",
    "silence": "Silence.",
    "done": "Done.",
    "allcaps_conclude": "CONCLUDE WITHOUT TEXT.",
    "allcaps_stop": "STOP.",
    "allcaps_tool_only": "TOOL ONLY.",
    "allcaps_no_reply": "NO REPLY.",
    "empty": "",
}


def _message(recipient: str, tail: str) -> str:
    separator = " " if tail else ""
    return f'USE straight quotes. Mail body:"",subject:"". {tail}{separator}to:"{recipient}"'


def _builder(tail: str):
    return lambda recipient: _message(recipient, tail)


VARIANTS = {
    "control_a": _builder(_TAILS["conclude_without_text"]),
    **{name: _builder(tail) for name, tail in _TAILS.items()},
    "control_b": _builder(_TAILS["conclude_without_text"]),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
