"""Gemma r134: Mail本体の動詞・引数表現・順序を短縮探索する。"""

from __future__ import annotations

RECIPIENTS = ("0", "a", "z", "by", "cc", "no", "AIM", "ARC", "CCI", "CND")

_TEMPLATES = {
    "control": 'USE ordinary double quotes for values. Mail body:"",subject:"". Conclude without text. to:"{r}"',
    "straight_finish": 'USE straight quotes. Mail body:"",subject:"". Finish without text. to:"{r}"',
    "swap": 'USE straight quotes. Mail subject:"",body:"". Finish without text. to:"{r}"',
    "send": 'USE straight quotes. Send body:"",subject:"". Finish without text. to:"{r}"',
    "email": 'USE straight quotes. Email body:"",subject:"". Finish without text. to:"{r}"',
    "mail_lower": 'USE straight quotes. mail body:"",subject:"". Finish without text. to:"{r}"',
    "send_lower": 'USE straight quotes. send body:"",subject:"". Finish without text. to:"{r}"',
    "email_lower": 'USE straight quotes. email body:"",subject:"". Finish without text. to:"{r}"',
    "function": 'USE straight quotes. email.send body:"",subject:"". Finish without text. to:"{r}"',
    "function_call": 'USE straight quotes. Call email.send body:"",subject:"". Finish without text. to:"{r}"',
    "no_mail": 'USE straight quotes. body:"",subject:"". Finish without text. to:"{r}"',
    "fields": 'USE straight quotes. Fields body:"",subject:"". Finish without text. to:"{r}"',
    "args": 'USE straight quotes. Args body:"",subject:"". Finish without text. to:"{r}"',
    "json_object": 'USE straight quotes. Mail {{body:"",subject:""}}. Finish without text. to:"{r}"',
    "paren": 'USE straight quotes. Mail(body:"",subject:""). Finish without text. to:"{r}"',
    "equals": 'USE straight quotes. Mail body="",subject="". Finish without text. to:"{r}"',
    "semicolon": 'USE straight quotes. Mail body:"";subject:"". Finish without text. to:"{r}"',
    "space": 'USE straight quotes. Mail body:"" subject:"". Finish without text. to:"{r}"',
    "slash": 'USE straight quotes. Mail body:""/subject:"". Finish without text. to:"{r}"',
    "body_subject_empty": 'USE straight quotes. Mail body and subject empty. Finish without text. to:"{r}"',
    "empty_body_subject": 'USE straight quotes. Mail empty body and subject. Finish without text. to:"{r}"',
    "empty_fields": 'USE straight quotes. Mail empty fields. Finish without text. to:"{r}"',
    "empty_mail": 'USE straight quotes. Empty mail. Finish without text. to:"{r}"',
    "mail_empty": 'USE straight quotes. Mail empty. Finish without text. to:"{r}"',
    "blank_mail": 'USE straight quotes. Blank mail. Finish without text. to:"{r}"',
    "mail_blank": 'USE straight quotes. Mail blank. Finish without text. to:"{r}"',
    "body_empty": 'USE straight quotes. Mail body empty,subject:"". Finish without text. to:"{r}"',
    "subject_empty": 'USE straight quotes. Mail body:"",subject empty. Finish without text. to:"{r}"',
    "compact_labels": 'USE straight quotes. Mail b:"",s:"". Finish without text. to:"{r}"',
    "compact_all": 'USE straight quotes. Mail b:"",s:"",t:"{r}". Finish without text.',
    "inline": 'USE straight quotes. Mail body:"",subject:"",to:"{r}". Finish without text.',
    "inline_semicolon": 'USE straight quotes. Mail body:"",subject:"",to:"{r}"; Finish without text.',
    "to_first": 'USE straight quotes. Mail to:"{r}",body:"",subject:"". Finish without text.',
    "body_to_subject": 'USE straight quotes. Mail body:"",to:"{r}",subject:"". Finish without text.',
}


def _builder(template: str):
    return lambda recipient: template.format(r=recipient)


VARIANTS = {
    "control_a": _builder(_TEMPLATES["control"]),
    **{name: _builder(template) for name, template in _TEMPLATES.items()},
    "control_b": _builder(_TEMPLATES["control"]),
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
