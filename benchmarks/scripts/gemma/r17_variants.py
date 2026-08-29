"""Gemma r17: r16で完全一致かつ13→12 input tokenになったmail引数順序だけをN=30検証する。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def b0_existing_sbt(r: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{r}"'


def a1_split_stb(r: str) -> str:
    return f'Mail subject="" to="{r}". Output nothing. body=""'


def a2_packed_sbt(r: str) -> str:
    return f'Mail subject="" body="" to="{r}". Output nothing.'


def a3_packed_bst(r: str) -> str:
    return f'Mail body="" subject="" to="{r}". Output nothing.'


def a4_split_bts(r: str) -> str:
    return f'Mail body="" to="{r}". Output nothing. subject=""'


def b5_existing_repeat(r: str) -> str:
    return b0_existing_sbt(r)


VARIANTS = {
    "b0_existing_sbt": b0_existing_sbt,
    "a1_split_stb": a1_split_stb,
    "a2_packed_sbt": a2_packed_sbt,
    "a3_packed_bst": a3_packed_bst,
    "a4_split_bts": a4_split_bts,
    "b5_existing_repeat": b5_existing_repeat,
}
