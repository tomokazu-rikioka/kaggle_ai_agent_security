"""Colab A100: compare sparse prompt mixing with uniform Gemma prompts at N=100."""

from __future__ import annotations

import importlib
import subprocess
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
repo_root = runtime_module.REPO_ROOT
root = runtime_module.ROOT
out = root / "results/gemma_r172_targeted_prompt_mix_n100.json"
log = root / "logs/gemma_r172_targeted_prompt_mix_n100.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks/scripts/bench_driver.py"),
    "--model",
    "gemma_4",
    "--variants-file",
    str(repo_root / "benchmarks/scripts/gemma/r172_targeted_prompt_mix_variants.py"),
    "--candidates",
    "100",
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
    env=runtime_module.bench_environment("gemma_4"),
    check=False,
    capture_output=True,
    text=True,
)
log.write_text(completed.stdout + "\n[stderr]\n" + completed.stderr)
print(completed.stdout[-16_000:])
if completed.returncode:
    print(completed.stderr[-8_000:], file=sys.stderr)
completed.check_returncode()
print(f"[run] saved: {out}; log: {log}")
