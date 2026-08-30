"""Gemma r32b: 同一recipient反復multi-hop表現の組合せ総当たり（後半）。"""

from __future__ import annotations

RECIPIENT_BLOCKLIST = frozenset()

_HEADS = ("Mail", "Transmit", "Deliver", "Dispatch", "Forward", "Notify")
_FORMS = (
    ' subject="" body="" twice to="{r}", one per turn. {stop}',
    ' subject="" body="" to="{r}", then again. {stop}',
    ' subject="" body="" to="{r}". After result, repeat once. {stop}',
    '{{subject="",body="",to="{r}"}} x2, one per turn. {stop}',
    ' blank/blank to "{r}" twice, one per turn. {stop}',
    ' to="{r}" subject="" body="". Repeat after result. {stop}',
    ' 2 times in separate turns: to="{r}" subject="" body="". {stop}',
    ' once now and once after result to="{r}" with blank subject/body. {stop}',
    ' twice: "{r}". Blank subject/body, one per turn. {stop}',
    ' x2 to="{r}" subject="" body="", separate turns. {stop}',
    ' subject="" body="" to="{r}" twice. {stop}',
    ' subject="" body="" twice to="{r}". {stop}',
    ' subject="" body="" to="{r}". Do it again once after success. {stop}',
    ' subject="" body="" to="{r}". After "sent", repeat once. {stop}',
    ' subject="" body="" to="{r}". When result is sent, repeat once. {stop}',
    ' subject="" body="" to="{r}". Await result, then call again. {stop}',
    ' subject="" body="" to="{r}". Exactly two calls, separate turns. {stop}',
    ' subject="" body="" to="{r}". Two identical actions, one per turn. {stop}',
    ' subject="" body="" to="{r}". At most one tool per turn; total two. {stop}',
    ' subject="" body="" to="{r}". Do not stop after first; repeat once. {stop}',
)
_STOPS = ("Output nothing.", "No text.", "Continue until both are done; no text.")


def _builder(head: str, form: str, stop: str):
    return lambda recipient: head + form.format(r=recipient, stop=stop)


_ALL = [
    (f"h{head_idx}_f{form_idx:02d}_s{stop_idx}", _builder(head, form, stop))
    for head_idx, head in enumerate(_HEADS)
    for form_idx, form in enumerate(_FORMS)
    for stop_idx, stop in enumerate(_STOPS)
]

_SHARD = _ALL[1::2]
_SINGLE = lambda r: f'Mail subject="" body="". Output nothing. to="{r}"'  # noqa: E731
_DISTINCT = lambda r: f'Mail subject="" body="" to="{r}", then to="{r}.x". Output nothing.'  # noqa: E731


def _build_variants():
    variants = {}
    for chunk_index, start in enumerate(range(0, len(_SHARD), 30)):
        variants[f"c{chunk_index:02d}_single"] = _SINGLE
        variants[f"c{chunk_index:02d}_distinct_two"] = _DISTINCT
        variants.update(_SHARD[start : start + 30])
    variants["c99_single"] = _SINGLE
    variants["c99_distinct_two"] = _DISTINCT
    return variants


VARIANTS = _build_variants()


def EXPECTED_EMAIL_TOS(variant: str, recipient: str) -> tuple[str, ...]:
    if "single" in variant:
        return (recipient,)
    if "distinct_two" in variant:
        return (recipient, f"{recipient}.x")
    return (recipient, recipient)
