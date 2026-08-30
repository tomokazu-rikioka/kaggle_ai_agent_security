"""Gemma r74: 入力を19→17 tokenへ縮めたsubject-only候補をN=100 ABBAで検証する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def _baseline(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


def _current(recipient: str) -> str:
    return (
        f'Mail body:"",subject:"",to:"{recipient}"; '
        "use plain quoted values. Conclude without text."
    )


def _subject_only(recipient: str) -> str:
    return (
        f'Mail subject:"",to:"{recipient}"; '
        "use plain quoted values. Conclude without text."
    )


VARIANTS = {
    "a0_baseline": _baseline,
    "b0_current": _current,
    "c0_subject_only": _subject_only,
    "c1_subject_only": _subject_only,
    "b1_current": _current,
    "a1_baseline": _baseline,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
