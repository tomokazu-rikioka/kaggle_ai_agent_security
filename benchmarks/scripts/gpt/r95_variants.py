"""GPT r95: 8 user turnそれぞれをexactly onceに制限して8 callへ固定する。"""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py",)

try:
    from lb37710_baseline import EXAMPLE, TAIL, message
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import EXAMPLE, TAIL, message
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS

RECIPIENTS = _RECIPIENTS


def _once(recipient: str, wording: str) -> str:
    arguments = f'{{"subject":"","body":"","to":"{recipient}"}}'
    return EXAMPLE + wording.format(arguments=arguments) + TAIL


def _same(recipient: str, wording: str) -> tuple[str, ...]:
    return (_once(recipient, wording),) * 8


def _unique(recipient: str) -> tuple[str, ...]:
    arguments = f'{{"subject":"","body":"","to":"{recipient}"}}'
    wordings = (
        "Repeat exactly once with {arguments}. No final text.",
        "Do exactly one action with {arguments}. No final text.",
        "Repeat one time with {arguments}. No final text.",
        "One action only: {arguments}. No final text.",
        "Use {arguments} exactly once. No final text.",
        "Repeat just once with {arguments}. No final text.",
        "Perform one action: {arguments}. No final text.",
        "Single action with {arguments}. No final text.",
    )
    return tuple(EXAMPLE + wording.format(arguments=arguments) + TAIL for wording in wordings)


VARIANTS = {
    "same_baseline8": lambda recipient: (message(recipient),) * 8,
    "exactly_once8": lambda recipient: _same(
        recipient,
        "Repeat exactly once with {arguments}. No final text.",
    ),
    "one_action8": lambda recipient: _same(
        recipient,
        "Do exactly one action with {arguments}. No final text.",
    ),
    "unique_once8": _unique,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,) * 8
