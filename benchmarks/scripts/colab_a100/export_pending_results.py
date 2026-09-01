"""Colab file API が不安定な場合に、直近結果を標準出力へbase64退避する。"""

from __future__ import annotations

import base64
from pathlib import Path

RESULTS = (
    "gpt_r033_suffix0_n1500.json",
    "gpt_r034_suffix_placeholders_n1500.json",
    "gpt_r036_final_masks47_n1500.json",
    "gpt_r037_final_masks46_n1500.json",
)
root = Path("/content/aas-a100/results")
for name in RESULTS:
    path = root / name
    if path.is_file():
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        print(f"RESULT_BASE64_BEGIN {name} {len(payload)}")
        print(payload)
        print(f"RESULT_BASE64_END {name}")
