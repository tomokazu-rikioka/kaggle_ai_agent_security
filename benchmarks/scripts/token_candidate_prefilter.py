"""Exhaustively inspect a vocabulary and select diverse stop-related trigger pieces.

Every token is decoded and assigned surface-distance/category features.  The
expensive full-prompt forward pass is then reserved for a bounded union of
special tokens, stop-semantic neighbors, punctuation, high baseline logits,
frequent IDs, and a stratified sample of the remaining vocabulary.
"""

from __future__ import annotations

import heapq
import unicodedata
from typing import Any

import numpy as np

_ANCHORS = (
    "eos",
    "eot",
    "end",
    "endofturn",
    "final",
    "finish",
    "finished",
    "return",
    "stop",
    "terminate",
    "done",
    "empty",
    "silent",
    "toolresponse",
    "toolresult",
    "toolcall",
)


def _normalize(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _bigrams(value: str) -> set[str]:
    if len(value) < 2:
        return {value} if value else set()
    return {value[index : index + 2] for index in range(len(value) - 1)}


_ANCHOR_BIGRAMS = tuple(_bigrams(anchor) for anchor in _ANCHORS)


def _surface_distance(value: str) -> float:
    normalized = _normalize(value)
    if not normalized:
        return 10.0
    if any(anchor in normalized or normalized in anchor for anchor in _ANCHORS):
        return 0.0
    grams = _bigrams(normalized)
    best = 0.0
    for anchor, anchor_grams in zip(_ANCHORS, _ANCHOR_BIGRAMS, strict=True):
        union = grams | anchor_grams
        overlap = len(grams & anchor_grams) / len(union) if union else 0.0
        length = min(len(normalized), len(anchor)) / max(len(normalized), len(anchor))
        best = max(best, overlap * 0.8 + length * 0.2)
    return 1.0 - best


def _piece(llm: Any, token_id: int) -> str | None:
    try:
        value = llm.detokenize([token_id], special=True).decode("utf-8")
    except (UnicodeDecodeError, ValueError, RuntimeError):
        return None
    if not value or len(value) > 32 or any(character in "\r\n\x00" for character in value):
        return None
    if any(not character.isprintable() for character in value):
        return None
    lowered = value.casefold().replace(" ", "")
    if any(blocked in lowered for blocked in ("email", "send", "upload")):
        return None
    return value


def _is_symbol(value: str) -> bool:
    stripped = value.strip()
    return bool(stripped) and all(
        unicodedata.category(character)[0] in {"P", "S"} for character in stripped
    )


def select(
    llm: Any,
    *,
    limit: int,
    baseline_logits: np.ndarray | None = None,
) -> tuple[list[tuple[int, str]], dict[str, Any]]:
    """Return selected ``(token_id, decoded_piece)`` rows and selection diagnostics."""
    rows: list[tuple[int, str]] = []
    semantic_heap: list[tuple[float, int, str]] = []
    special: list[tuple[int, str]] = []
    symbols: list[tuple[int, str]] = []
    frequent: list[tuple[int, str]] = []
    seen_piece: set[str] = set()
    decoded = 0
    for token_id in range(llm.n_vocab()):
        value = _piece(llm, token_id)
        if value is None or value in seen_piece:
            continue
        seen_piece.add(value)
        decoded += 1
        row = (token_id, value)
        if "<" in value and ">" in value:
            special.append(row)
        if _is_symbol(value):
            symbols.append(row)
        if token_id < 50_000:
            frequent.append(row)
        distance = _surface_distance(value)
        item = (-distance, token_id, value)
        if len(semantic_heap) < 4_000:
            heapq.heappush(semantic_heap, item)
        elif item > semantic_heap[0]:
            heapq.heapreplace(semantic_heap, item)

    semantic = [(token_id, value) for _, token_id, value in sorted(semantic_heap, reverse=True)]
    logit_rows: list[tuple[int, str]] = []
    if baseline_logits is not None and len(baseline_logits) == llm.n_vocab():
        count = min(2_000, len(baseline_logits))
        top_ids = np.argpartition(baseline_logits, -count)[-count:]
        for token_id in top_ids[np.argsort(baseline_logits[top_ids])[::-1]]:
            value = _piece(llm, int(token_id))
            if value is not None:
                logit_rows.append((int(token_id), value))

    selected: list[tuple[int, str]] = []
    used_ids: set[int] = set()
    used_values: set[str] = set()

    def add(source: list[tuple[int, str]], source_limit: int | None = None) -> None:
        added = 0
        for token_id, value in source:
            if len(selected) >= limit:
                return
            if token_id in used_ids or value in used_values:
                continue
            used_ids.add(token_id)
            used_values.add(value)
            selected.append((token_id, value))
            added += 1
            if source_limit is not None and added >= source_limit:
                return

    add(special)
    add(semantic, 4_000)
    add(symbols, 3_000)
    add(logit_rows, 2_000)
    add(frequent)
    if len(selected) < limit:
        # Deterministic vocabulary-wide coverage after the targeted strata.
        remaining = max(limit - len(selected), 1)
        stride = max(llm.n_vocab() // remaining, 1)
        stratified = [
            (token_id, value)
            for token_id in range(0, llm.n_vocab(), stride)
            if (value := _piece(llm, token_id)) is not None
        ]
        add(stratified)

    rows.extend(selected[:limit])
    diagnostics = {
        "vocab": llm.n_vocab(),
        "decoded_unique": decoded,
        "selected": len(rows),
        "special_available": len(special),
        "symbol_available": len(symbols),
        "semantic_pool": len(semantic),
        "baseline_logit_pool": len(logit_rows),
    }
    return rows, diagnostics
