"""Colab A100: sent履歴条件×終了動作216組をN=2でscreenする。"""

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
out = root / "results/gemma_r189_sent_history_cross_n2.json"
log = root / "logs/gemma_r189_sent_history_cross_n2.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks/scripts/bench_driver.py"),
    "--model",
    "gemma_4",
    "--variants-file",
    str(repo_root / "benchmarks/scripts/gemma/r189_sent_history_cross_variants.py"),
    "--candidates",
    "2",
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
short = {}
for name, row in payload["results"].items():
    metrics = row["guardrails"]["public"]
    completions = metrics["completion_token_sequences"]
    if any(
        ">" in sequence and int(sequence.rsplit(">", 1)[1]) < 4
        for sequence in completions
    ):
        short[name] = {
            "message": row["sample_message"],
            "raw": metrics["score_raw"],
            "cells": metrics["unique_cells"],
            "to": metrics["email_to_exact_rate"],
            "completion": completions,
            "outputs": metrics["generation_text_sequences"],
        }
print("[short-json]", json.dumps(short, sort_keys=True))
print(f"[run] variants={len(payload['results'])}; shortened={len(short)}; saved={out}; log={log}")
