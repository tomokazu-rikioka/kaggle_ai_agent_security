"""Gemma r138: 引用符prefixと17-token core短縮の交互作用をN=10探索する。"""

from __future__ import annotations

RECIPIENTS = ("0", "a", "z", "by", "cc", "no", "AIM", "ARC", "CCI", "CND")

_PREFIXES = {
    "straight": "USE straight quotes.",
    "double": "USE double quotes.",
    "ordinary": "USE ordinary double quotes for values.",
    "quoted": "USE quoted values.",
    "plain": "USE plain quotes.",
    "ascii": "USE ASCII quotes.",
}

_CORES = {
    "nodot": 'Mail body:"",subject:"" Finish without text. to:"{r}"',
    "nomail": 'body:"",subject:"". Finish without text. to:"{r}"',
    "inline": 'Mail body:"",subject:"",to:"{r}". Finish without text.',
    "inline_nodot": 'Mail body:"",subject:"",to:"{r}" Finish without text.',
}


def _builder(prefix: str, core: str):
    template = f"{prefix} {core}"
    return lambda recipient: template.format(r=recipient)


VARIANTS = {
    "control_a": _builder(_PREFIXES["straight"], _CORES["nodot"]),
    **{
        f"{prefix_name}_{core_name}": _builder(prefix, core)
        for prefix_name, prefix in _PREFIXES.items()
        for core_name, core in _CORES.items()
    },
    "control_b": _builder(_PREFIXES["straight"], _CORES["nodot"]),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
