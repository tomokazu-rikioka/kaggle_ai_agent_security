"""GPT r145: full-replay comparison of normalization-safe semantic finalists."""

from __future__ import annotations

import unicodedata

try:
    from r141_safe_semantic_variants import RECIPIENTS as _RECIPIENTS
    from r141_safe_semantic_variants import VARIANTS as _SEMANTIC
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r141_safe_semantic_variants import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r141_safe_semantic_variants import VARIANTS as _SEMANTIC

RECIPIENTS = _RECIPIENTS

_NAMES = (
    "semantic_contact_2",
    "semantic_alert_4",
    "semantic_share_2",
    "semantic_correspond_2",
    "semantic_inform_2",
    "semantic_dispatch_2",
    "semantic_deliver_2",
    "semantic_notify_2",
)

VARIANTS = {
    **{f"{name}_a": _SEMANTIC[name] for name in _NAMES},
    **{f"{name}_b": _SEMANTIC[name] for name in reversed(_NAMES)},
}

_RISKY = ("email", "mail", "send", "upload", "secret", "password", "credential", "confidential")


def _normalized_letters(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    return "".join(character for character in normalized if character.isalnum())


for _name, _builder in VARIANTS.items():
    _normalized = _normalized_letters(_builder("a"))
    assert not any(_word in _normalized for _word in _RISKY), (_name, _normalized)


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
