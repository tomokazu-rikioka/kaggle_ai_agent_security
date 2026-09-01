"""Colab A100: GPTのsent後即終了3系列をN=10で実生成する。"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

SERIES = {
    "a": ("r191a_sent_eos_natural_variants.py", "gpt_r191a_sent_eos_natural_n10"),
    "b": ("r191b_sent_history_variants.py", "gpt_r191b_sent_history_n10"),
    "c": ("r191c_sent_dsl_role_variants.py", "gpt_r191c_sent_dsl_role_n10"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series", choices=SERIES, required=True)
    args = parser.parse_args()

    runtime = importlib.reload(runtime_module)
    repo_root = runtime.REPO_ROOT
    root = runtime.ROOT
    variants_file, stem = SERIES[args.series]
    out = root / "results" / f"{stem}.json"
    log = root / "logs" / f"{stem}.log"
    out.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(repo_root / "benchmarks/scripts/bench_driver.py"),
        "--model",
        "gpt_oss",
        "--variants-file",
        str(repo_root / "benchmarks/scripts/gpt" / variants_file),
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
    print("[run]", " ".join(command))
    completed = subprocess.run(
        command,
        cwd=repo_root,
        env=runtime.bench_environment("gpt_oss"),
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

    payload = json.loads(out.read_text())
    summary = {}
    for name, row in payload["results"].items():
        metrics = row["guardrails"]["public"]
        completion = metrics["completion_token_sequences"]
        post_tool = []
        for sequence in completion:
            if ">" in sequence:
                post_tool.append(int(sequence.rsplit(">", 1)[-1]))
        summary[name] = {
            "input": row["sample_tokens"],
            "raw_s": metrics["score_raw_per_s"],
            "raw": metrics["score_raw"],
            "cells": metrics["unique_cells"],
            "to": metrics["email_to_exact_rate"],
            "completion": completion,
            "post_min": min(post_tool) if post_tool else None,
            "post_max": max(post_tool) if post_tool else None,
            "outputs": metrics["generation_text_sequences"],
        }
    print("[summary-json]", json.dumps(summary, sort_keys=True))
    print(f"[run] saved: {out}; log: {log}")


if __name__ == "__main__":
    main()
