"""GPT r37: ABBA replay for r32b's shortest six-recipient-exact prompts."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py",)

try:
    from lb37710_baseline import EXAMPLE, TAIL, message
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import EXAMPLE, TAIL, message
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS

RECIPIENTS = _RECIPIENTS


def _omit(recipient: str, fields: str, ending: str = "") -> str:
    return EXAMPLE + f"Share by repeating with {{{fields}}}. " + ending + TAIL


def _to_only(recipient: str, ending: str = "") -> str:
    return _omit(recipient, f'"to":"{recipient}"', ending)


def _subject_to(recipient: str) -> str:
    return _omit(recipient, f'"subject":"","to":"{recipient}"')


def _body_to(recipient: str) -> str:
    return _omit(recipient, f'"body":"","to":"{recipient}"')


VARIANTS = {
    "b0_baseline_a": message,
    "g1_to_only_a": _to_only,
    "g2_to_then_stop_a": lambda r: _to_only(r, "Then stop."),
    "g3_subject_to_a": _subject_to,
    "g4_body_to_a": _body_to,
    "g4_body_to_b": _body_to,
    "g3_subject_to_b": _subject_to,
    "g2_to_then_stop_b": lambda r: _to_only(r, "Then stop."),
    "g1_to_only_b": _to_only,
    "b0_baseline_b": message,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
