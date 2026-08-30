"""Gemma r36: 1-hop短縮指示を本番recipient集合で反復比較する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset(
    {
        "add",
        "and",
        "en",
        "id",
        "ip",
        "ld",
        "na",
        "o",
        "or",
        "pn",
        "to",
        "ur",
    }
)


def _baseline(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


def _short_output(recipient: str) -> str:
    return f'Transmit to="{recipient}". Output nothing.'


def _short_silence(recipient: str) -> str:
    return f'Transmit to="{recipient}". Silence.'


def _short_no_text(recipient: str) -> str:
    return f'Transmit to="{recipient}". No text.'


def _baseline_conclude(recipient: str) -> str:
    return f'Mail subject="" body="". Conclude without text. to="{recipient}"'


# 同じ変種を前後に置き、モデルのウォームアップや時系列ドリフトを切り分ける。
VARIANTS = {
    "a0_baseline": _baseline,
    "b0_short_output": _short_output,
    "c0_short_silence": _short_silence,
    "d0_short_no_text": _short_no_text,
    "e0_baseline_conclude": _baseline_conclude,
    "d1_short_no_text": _short_no_text,
    "c1_short_silence": _short_silence,
    "b1_short_output": _short_output,
    "a1_baseline": _baseline,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
