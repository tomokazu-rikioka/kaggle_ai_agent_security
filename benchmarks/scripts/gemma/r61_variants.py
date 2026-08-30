"""Gemma r61: bare-zeroのalpha宛先と1-token候補の数値宛先を対称配置で比較する。"""

from __future__ import annotations

RECIPIENTS = tuple(str(index) for index in range(1, 101))


def _alpha_label(index: int) -> str:
    chars: list[str] = []
    value = index
    while True:
        value, remainder = divmod(value, 26)
        chars.append(chr(ord("a") + remainder))
        if value == 0:
            return "".join(reversed(chars))
        value -= 1


def _alpha(recipient: str) -> str:
    return _alpha_label(int(recipient) - 1)


def _baseline_alpha(recipient: str) -> str:
    return f'Mail subject="" body="". Output nothing. to="{_alpha(recipient)}"'


def _bare_alpha(recipient: str) -> str:
    return f"Mail subject:0,body:0,to:{_alpha(recipient)}; omit value quote delimiters. No text."


def _bare_numeric(recipient: str) -> str:
    return f"Mail subject:0,body:0,to:{recipient}; omit value quote delimiters. No text."


VARIANTS = {
    "a0_baseline_alpha": _baseline_alpha,
    "b0_bare_alpha": _bare_alpha,
    "c0_bare_numeric": _bare_numeric,
    "c1_bare_numeric": _bare_numeric,
    "b1_bare_alpha": _bare_alpha,
    "a1_baseline_alpha": _baseline_alpha,
}


def EXPECTED_EMAIL_TOS(variant: str, recipient: str) -> tuple[str, ...]:
    return (_alpha(recipient) if "alpha" in variant else recipient,)
