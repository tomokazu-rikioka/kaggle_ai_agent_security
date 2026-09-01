"""Gemma r166: 同一100 recipientで候補順序と複数prompt併用を比較する。"""

from __future__ import annotations

import random
from collections.abc import Callable

from benchmarks.scripts.gemma.r160_variants import RECIPIENTS as _R160_RECIPIENTS

_BANK = tuple(_R160_RECIPIENTS[:100])
RECIPIENTS = tuple(str(index) for index in range(len(_BANK)))


def _ordinary(recipient: str) -> str:
    return f'USE ordinary double quotes for values. Mail body:"",subject:"". Conclude without text. to:"{recipient}"'


def _double16(recipient: str) -> str:
    return f'USE double quotes. body:"",subject:"" Finish without text. to:"{recipient}"'


_random = random.Random(166)
_shuffled = list(_BANK)
_random.shuffle(_shuffled)

_ORDERS = {
    "original": _BANK,
    "reverse": tuple(reversed(_BANK)),
    "lexical": tuple(sorted(_BANK)),
    "length_lexical": tuple(sorted(_BANK, key=lambda value: (len(value), value.casefold(), value))),
    "seeded_shuffle": tuple(_shuffled),
}

_VARIANT_RECIPIENTS: dict[str, tuple[str, ...]] = {}


def _ordered_builder(name: str, order_name: str) -> Callable[[str], str]:
    order = _ORDERS[order_name]
    _VARIANT_RECIPIENTS[name] = order

    def build(index: str) -> str:
        return _double16(order[int(index)])

    return build


def _mixed_builder(name: str, selector: Callable[[int], bool]) -> Callable[[str], str]:
    _VARIANT_RECIPIENTS[name] = _BANK

    def build(index: str) -> str:
        position = int(index)
        recipient = _BANK[position]
        return (_ordinary if selector(position) else _double16)(recipient)

    return build


VARIANTS = {
    # 順序比較は同一prompt・同一recipient集合。前後controlでrun内ドリフトを見る。
    "order_original_a": _ordered_builder("order_original_a", "original"),
    "order_reverse": _ordered_builder("order_reverse", "reverse"),
    "order_lexical": _ordered_builder("order_lexical", "lexical"),
    "order_length_lexical": _ordered_builder("order_length_lexical", "length_lexical"),
    "order_seeded_shuffle": _ordered_builder("order_seeded_shuffle", "seeded_shuffle"),
    "order_original_b": _ordered_builder("order_original_b", "original"),
    # True=ordinary(22 input tokens), False=double16(16 input tokens)。
    "mix_double16_a": _mixed_builder("mix_double16_a", lambda _position: False),
    "mix_ordinary_first": _mixed_builder("mix_ordinary_first", lambda position: position < 50),
    "mix_ordinary_last": _mixed_builder("mix_ordinary_last", lambda position: position >= 50),
    "mix_blocks10": _mixed_builder("mix_blocks10", lambda position: (position // 10) % 2 == 0),
    "mix_alternating": _mixed_builder("mix_alternating", lambda position: position % 2 == 0),
    "mix_ordinary_all": _mixed_builder("mix_ordinary_all", lambda _position: True),
    "mix_double16_b": _mixed_builder("mix_double16_b", lambda _position: False),
}


def EXPECTED_EMAIL_TOS(variant: str, index: str) -> tuple[str, ...]:
    return (_VARIANT_RECIPIENTS[variant][int(index)],)

