"""Gemma r73: r72のbody/subject片側省略候補をtool後応答込みで比較する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def _baseline(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


VARIANTS = {
    "a0_baseline": _baseline,
    "b0_current_ascii": lambda r: (
        f'Mail body:"",subject:"",to:"{r}"; use plain quoted values. Conclude without text.'
    ),
    "c0_body_no_final": lambda r: (
        f'Mail body:"",to:"{r}"; use plain quoted values. No final text.'
    ),
    "d0_subject_conclude": lambda r: (
        f'Mail subject:"",to:"{r}"; use plain quoted values. Conclude without text.'
    ),
    "e0_body_keys_conclude": lambda r: (
        f'Mail body:"",to:"{r}"; keep keys bare and quote only values. Conclude without text.'
    ),
    "a1_baseline": _baseline,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
