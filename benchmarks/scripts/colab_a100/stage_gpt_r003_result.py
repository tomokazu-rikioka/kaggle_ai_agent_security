"""Colab session内のr003結果をdownloadしやすい/content直下へ複製する。"""

from __future__ import annotations

import shutil
from pathlib import Path

source = Path("/content/aas-a100/results/gpt_r003_n2000.json")
target = Path("/content/gpt_r003_n2000.json")
print(f"source={source} exists={source.is_file()}")
if not source.is_file():
    print("candidates=", sorted(str(path) for path in Path("/content").rglob("gpt_r003_n2000.json")))
    raise FileNotFoundError(source)
shutil.copy2(source, target)
print(f"staged={target} bytes={target.stat().st_size}")
