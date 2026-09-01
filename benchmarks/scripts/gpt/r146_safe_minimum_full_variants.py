"""GPT r146: full replay of normalization-safe theoretical-minimum finalists."""

from __future__ import annotations

import unicodedata

try:
    from r143_safe_minimum_variants import RECIPIENTS as _RECIPIENTS
    from r143_safe_minimum_variants import VARIANTS as _MINIMUM
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r143_safe_minimum_variants import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.r143_safe_minimum_variants import VARIANTS as _MINIMUM

RECIPIENTS = _RECIPIENTS

_NAMES = (
    "minimum_02_3",
    "minimum_00_4",
    "minimum_03_3",
    "minimum_00_3",
    "minimum_02_4",
    "minimum_06_4",
)

VARIANTS = {
    **{f"{name}_a": _MINIMUM[name] for name in _NAMES},
    **{f"{name}_b": _MINIMUM[name] for name in reversed(_NAMES)},
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
