"""Colab A100: search GPT subject/body values for an immediate post-tool return."""

from __future__ import annotations

import importlib
import subprocess
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
repo_root = runtime_module.REPO_ROOT
root = runtime_module.ROOT
out = root / "results/gpt_r121_tail_value_sweep.json"
log = root / "logs/gpt_r121_tail_value_sweep.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks/scripts/tail_state_value_sweep.py"),
    "--model",
    "gpt_oss",
    "--fields",
    "subject,body",
    "--max-call-added",
    "2",
    "--max-message-added",
    "4",
    "--keep",
    "400",
    "--out",
    str(out),
]
print("[run]", " ".join(command))
completed = subprocess.run(
    command,
    cwd=repo_root,
    env=runtime_module.bench_environment("gpt_oss"),
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
