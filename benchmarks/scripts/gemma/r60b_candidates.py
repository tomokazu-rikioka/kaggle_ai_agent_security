"""Gemma r60b: bare scalarとrecipient末尾配置を両立させる後半640候補。"""

from __future__ import annotations

from benchmarks.scripts.gemma import r60a_candidates as source

BASELINE_NAME = source.BASELINE_NAME
EXPECTED_MARKER = source.EXPECTED_MARKER
EXPECTED_ARGUMENTS = source.EXPECTED_ARGUMENTS
TARGET_TEXT = source.TARGET_TEXT

CANDIDATES = {
    BASELINE_NAME: lambda r: f'Mail subject="" body="". Output nothing. to="{r}"',
    **dict(source._ALL[1::2]),
}
