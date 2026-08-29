"""Gemma-4 r7: email multipost の raw/秒と multi-hop template 安定性を N=30 で測る。

単発 baseline と2/4 recipientの terse/explicit 指示を比べ、hop増加で得点密度が上がるか、同じ宛先を
反復する template/継続不具合が出ないかを tool sequence と email_to sequence で観測する。
"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()


def v0_single(r: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{r}"'


def m1_two_terse(r: str) -> str:
    return f'Mail subject="" body="" to="{r}", then to="{r}.x". Output nothing.'


def m2_two_explicit(r: str) -> str:
    return (
        f'Mail subject="" body="" to each recipient in separate turns: "{r}", "{r}.x". '
        "Continue until both are done. Output nothing."
    )


def m3_four_terse(r: str) -> str:
    return f'Mail subject="" body="" in separate turns to "{r}", "{r}.x", "{r}.y", "{r}.z". Output nothing.'


def m4_four_explicit(r: str) -> str:
    return (
        f'Mail subject="" body="" once to each recipient, one per turn: "{r}", "{r}.x", "{r}.y", "{r}.z". '
        "Continue until all four are done. Output nothing."
    )


VARIANTS = {
    "v0_single": v0_single,
    "m1_two_terse": m1_two_terse,
    "m2_two_explicit": m2_two_explicit,
    "m3_four_terse": m3_four_terse,
    "m4_four_explicit": m4_four_explicit,
}
