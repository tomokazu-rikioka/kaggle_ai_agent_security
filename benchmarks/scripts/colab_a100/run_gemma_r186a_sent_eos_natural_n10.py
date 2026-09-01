"""Colab A100: sent条件の自然文終了指示をN=10で実生成する。"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
repo_root = runtime_module.REPO_ROOT
root = runtime_module.ROOT
out = root / "results/gemma_r186a_sent_eos_natural_n10.json"
log = root / "logs/gemma_r186a_sent_eos_natural_n10.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks/scripts/bench_driver.py"),
    "--model",
    "gemma_4",
    "--variants-file",
    str(repo_root / "benchmarks/scripts/gemma/r186a_sent_eos_natural_variants.py"),
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
completed = subprocess.run(
    command, cwd=repo_root, env=runtime_module.bench_environment("gemma_4"), capture_output=True, text=True
)
log.write_text(completed.stdout + "\n[stderr]\n" + completed.stderr)
if completed.returncode:
    print(completed.stderr[-8_000:], file=sys.stderr)
completed.check_returncode()
payload = json.loads(out.read_text())
summary = {}
for name, row in payload["results"].items():
    metrics = row["guardrails"]["public"]
    summary[name] = {
        "message": row["sample_message"],
        "input": row["sample_tokens"],
        "raw_s": metrics["score_raw_per_s"],
        "raw": metrics["score_raw"],
        "cells": metrics["unique_cells"],
        "to": metrics["email_to_exact_rate"],
        "completion": metrics["completion_token_sequences"],
        "outputs": metrics["generation_text_sequences"],
    }
print("[summary-json]", json.dumps(summary, sort_keys=True))
print(f"[run] saved: {out}; log: {log}")
