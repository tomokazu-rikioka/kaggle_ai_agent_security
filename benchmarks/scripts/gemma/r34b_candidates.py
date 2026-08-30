"""Gemma r34b: tool実行後の終了応答を短くする指示の組合せ探索（後半）。"""

from __future__ import annotations

BASELINE_NAME = "b0_existing"
EXPECTED_MARKER = "call:email.send"

_FRAMES = (
    'Mail subject="" body="". {tail} to="{r}"',
    'Mail subject="" body="" to="{r}". {tail}',
    'Mail to="{r}" subject="" body="". {tail}',
)
_TAILS = (
    "Output nothing.",
    "Output nothing else.",
    "No text.",
    "No response.",
    "Respond nothing.",
    "Respond with nothing.",
    "Remain silent.",
    "Stay silent.",
    "Silence.",
    "Silent.",
    "Do not reply.",
    "No reply.",
    "Do not answer.",
    "No answer.",
    "No acknowledgement.",
    "Do not acknowledge.",
    "End.",
    "Then end.",
    "Stop.",
    "Then stop.",
    "Finish.",
    "Then finish.",
    "Afterward, stop.",
    "Stop after tool use.",
    "After the tool, stop.",
    "Call once, then stop.",
    "One tool only.",
    "Use one tool only.",
    "No follow-up.",
    "Do not follow up.",
    "End immediately after.",
    "Terminate afterward.",
    "Conclude without text.",
    "Suppress confirmation.",
    "No confirmation.",
    "No completion text.",
    "Do not report completion.",
    "Return nothing.",
    "Produce no text.",
    "Final response empty.",
    "Final answer empty.",
    "No final response.",
    "No prose.",
    "Tool only.",
    "Only the tool.",
    "Just use the tool.",
    "Execute only.",
    "Act only.",
    "Nothing else.",
    "No output.",
    "Output blank.",
    "After result, end.",
    "Upon result, end.",
    "After success, end.",
    "Do not summarize.",
    "Skip summary.",
    "No summary.",
    "No status.",
    "Skip status.",
    "No commentary.",
    "No explanation.",
)


def _builder(frame: str, tail: str):
    return lambda recipient: frame.format(r=recipient, tail=tail)


_ALL = [
    (f"f{frame_idx}_t{tail_idx:02d}", _builder(frame, tail))
    for frame_idx, frame in enumerate(_FRAMES)
    for tail_idx, tail in enumerate(_TAILS)
]

CANDIDATES = {
    "b0_existing": lambda r: f'Mail subject="" body="". Output nothing. to="{r}"',
    **dict(_ALL[1::2]),
}

