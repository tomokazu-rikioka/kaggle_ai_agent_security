"""Colab A100 ベンチ用ランタイムを初期化する。

このファイルは ``colab exec -s aas-a100 -f ...`` で Colab 側に送って実行する。
モデルは各ベンチ開始時に個別取得し、この段階では Python 依存だけを揃える。
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path


def _run(command: list[str]) -> None:
    print("[setup]", " ".join(command))
    subprocess.run(command, check=True)


_run([sys.executable, "-m", "pip", "-q", "install", "gymnasium", "pydantic>=2", "huggingface_hub"])
_run(
    [
        sys.executable,
        "-m",
        "pip",
        "-q",
        "install",
        "llama-cpp-python",
        "--extra-index-url",
        "https://abetlen.github.io/llama-cpp-python/whl/cu124",
    ]
)

import llama_cpp  # noqa: E402
import torch  # noqa: E402

root = Path("/content/aas-a100")
root.mkdir(parents=True, exist_ok=True)
runtime = {
    "python": sys.version,
    "platform": platform.platform(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "gpu_memory_bytes": torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else None,
    "llama_cpp_python": llama_cpp.__version__,
}
if runtime["gpu"] != "NVIDIA A100-SXM4-40GB":
    raise RuntimeError(f"想定した A100 ではありません: {runtime['gpu']!r}")
(root / "runtime.json").write_text(json.dumps(runtime, ensure_ascii=False, indent=2))
print(json.dumps(runtime, ensure_ascii=False, indent=2))

