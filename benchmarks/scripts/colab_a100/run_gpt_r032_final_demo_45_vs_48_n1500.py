"""Colab A100: 空final45と48をN=1,500で直接ABBA比較する。"""

from __future__ import annotations

import importlib
import subprocess
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
repo_root = runtime_module.REPO_ROOT
root = runtime_module.ROOT
out = root / "results" / "gpt_r032_final_demo_45_vs_48_n1500.json"
log = root / "logs" / "gpt_r032_final_demo_45_vs_48_n1500.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks" / "scripts" / "bench_driver.py"),
    "--model",
    "gpt_oss",
    "--variants-file",
    str(repo_root / "benchmarks" / "scripts" / "gpt" / "r116_variants.py"),
    "--candidates",
    "1500",
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
    cwd=repo_root,
    env=runtime_module.bench_environment("gpt_oss"),
    check=False,
    capture_output=True,
    text=True,
)
log.write_text(completed.stdout + "\n[stderr]\n" + completed.stderr)
for line in completed.stdout.splitlines():
    if line.startswith(("[bench]", "[eval]")):
        print(line)
if completed.returncode:
    print(completed.stderr[-8_000:], file=sys.stderr)
completed.check_returncode()
print(f"[run] saved: {out}; log: {log}")
