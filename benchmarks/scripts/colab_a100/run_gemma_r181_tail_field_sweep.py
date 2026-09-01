"""Colab A100: Gemma post-tool値探索をsubject/bodyへ分割して並列実行する。"""

from __future__ import annotations

import argparse
import importlib
import subprocess
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--field", choices=("subject", "body"), required=True)
args = parser.parse_args()

runtime_module = importlib.reload(runtime_module)
repo_root = runtime_module.REPO_ROOT
root = runtime_module.ROOT
out = root / f"results/gemma_r181_tail_{args.field}.json"
log = root / f"logs/gemma_r181_tail_{args.field}.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks/scripts/tail_state_value_sweep.py"),
    "--model",
    "gemma_4",
    "--style",
    "double16",
    "--fields",
    args.field,
    "--max-call-added",
    "2",
    "--max-message-added",
    "3",
    "--keep",
    "800",
    "--analyze-empty-thought",
    "--out",
    str(out),
]
print("[run]", " ".join(command))
completed = subprocess.run(
    command,
    cwd=repo_root,
    env=runtime_module.bench_environment("gemma_4"),
    check=False,
    capture_output=True,
    text=True,
)
log.write_text(completed.stdout + "\n[stderr]\n" + completed.stderr)
print(completed.stdout[-12_000:])
if completed.returncode:
    print(completed.stderr[-8_000:], file=sys.stderr)
completed.check_returncode()
print(f"[run] saved: {out}; log: {log}")
