"""Colab A100: GPT-OSS の初回 N=10 ABBA スモークテスト。"""

from __future__ import annotations

import importlib
import subprocess
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
REPO_ROOT = runtime_module.REPO_ROOT
ROOT = runtime_module.ROOT
bench_environment = runtime_module.bench_environment

out = ROOT / "results" / "gpt_r001_n10.json"
out.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(REPO_ROOT / "benchmarks" / "scripts" / "bench_driver.py"),
    "--model",
    "gpt_oss",
    "--variants-file",
    str(REPO_ROOT / "benchmarks" / "scripts" / "gpt" / "r100_variants.py"),
    "--candidates",
    "10",
    "--guardrails",
    "public",
    "--warmup-candidates",
    "1",
    "--max-tool-hops",
    "8",
    "--out",
    str(out),
]
print("[run]", " ".join(command))
completed = subprocess.run(
    command,
    cwd=REPO_ROOT,
    env=bench_environment("gpt_oss"),
    check=False,
    capture_output=True,
    text=True,
)
print(completed.stdout)
print(completed.stderr, file=sys.stderr)
completed.check_returncode()
print(f"[run] saved: {out}")
