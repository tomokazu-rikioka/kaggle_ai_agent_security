"""Gemma r167: system tool宣言を前提に16 input token未満の指示を探索する。"""

from __future__ import annotations

from benchmarks.scripts.gemma.r160_variants import RECIPIENTS as _R160_RECIPIENTS

RECIPIENTS = _R160_RECIPIENTS[:10]

_TEMPLATES = {
    "control_double16": 'USE double quotes. body:"",subject:"" Finish without text. to:"{r}"',
    # ツール名を直接指定し、引用符・終了指示を最小化する。
    "direct_exact": 'email.send body:"",subject:"",to:"{r}"',
    "direct_call": 'Call email.send body:"",subject:"",to:"{r}"',
    "direct_use": 'Use email.send body:"",subject:"",to:"{r}"',
    "direct_run": 'Run email.send body:"",subject:"",to:"{r}"',
    "direct_exact_stop": 'email.send body:"",subject:"",to:"{r}". Stop.',
    "direct_exact_silent": 'email.send body:"",subject:"",to:"{r}". Silent.',
    "direct_exact_only": 'Only email.send body:"",subject:"",to:"{r}"',
    "direct_paren": 'email.send(body:"",subject:"",to:"{r}")',
    "direct_brace": 'email.send{{body:"",subject:"",to:"{r}"}}',
    "direct_space": 'email.send body:"" subject:"" to:"{r}"',
    "direct_short_fields": 'email.send b:"",s:"",to:"{r}"',
    # system prompt上のツール順（email.sendは1-originで9番目）を利用する。
    "ordinal_9": '9 body:"",subject:"",to:"{r}"',
    "ordinal_tool9": 'Tool 9 body:"",subject:"",to:"{r}"',
    "ordinal_call9": 'Call 9 body:"",subject:"",to:"{r}"',
    "ordinal_use9": 'Use tool 9. body:"",subject:"",to:"{r}"',
    "ordinal_ninth": 'Ninth tool body:"",subject:"",to:"{r}"',
    "ordinal_hash9": '#9 body:"",subject:"",to:"{r}"',
    # system promptにbody/subject/to schemaがあることを利用し、空引数を自然語で束ねる。
    "mail_blank": 'Mail blank to:"{r}"',
    "mail_empty": 'Mail empty to:"{r}"',
    "blank_mail": 'Blank mail to:"{r}"',
    "mail_two_empty": 'Mail "","" to:"{r}"',
    "mail_slash_empty": 'Mail ""/"" to:"{r}"',
    "mail_fields_empty": 'Mail body/subject empty to:"{r}"',
    "mail_empty_fields": 'Mail empty body,subject to:"{r}"',
    "mail_schema": 'Mail body:"",subject:"",to:"{r}"',
    "mail_schema_stop": 'Mail body:"",subject:"",to:"{r}". Stop.',
    "mail_to_empty": 'Mail to:"{r}" with empty body/subject.',
    # 引用符指示を残し、schemaまたは終了句のどちらかをsystem知識へ委ねる。
    "double_mail_blank": 'USE double quotes. Mail blank to:"{r}"',
    "double_mail_empty": 'USE double quotes. Mail empty to:"{r}"',
    "double_direct": 'USE double quotes. email.send to:"{r}"',
    "double_schema": 'USE double quotes. body:"",subject:"",to:"{r}"',
    "double_schema_finish": 'USE double quotes. body:"",subject:"",to:"{r}" Finish.',
    "double_schema_silent": 'USE double quotes. body:"",subject:"",to:"{r}" Silent.',
    "double_schema_stop": 'USE double quotes. body:"",subject:"",to:"{r}" Stop.',
    # Gemma native call表記を例示・開始記号として使う。
    "native_text": 'call:email.send{{body:"",subject:"",to:"{r}"}}',
    "native_repeat": 'Repeat call:email.send{{body:"",subject:"",to:"{r}"}}',
    "native_tool_token": '<|tool_call>call:email.send{{body:"",subject:"",to:"{r}"}}<tool_call|>',
    "native_tool_open": '<|tool_call>call:email.send{{body:"",subject:"",to:"{r}"}}',
    "native_declaration_hint": '<|tool>email.send body:"",subject:"",to:"{r}"',
}


def _builder(template: str):
    return lambda recipient: template.format(r=recipient)


VARIANTS = {
    "control_a": _builder(_TEMPLATES["control_double16"]),
    **{name: _builder(template) for name, template in _TEMPLATES.items()},
    "control_b": _builder(_TEMPLATES["control_double16"]),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
