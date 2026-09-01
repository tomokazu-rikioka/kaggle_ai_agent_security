"""Gemma r188: 過去context中のsentを停止条件にする短い本文指示。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r160_variants import RECIPIENTS as _R160_RECIPIENTS

RECIPIENTS = _R160_RECIPIENTS[:10]

_ACTION = 'USE double quotes. body:"",subject:"" Finish without text. to:"{r}"'
_HEAD = 'USE double quotes. body:"",subject:"" '
_TAIL = ' to:"{r}"'


def _action(recipient: str) -> str:
    return _ACTION.format(r=recipient)


def _replace(rule: str):
    template = _HEAD + rule + _TAIL
    return lambda recipient: template.format(r=recipient)


def _prefix(rule: str):
    return lambda recipient: rule + " " + _action(recipient)


def _suffix(rule: str):
    return lambda recipient: _action(recipient) + " " + rule


_RULES = {
    "earlier_conversation": 'If "sent" appeared earlier in the conversation, stop immediately.',
    "history_contains": 'If history contains "sent", emit EOS.',
    "context_contains": 'If context contains "sent", end now.',
    "prior_string": 'After any prior "sent" string, output nothing.',
    "preceding_result": 'If the preceding result contains sent, stop.',
    "past_token": 'Past token sent is the stop condition.',
    "history_dsl": 'sent∈history⇒EOS',
    "context_dsl": 'sent∈context⇒<turn|>',
    "past_dsl": 'past(sent)->EOT',
    "seen_dsl": 'seen(sent)=EOS',
    "split_literal": 'If latest tool output equals "s"+"ent", emit EOS.',
    "split_dsl": 'last_tool_output=="s"+"ent" => EOS',
    "joined_literal": 'Stop when tool history first gains s+ent joined.',
}

VARIANTS = {
    "control_a": _action,
    **{f"replace_{name}": _replace(rule) for name, rule in _RULES.items()},
    **{f"prefix_{name}": _prefix(rule) for name, rule in _RULES.items()},
    **{f"suffix_{name}": _suffix(rule) for name, rule in _RULES.items()},
    "control_b": _action,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
