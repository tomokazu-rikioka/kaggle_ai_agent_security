"""GPT r140: one-call full-replay comparison of normalization-safe finalists."""

from __future__ import annotations

import unicodedata

try:
    from r139_pure_notify_variants import RECIPIENTS as _RECIPIENTS
    from r139_pure_notify_variants import VARIANTS as _PURE
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r139_pure_notify_variants import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r139_pure_notify_variants import VARIANTS as _PURE

RECIPIENTS = _RECIPIENTS

_PURE_34 = _PURE["pure_x_empty_01"]
_PURE_36 = _PURE["pure_x_empty_00"]
_PURE_16 = _PURE["pure_none_03"]
_PURE_19 = _PURE["pure_none_00"]

VARIANTS = {
    "pure34_a": _PURE_34,
    "pure36_a": _PURE_36,
    "pure16_a": _PURE_16,
    "pure19_a": _PURE_19,
    "pure19_b": _PURE_19,
    "pure16_b": _PURE_16,
    "pure36_b": _PURE_36,
    "pure34_b": _PURE_34,
}

_RISKY = ("email", "mail", "send", "upload", "secret", "password", "credential", "confidential")


def _normalized_letters(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    return "".join(character for character in normalized if character.isalnum())


for _name, _builder in VARIANTS.items():
    _probe = _builder("a")
    _normalized = _normalized_letters(_probe)
    assert not any(_word in _normalized for _word in _RISKY), (_name, _normalized)


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
