"""Colab A100: r001通過案を N=100 ABBA で再計測する。"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
REPO_ROOT = runtime_module.REPO_ROOT
ROOT = runtime_module.ROOT


def run_bench(model: str, variants_file: Path, output_name: str) -> None:
    out = ROOT / "results" / output_name
    log = ROOT / "logs" / output_name.replace(".json", ".log")
    out.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(REPO_ROOT / "benchmarks" / "scripts" / "bench_driver.py"),
        "--model",
        model,
        "--variants-file",
        str(variants_file),
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
        cwd=REPO_ROOT,
        env=runtime_module.bench_environment(model),
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


run_bench(
    "gpt_oss",
    REPO_ROOT / "benchmarks" / "scripts" / "gpt" / "r100_variants.py",
    "gpt_r002_n100.json",
)
run_bench(
    "gemma_4",
    REPO_ROOT / "benchmarks" / "scripts" / "gemma" / "r122_variants.py",
    "gemma_r002_n100.json",
)

