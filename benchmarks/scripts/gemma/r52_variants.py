"""Gemma r52: r47で24→22 tokenへ短縮できたbare-null hybridを実時間比較する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def _baseline(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


VARIANTS = {
    "a0_baseline": _baseline,
    "p3_null_f06": lambda r: f"Use bare unquoted values: subject:null,to:{r},body:null. Mail. No text.",
    "p5_null_f06": lambda r: f"Use bare unquoted values: to:{r},subject:null,body:null. Mail. No text.",
    "p1_null_f06": lambda r: f"Use bare unquoted values: body:null,to:{r},subject:null. Mail. No text.",
    "p4_null_f06": lambda r: f"Use bare unquoted values: to:{r},body:null,subject:null. Mail. No text.",
    "a1_baseline": _baseline,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
