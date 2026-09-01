"""Colab A100: exp021の2,000候補を3回測り、平均応答時間順へ並べる。"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import statistics
import subprocess
import sys
from collections import defaultdict

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
sys.path.insert(0, "/content/aas")
import runtime as runtime_module  # noqa: E402

CONFIG = {
    "gpt_oss": (
        "gpt/r192_exp021_candidate_order_variants.py",
        "gpt_r192_exp021_candidate_order_n3",
    ),
    "gemma_4": (
        "gemma/r192_exp021_candidate_order_variants.py",
        "gemma_r192_exp021_candidate_order_n3",
    ),
}


def _load_module(path):
    spec = importlib.util.spec_from_file_location("_r192_variants", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=CONFIG, required=True)
    parser.add_argument(
        "--postprocess-only",
        action="store_true",
        help="保存済みraw JSONから順位だけを再生成する",
    )
    args = parser.parse_args()

    runtime = importlib.reload(runtime_module)
    repo_root = runtime.REPO_ROOT
    root = runtime.ROOT
    relative_variants, stem = CONFIG[args.model]
    variants_path = repo_root / "benchmarks/scripts" / relative_variants
    raw_out = root / "results" / f"{stem}_raw.json"
    ranked_out = root / "results" / f"{stem}_ranked.json"
    log = root / "logs" / f"{stem}.log"
    raw_out.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        str(repo_root / "benchmarks/scripts/bench_driver.py"),
        "--model",
        args.model,
        "--variants-file",
        str(variants_path),
        "--candidates",
        "2001",
        "--guardrails",
        "public",
        "--warmup-candidates",
        "0",
        "--max-tool-hops",
        "8",
        "--out",
        str(raw_out),
    ]
    if not args.postprocess_only:
        print("[run]", " ".join(command), flush=True)
        with log.open("w") as stream:
            process = subprocess.Popen(
                command,
                cwd=repo_root,
                env=runtime.bench_environment(args.model),
                stdout=stream,
                stderr=subprocess.STDOUT,
                text=True,
            )
            returncode = process.wait()
        if returncode:
            print(log.read_text()[-8_000:], file=sys.stderr)
            raise subprocess.CalledProcessError(returncode, command)
    elif not raw_out.is_file():
        raise FileNotFoundError(f"raw result not found: {raw_out}")

    payload = json.loads(raw_out.read_text())
    module = _load_module(variants_path)
    samples: dict[str, list[dict[str, object]]] = defaultdict(list)
    run_summary = {}
    for order_name, order in module.ORDERS.items():
        metrics = payload["results"][order_name]["guardrails"]["public"]
        times = metrics["replay_seconds"]
        diagnostics = metrics["recipient_diagnostics"]
        if not (len(times) == len(diagnostics) == len(order)):
            raise RuntimeError(f"unexpected row count for {order_name}")
        for index in range(1, len(order)):
            recipient = order[index]
            diagnostic = diagnostics[index]
            samples[recipient].append(
                {
                    "order": order_name,
                    "seconds": times[index],
                    "completion_tokens": diagnostic["completion_tokens"],
                    "tool_sequence": diagnostic["tool_sequence"],
                    "email_to_exact": diagnostic["email_to_exact"],
                    "fire": diagnostic["fire"],
                }
            )
        run_summary[order_name] = {
            "total_s": metrics["replay_total_s"],
            "mean_s": metrics["replay_mean_s"],
            "raw_s": metrics["score_raw_per_s"],
            "raw": metrics["score_raw"],
            "cells": metrics["unique_cells"],
            "to_exact": metrics["email_to_exact_rate"],
            "completion": metrics["completion_token_sequences"],
        }

    ranked = []
    for original_index, recipient in enumerate(module.BASE_RECIPIENTS):
        rows = samples[recipient]
        if len(rows) != 3:
            raise RuntimeError(f"{recipient}: expected 3 measurements, got {len(rows)}")
        seconds = [float(row["seconds"]) for row in rows]
        stable = all(
            row["email_to_exact"] is True and row["fire"] is True and row["tool_sequence"] == "email.send"
            for row in rows
        )
        ranked.append(
            {
                "recipient": recipient,
                "original_index": original_index,
                "mean_s": round(statistics.fmean(seconds), 6),
                "median_s": round(statistics.median(seconds), 6),
                "min_s": round(min(seconds), 6),
                "max_s": round(max(seconds), 6),
                "stable": stable,
                "measurements": rows,
            }
        )

    fastest_response = sorted(ranked, key=lambda row: (row["mean_s"], row["recipient"]))
    recommended = sorted(ranked, key=lambda row: (not row["stable"], row["mean_s"], row["recipient"]))
    for index, row in enumerate(fastest_response, start=1):
        row["speed_rank"] = index
    speed_rank = {row["recipient"]: row["speed_rank"] for row in fastest_response}
    for index, row in enumerate(recommended, start=1):
        row["recommended_rank"] = index
        row["speed_rank"] = speed_rank[row["recipient"]]

    result = {
        "model": args.model,
        "source": "experiments/exp021/attack.py",
        "recipients": len(ranked),
        "measurements_per_recipient": 3,
        "measurement_orders": list(module.ORDERS),
        "run_summary": run_summary,
        "stable_recipients": sum(bool(row["stable"]) for row in ranked),
        "fastest_response_order": [row["recipient"] for row in fastest_response],
        "recommended_order": [row["recipient"] for row in recommended],
        "ranked": recommended,
    }
    ranked_out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    compact_result = {
        key: value
        for key, value in result.items()
        if key not in {"ranked", "fastest_response_order", "recommended_order"}
    }
    print("[summary]", json.dumps(compact_result), flush=True)
    print("[top20]", json.dumps(recommended[:20], ensure_ascii=False), flush=True)
    print(f"[run] saved: {raw_out}; ranked: {ranked_out}; log: {log}", flush=True)


if __name__ == "__main__":
    main()
