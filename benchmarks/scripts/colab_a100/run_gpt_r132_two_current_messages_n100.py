"""Colab A100: compare current one-hop with two identical messages at N=100 ABBA."""

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
out = root / "results/gpt_r132_two_current_messages_n100.json"
log = root / "logs/gpt_r132_two_current_messages_n100.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks/scripts/bench_driver.py"),
    "--model",
    "gpt_oss",
    "--variants-file",
    str(repo_root / "benchmarks/scripts/gpt/r132_two_current_messages_variants.py"),
    "--candidates",
    "100",
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
summary = {}
for name, row in payload["results"].items():
    metrics = row["guardrails"]["public"]
    times = metrics["replay_seconds"]
    summary[name] = {
        "raw_s": metrics["score_raw_per_s"],
        "raw": metrics["score_raw"],
        "cells": metrics["unique_cells"],
        "exact": metrics["email_to_exact_rate"],
        "tools": metrics["tool_events_mean"],
        "generations": metrics["generations_mean"],
        "completion": metrics["completion_token_sequences"],
        "min_s": min(times),
        "median_s": metrics["replay_p50_s"],
        "max_s": max(times),
    }
print("[summary-json]", json.dumps(summary, sort_keys=True))
print(f"[run] saved: {out}; log: {log}")
