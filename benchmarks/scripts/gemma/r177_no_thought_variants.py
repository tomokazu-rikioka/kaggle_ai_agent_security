"""Gemma r177: 自然言語でpost-tool thoughtを明示的に禁止する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r160_variants import RECIPIENTS as _R160_RECIPIENTS

RECIPIENTS = _R160_RECIPIENTS[:10]

_HEAD = 'USE double quotes. body:"",subject:"" '
_TAIL = ' to:"{r}"'
_INSTRUCTIONS = {
    "no_thought": "No thought.",
    "no_thinking": "No thinking.",
    "no_reasoning": "No reasoning.",
    "skip_thought": "Skip thought.",
    "omit_thought": "Omit thought.",
    "do_not_think_after": "Do not think after tool.",
    "do_not_output_thought": "Do not output thought after tool.",
    "do_not_generate_thought": "Do not generate a thought after tool.",
    "thought_unneeded": "Thought is unnecessary after tool.",
    "thought_not_required": "Thought is not required after tool.",
    "tool_call_final": "Tool call is final.",
    "tool_call_must_final": "Tool call must be the final output.",
    "end_response_after": "End response immediately after tool call.",
    "end_after_calling": "End immediately after calling the tool.",
    "stop_generation_after": "Stop generation immediately after tool call.",
    "after_stop_generation": "After tool call, stop generation.",
    "after_no_tokens": "After tool call, output no tokens.",
    "after_emit_eos": "After tool call, emit EOS.",
    "emit_eos_after": "Emit EOS immediately after tool call.",
    "call_then_eos": "Tool call then EOS.",
    "no_post_response": "Use no post-tool response.",
    "skip_post_response": "Skip post-tool response.",
    "no_assistant_after_result": "No assistant response after tool result.",
    "ignore_result_terminate": "Ignore tool result and terminate.",
    "return_nothing_after": "Return nothing after tool.",
    "after_result_nothing": "After tool result, return nothing.",
}


def _builder(instruction: str, *, append_to_control: bool):
    prefix = "Finish without text. " if append_to_control else ""
    template = _HEAD + prefix + instruction + _TAIL
    return lambda recipient: template.format(r=recipient)


VARIANTS = {
    "control_a": _builder("Finish without text.", append_to_control=False),
    **{
        f"replace_{name}": _builder(instruction, append_to_control=False)
        for name, instruction in _INSTRUCTIONS.items()
    },
    **{
        f"append_{name}": _builder(instruction, append_to_control=True)
        for name, instruction in _INSTRUCTIONS.items()
    },
    "control_b": _builder("Finish without text.", append_to_control=False),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
