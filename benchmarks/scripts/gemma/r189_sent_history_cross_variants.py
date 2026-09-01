"""Gemma r189: 過去tool/context中のsent条件と終了動作を総当たりする。"""

from __future__ import annotations

RECIPIENTS = ("0", "1")

_ACTION = 'USE double quotes. body:"",subject:"" Finish without text. to:"{r}"'
_HEAD = 'USE double quotes. body:"",subject:"" '
_TAIL = ' to:"{r}"'


def _action(recipient: str) -> str:
    return _ACTION.format(r=recipient)


def _replace(rule: str):
    template = _HEAD + rule + _TAIL
    return lambda recipient: template.format(r=recipient)


def _suffix(rule: str):
    return lambda recipient: _action(recipient) + " " + rule


_CONDITIONS = {
    "after": "After sent",
    "tool_result": "When sent appears in a tool result",
    "prior_context": "If prior context contains sent",
    "tool_history": "If sent is in tool history",
    "upon": "Upon reading sent",
    "once_result": "Once the result is sent",
    "latest_result": "Given latest result sent",
    "previous": "On previous sent",
    "exact_result": 'After exact result "sent"',
}
_ACTIONS = {
    "stop": "stop.",
    "end": "end.",
    "end_turn": "end the turn.",
    "return": "return.",
    "eos": "emit EOS.",
    "eot": "emit EOT.",
    "turn": "emit <turn|>.",
    "nothing": "output nothing.",
    "no_token": "produce no token.",
    "close": "close immediately.",
    "no_think": "do not think.",
    "halt": "halt generation.",
}

_RULES = {
    f"{condition_name}_{action_name}": f"{condition}, {action}"
    for condition_name, condition in _CONDITIONS.items()
    for action_name, action in _ACTIONS.items()
}

VARIANTS = {
    "control_a": _action,
    **{f"replace_{name}": _replace(rule) for name, rule in _RULES.items()},
    **{f"suffix_{name}": _suffix(rule) for name, rule in _RULES.items()},
    "control_b": _action,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
