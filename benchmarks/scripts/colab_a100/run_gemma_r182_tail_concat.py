"""Colab A100: r181上位値の同一field内 ordered concatを探索する。"""

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
seed = root / "results/gemma_r181_tail_merged.json"
out = root / f"results/gemma_r182_tail_concat_{args.field}.json"
log = root / f"logs/gemma_r182_tail_concat_{args.field}.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks/scripts/tail_state_value_concat_sweep.py"),
    "--seed-results",
    str(seed),
    "--field",
    args.field,
    "--top-values",
    "48",
    "--max-call-added",
    "3",
    "--max-message-added",
    "6",
    "--keep",
    "400",
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
