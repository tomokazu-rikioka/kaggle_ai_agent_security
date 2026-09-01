"""Colab に置いた両 GGUF のサイズ/SHA-256 manifest を更新する。"""

from __future__ import annotations

import importlib
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
for model_kind in ("gpt_oss", "gemma_4"):
    runtime_module.ensure_model(model_kind)

