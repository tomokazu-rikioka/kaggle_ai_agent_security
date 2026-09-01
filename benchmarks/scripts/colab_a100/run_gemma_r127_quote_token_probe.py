"""Colab A100: ALLCAPS引用符候補をtoken/NLL/生成で比較する。"""

from __future__ import annotations

import importlib
import subprocess
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
repo_root = runtime_module.REPO_ROOT
root = runtime_module.ROOT
out = root / "results" / "gemma_r127_quote_token_probe.json"
log = root / "logs" / "gemma_r127_quote_token_probe.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks" / "scripts" / "token_probe.py"),
    "--model",
    "gemma_4",
    "--candidates-file",
    str(repo_root / "benchmarks" / "scripts" / "gemma" / "r127_candidates.py"),
    "--recipient",
    "a",
    "--validation-recipients",
    "0,a,z,by,cc,no,AIM,ARC,CCI,CND",
    "--preview-tokens",
    "48",
    "--target-tokens",
    "48",
    "--prune-primary-miss",
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
for line in completed.stdout.splitlines():
    if line.startswith("[probe]"):
        print(line)
if completed.returncode:
    print(completed.stderr[-8_000:], file=sys.stderr)
completed.check_returncode()
print(f"[run] saved: {out}; log: {log}")
