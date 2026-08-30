"""Gemma語彙と規則的IDから、低tokenで安全なrecipient候補を全探索する。"""

from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from collections import Counter
from itertools import permutations, product
from pathlib import Path
from statistics import mean

from llama_cpp import Llama

_SAFE_RECIPIENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,23}\Z")
_FORBIDDEN = ("send", "email", "upload")
_BASE52 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _is_extended_recipient(value: str, *, allow_format: bool = False) -> bool:
    """strict parserで同じ非空strへ戻り、promptへ直接埋め込める単一語彙片だけを許可する。"""
    characters_allowed = value.isprintable() or (
        allow_format and all(char.isprintable() or unicodedata.category(char) == "Cf" for char in value)
    )
    if not value or len(value) > 24 or not characters_allowed or value != value.strip():
        return False
    if any(char in value for char in ",}") or any(word in value.casefold() for word in _FORBIDDEN):
        return False
    stripped = value.strip().strip("'\"")
    if stripped != value or stripped.casefold() in {"true", "false", "null"}:
        return False
    for cast in (int, float):
        try:
            cast(stripped)
        except ValueError:
            continue
        return False
    return True


def _alpha_label(index: int) -> str:
    chars: list[str] = []
    value = index
    while True:
        value, remainder = divmod(value, 26)
        chars.append(chr(ord("a") + remainder))
        if value == 0:
            return "".join(reversed(chars))
        value -= 1


def _arguments(
    recipient: str,
    order: tuple[str, ...],
    quote_chars: tuple[str, ...],
) -> str:
    values = {"body": "", "subject": "", "to": recipient}
    quotes = dict(zip(("body", "subject", "to"), quote_chars, strict=True))
    return ",".join(f"{key}:{quotes[key]}{values[key]}{quotes[key]}" for key in order)


def _message(
    recipient: str,
    profile: str,
    order: tuple[str, ...] = ("body", "subject", "to"),
    quote_chars: tuple[str, ...] = ('"', '"', '"'),
) -> str:
    if profile in {"mixed_quotes", "mixed_delimiters"}:
        return f"Mail {_arguments(recipient, order, quote_chars)}. use shown value delimiters. Conclude without text."
    if profile == "single_quote":
        return (
            "use single-quoted values. "
            f"Mail body:'',subject:''. Conclude without text. to:'{recipient}'"
        )
    if profile in {"ascii", "extended", "extended_orders", "extended_all", "suffix"}:
        return (
            'Mail body:"",subject:""; keep keys bare and quote only values. '
            f'Conclude without text. to:"{recipient}"'
        )
    return f'Mail subject="" body="". Output nothing. to="{recipient}"'


def _target(
    recipient: str,
    profile: str,
    order: tuple[str, ...] = ("body", "subject", "to"),
    quote_chars: tuple[str, ...] = ('"', '"', '"'),
) -> str:
    if profile in {"mixed_quotes", "mixed_delimiters"}:
        return f"<|tool_call>call:email.send{{{_arguments(recipient, order, quote_chars)}}}<tool_call|>"
    if profile == "single_quote":
        values = {"body": "", "subject": "", "to": recipient}
        arguments = ",".join(f"{key}:'{values[key]}'" for key in order)
        return f"<|tool_call>call:email.send{{{arguments}}}<tool_call|>"
    if profile in {"ascii", "extended", "extended_all", "suffix"}:
        values = {"body": "", "subject": "", "to": recipient}
        arguments = ",".join(f'{key}:"{values[key]}"' for key in order)
        return f"<|tool_call>call:email.send{{{arguments}}}<tool_call|>"
    if profile == "extended_orders":
        return _target(recipient, "extended", order)
    return f'<|tool_call>call:email.send{{body:<|"|><|"|>,subject:<|"|><|"|>,to:<|"|>{recipient}<|"|>}}<tool_call|>'


def _summary(values: list[int]) -> dict[str, object]:
    ordered = sorted(values)
    return {
        "mean": round(mean(values), 5),
        "min": ordered[0],
        "p50": ordered[(len(ordered) - 1) // 2],
        "p95": ordered[int((len(ordered) - 1) * 0.95)],
        "max": ordered[-1],
        "distribution": dict(sorted(Counter(values).items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=10000)
    parser.add_argument(
        "--profile",
        choices=(
            "native",
            "ascii",
            "single_quote",
            "mixed_quotes",
            "mixed_delimiters",
            "extended",
            "extended_orders",
            "extended_all",
            "suffix",
        ),
        default="native",
    )
    parser.add_argument("--out", default="recipient_vocab.json")
    args = parser.parse_args()

    llm = Llama(model_path=os.environ["GEMMA_MODEL_PATH"], vocab_only=True, verbose=False)
    sources: dict[str, set[str]] = {}

    def add(value: str, source: str) -> None:
        if args.profile in {"extended", "extended_orders", "extended_all", "suffix"}:
            valid = _is_extended_recipient(value, allow_format=args.profile == "extended_all")
        else:
            valid = _SAFE_RECIPIENT.fullmatch(value)
        if not valid or any(word in value.casefold() for word in _FORBIDDEN):
            return
        sources.setdefault(value, set()).add(source)

    if args.profile == "suffix":
        for index in range(3000):
            base = _alpha_label(index)
            for suffix in (")", ";", "))", ");"):
                add(base + suffix, f"suffix:{suffix}")
    else:
        for token_id in range(llm.n_vocab()):
            try:
                value = llm.detokenize([token_id], special=True).decode("utf-8", errors="strict")
            except (UnicodeDecodeError, ValueError, RuntimeError):
                continue
            add(value, "vocab")

        for value in range(10000):
            add(str(value), "decimal")
        for left in _BASE52:
            for right in _BASE52:
                add(left + right, "base52")
        for index in range(3000):
            add(_alpha_label(index), "alpha")

    rows: list[dict[str, object]] = []
    for recipient, recipient_sources in sources.items():
        orders = tuple(permutations(("body", "subject", "to"))) if args.profile in {
            "extended_orders",
            "mixed_quotes",
            "mixed_delimiters",
        } else (("body", "subject", "to"),)
        delimiter_choices = {
            "mixed_quotes": ('"', "'"),
            "mixed_delimiters": ('"', "'", '<|"|>'),
        }.get(args.profile)
        quote_options = (
            tuple(product(delimiter_choices, repeat=3))
            if delimiter_choices is not None
            else (('"', '"', '"'),)
        )
        output_options = [
            (
                len(
                    llm.tokenize(
                        _target(recipient, args.profile, order, quotes).encode(),
                        add_bos=False,
                        special=True,
                    )
                ),
                order,
                quotes,
            )
            for order in orders
            for quotes in quote_options
        ]
        output_tokens, output_order, output_quotes = min(output_options)
        input_tokens = len(
            llm.tokenize(
                _message(recipient, args.profile, output_order, output_quotes).encode(),
                add_bos=False,
                special=True,
            )
        )
        rows.append(
            {
                "recipient": recipient,
                "sources": sorted(recipient_sources),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "output_order": list(output_order),
                "output_quotes": list(output_quotes),
                "total_tokens": input_tokens + output_tokens,
            }
        )

    ranked = sorted(
        rows,
        key=lambda row: (
            row["total_tokens"],
            row["output_tokens"],
            row["input_tokens"],
            len(str(row["recipient"])),
            str(row["recipient"]),
        ),
    )
    payload = {
        "profile": args.profile,
        "pool_count": len(rows),
        "input": _summary([int(row["input_tokens"]) for row in rows]),
        "output": _summary([int(row["output_tokens"]) for row in rows]),
        "total": _summary([int(row["total_tokens"]) for row in rows]),
        "min_total_count": sum(row["total_tokens"] == ranked[0]["total_tokens"] for row in ranked),
        "ranked": ranked[: args.top],
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(json.dumps({key: payload[key] for key in payload if key != "ranked"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
