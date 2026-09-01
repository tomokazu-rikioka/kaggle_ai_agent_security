"""Colab A100: smoke-test the Gemma post-tool value sweep on 256 token IDs."""

from __future__ import annotations

import importlib
import subprocess
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
repo_root = runtime_module.REPO_ROOT
root = runtime_module.ROOT
out = root / "results/gemma_r162_smoke.json"
command = [
    sys.executable,
    str(repo_root / "benchmarks/scripts/tail_state_value_sweep.py"),
    "--model",
    "gemma_4",
    "--style",
    "double16",
    "--fields",
    "subject",
    "--stop-token",
    "256",
    "--keep",
    "30",
    "--out",
    str(out),
]
completed = subprocess.run(
    command,
    cwd=repo_root,
    env=runtime_module.bench_environment("gemma_4"),
    capture_output=True,
    text=True,
)
print(completed.stdout[-12_000:])
if completed.returncode:
    print(completed.stderr[-12_000:], file=sys.stderr)
completed.check_returncode()
print(f"[run] saved: {out}")
