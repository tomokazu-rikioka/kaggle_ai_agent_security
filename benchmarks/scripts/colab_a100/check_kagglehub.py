"""Colab の kagglehub 公開モデル取得 API を確認する診断。"""

from __future__ import annotations

import inspect
from pathlib import Path

import kagglehub

print("kagglehub", kagglehub.__version__)
print("model_download", inspect.signature(kagglehub.model_download))
for handle in (
    "llkh0a/gpt-oss-20b-gguf/pyTorch/default/1",
    "llkh0a/gemma-4-26b-a4b-it-ud-q4-k-m-gguf/pyTorch/default/1",
):
    path = Path(kagglehub.model_download(handle, path="manifest.json"))
    print(handle, path)
    print(path.read_text())
