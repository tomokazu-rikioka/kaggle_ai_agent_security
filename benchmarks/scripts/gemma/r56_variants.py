"""Gemma r56: r49で24 stress recipient完全一致した9短文をN=30実時間比較する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def _baseline(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


VARIANTS = {
    "a0_baseline": _baseline,
    "h09_f0_t04": lambda r: f'Write to="{r}". Respond with nothing.',
    "h07_f0_t04": lambda r: f'Contact to="{r}". Respond with nothing.',
    "h06_f0_t04": lambda r: f'Message to="{r}". Respond with nothing.',
    "h46_f0_t04": lambda r: f'Compose to="{r}". Respond with nothing.',
    "h07_f1_t03": lambda r: f'Contact: to="{r}". Respond nothing.',
    "h22_f0_t18": lambda r: f'Tell to="{r}". Final response empty.',
    "h07_f1_t04": lambda r: f'Contact: to="{r}". Respond with nothing.',
    "h46_f1_t18": lambda r: f'Compose: to="{r}". Final response empty.',
    "h07_f1_t18": lambda r: f'Contact: to="{r}". Final response empty.',
    "a1_baseline": _baseline,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
