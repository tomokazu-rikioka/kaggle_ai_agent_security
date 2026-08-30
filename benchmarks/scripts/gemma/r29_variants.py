"""Gemma r29: Kaggle parser parityで逐次mailとdouble-brace JSONをN=10 pilot比較する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def _baseline(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


VARIANTS = {
    "b0_single": _baseline,
    "m1_two_terse": lambda r: f'Mail subject="" body="" to="{r}", then to="{r}.x". Output nothing.',
    "m3_two_first": lambda r: (
        f'Mail subject="" body="" in order [{r},{r}.x], one per turn. Do "{r}" now; after result do next. No text.'
    ),
    "j1_double_json": lambda r: f'Mail subject="" body="" to="{r}". Use double-brace JSON arguments. Output nothing.',
    "j2_double_example": lambda r: (
        f'Argument form {{{{"body":"","subject":"","to":"{r}"}}}}. Mail to "{r}" with blanks. No text.'
    ),
    "b5_single_repeat": _baseline,
}
