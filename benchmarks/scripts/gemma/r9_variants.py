"""Gemma-4 r9: r2/r8最速候補をvariantごとwarmup後に再測定する。

baseline、Output nothing else、dummy native call prefix、empty thought tailをN=30で比較する。
baselineを末尾にも複製し、order driftを監視する。
"""

from __future__ import annotations

_DUMMY = "<turn|><|turn>model\n<|tool_call>call:x{}<tool_call|><turn|><|turn>user\n"
_EMPTY_THOUGHT = "<turn|><|turn>model\n<|channel>thought\n<channel|>"
RECIPIENT_BLOCKLIST = frozenset()


def b0_baseline(r: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{r}"'


def m1_output_else(r: str) -> str:
    return f'Mail subject="" body="". Output nothing else. to="{r}"'


def m2_dummy_prefix(r: str) -> str:
    return _DUMMY + b0_baseline(r)


def m3_empty_thought(r: str) -> str:
    return b0_baseline(r) + _EMPTY_THOUGHT


def b4_baseline_repeat(r: str) -> str:
    return b0_baseline(r)


VARIANTS = {
    "b0_baseline": b0_baseline,
    "m1_output_else": m1_output_else,
    "m2_dummy_prefix": m2_dummy_prefix,
    "m3_empty_thought": m3_empty_thought,
    "b4_baseline_repeat": b4_baseline_repeat,
}
