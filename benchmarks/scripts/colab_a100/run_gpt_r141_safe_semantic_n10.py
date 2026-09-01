"""Colab A100: first-call screen of normalization-safe semantic prompts."""

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
out = root / "results/gpt_r141_safe_semantic_n10.json"
log = root / "logs/gpt_r141_safe_semantic_n10.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks/scripts/bench_driver.py"),
    "--model", "gpt_oss",
    "--variants-file", str(repo_root / "benchmarks/scripts/gpt/r141_safe_semantic_variants.py"),
    "--candidates", "10",
    "--guardrails", "public",
    "--warmup-candidates", "1",
    "--max-tool-hops", "1",
    "--out", str(out),
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
    ranked.append({
        "name": name,
        "raw_s": metrics["score_raw_per_s"],
        "raw": metrics["score_raw"],
        "cells": metrics["unique_cells"],
        "exact": metrics["email_to_exact_rate"],
        "tools": metrics["tool_events_mean"],
        "input": metrics["logical_prompt_tokens_mean"],
        "completion": metrics["completion_token_sequences"],
    })
ranked.sort(key=lambda row: (row["raw_s"], row["raw"]), reverse=True)
print("[top-json]", json.dumps(ranked[:30], sort_keys=True))
print(f"[run] saved: {out}; log: {log}")
