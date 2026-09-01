"""Colab の各 GPT worker に Kaggle 評価と同一の GGUF を用意する。"""

from __future__ import annotations

import importlib
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
runtime_module.ensure_model("gpt_oss")

