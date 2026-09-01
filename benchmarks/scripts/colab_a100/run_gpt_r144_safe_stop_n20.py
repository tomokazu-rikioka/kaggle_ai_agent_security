"""Colab A100: full-replay screen of normalization-safe stop directives."""

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
out = root / "results/gpt_r144_safe_stop_n20.json"
log = root / "logs/gpt_r144_safe_stop_n20.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks/scripts/bench_driver.py"),
    "--model",
    "gpt_oss",
    "--variants-file",
    str(repo_root / "benchmarks/scripts/gpt/r144_safe_stop_variants.py"),
    "--candidates",
    "20",
    "--guardrails",
    "public",
    "--warmup-candidates",
    "1",
    "--max-tool-hops",
    "3",
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
if completed.returncode:
    print(completed.stderr[-8_000:], file=sys.stderr)
completed.check_returncode()
payload = json.loads(out.read_text())
ranked = []
for name, row in payload["results"].items():
    metrics = row["guardrails"]["public"]
    ranked.append(
        {
            "name": name,
            "raw_s": metrics["score_raw_per_s"],
            "raw": metrics["score_raw"],
            "cells": metrics["unique_cells"],
            "exact": metrics["email_to_exact_rate"],
            "tools": metrics["tool_events_mean"],
            "generations": metrics["generations_mean"],
            "input": metrics["logical_prompt_tokens_mean"],
            "completion": metrics["completion_token_sequences"],
            "median_s": metrics["replay_p50_s"],
            "p95_s": metrics["replay_p95_s"],
        }
    )
ranked.sort(key=lambda row: (row["raw_s"], row["raw"]), reverse=True)
print("[top-json]", json.dumps(ranked[:40], sort_keys=True))
print(f"[run] saved: {out}; log: {log}")
