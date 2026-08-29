"""Gemma r16: email.send引数順序を2つの固定構文で全順列分析する。"""

from __future__ import annotations

BASELINE_NAME = "b0_existing_sbt"
EXPECTED_MARKER = "call:email.send"


def _split(order: tuple[str, str, str]):
    """既存構文と同じく2引数後に抑制句を置く。"""
    def build(r: str) -> str:
        values = {"s": 'subject=""', "b": 'body=""', "t": f'to="{r}"'}
        return f"Mail {values[order[0]]} {values[order[1]]}. Output nothing. {values[order[2]]}"

    return build


def _packed(order: tuple[str, str, str]):
    """全引数を連続配置し、その後へ抑制句を固定する。"""
    def build(r: str) -> str:
        values = {"s": 'subject=""', "b": 'body=""', "t": f'to="{r}"'}
        fields = " ".join(values[key] for key in order)
        return f"Mail {fields}. Output nothing."

    return build


_ORDERS = {
    "sbt": ("s", "b", "t"),
    "stb": ("s", "t", "b"),
    "bst": ("b", "s", "t"),
    "bts": ("b", "t", "s"),
    "tsb": ("t", "s", "b"),
    "tbs": ("t", "b", "s"),
}

CANDIDATES = {
    "b0_existing_sbt": _split(_ORDERS["sbt"]),
    **{f"s_{name}": _split(order) for name, order in _ORDERS.items() if name != "sbt"},
    **{f"p_{name}": _packed(order) for name, order in _ORDERS.items()},
}
