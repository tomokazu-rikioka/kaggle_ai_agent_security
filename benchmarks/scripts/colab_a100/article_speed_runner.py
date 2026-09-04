"""記事用累積ベンチをColab A100で実行し、再現情報を結果へ付加する。"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

BASE_REPO_COMMIT = "e8a639bdc2d77b2f5d1da81d0a11fc3783cb8169"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _variant_metadata(path: Path) -> dict[str, object]:
    """測定に使ったrecipient bankと公開出典を結果JSONへ固定する。"""

    spec = importlib.util.spec_from_file_location("article_speed_variant_metadata", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load variants: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    recipients = tuple(module.RECIPIENTS)
    digest = hashlib.sha256("\n".join(recipients).encode("ascii")).hexdigest()
    expected_digest = getattr(module, "FIRST_PLACE_RECIPIENT_BANK_SHA256", digest)
    if digest != expected_digest:
        raise RuntimeError(f"Recipient bank SHA-256 mismatch: {digest} != {expected_digest}")
    return {
        "recipient_bank": {
            "source": getattr(module, "FIRST_PLACE_RECIPIENT_BANK_SOURCE", None),
            "variant": getattr(module, "FIRST_PLACE_RECIPIENT_BANK_VARIANT", None),
            "total_count": len(recipients),
            "unique_count": len(set(recipients)),
            "first": recipients[0],
            "last": recipients[-1],
            "sha256_newline_joined": digest,
        },
        "first_place_prompt_source": getattr(module, "FIRST_PLACE_PROMPT_SOURCE", None),
        "first_place_prompt_prefix_sha256": getattr(module, "FIRST_PLACE_PROMPT_PREFIX_SHA256", None),
    }


def _compact_summary(payload: dict[str, object]) -> dict[str, object]:
    """CLI履歴だけでも記事用の統計とプロンプトを復元できる要約を作る。"""

    results = payload["results"]
    assert isinstance(results, dict)
    compact_results: dict[str, object] = {}
    for variant, result_value in results.items():
        assert isinstance(result_value, dict)
        guardrails = result_value["guardrails"]
        assert isinstance(guardrails, dict)
        metrics = guardrails["public"]
        assert isinstance(metrics, dict)
        compact_results[str(variant)] = {
            "sample_message": result_value["sample_message"],
            "sample_message_count": result_value["sample_message_count"],
            "sample_len": result_value["sample_len"],
            "sample_tokens": result_value["sample_tokens"],
            "sample_recipient_common_prefix_tokens": result_value["sample_recipient_common_prefix_tokens"],
            "public": {
                key: metrics[key]
                for key in (
                    "candidate_raw_per_s_stats",
                    "score_raw_per_s",
                    "score_raw",
                    "fire_rate",
                    "email_to_exact_rate",
                    "replay_mean_s",
                    "replay_p50_s",
                    "replay_p95_s",
                    "replay_total_s",
                    "completion_tokens_mean",
                    "replay_error_count",
                )
            },
        }
    return {
        "model": payload["model"],
        "candidates_per_variant": payload["candidates_per_variant"],
        "result_complete": payload.get("result_complete"),
        "reuse_environment": payload.get("reuse_environment"),
        "benchmark_environment": payload["benchmark_environment"],
        "results": compact_results,
    }


def run(model: str, variants_relative: str, result_name: str, *, candidates: int = 2000) -> None:
    runtime = importlib.reload(runtime_module)
    repo_root = runtime.REPO_ROOT
    root = runtime.ROOT
    out = root / "results" / result_name
    log = root / "logs" / result_name.replace(".json", ".log")
    variants_path = repo_root / variants_relative
    driver_path = repo_root / "benchmarks/scripts/bench_driver.py"
    out.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)

    stop_heartbeat = threading.Event()

    def heartbeat() -> None:
        while not stop_heartbeat.wait(30):
            print(f"[run] heartbeat model={model} monotonic={time.monotonic():.0f}", flush=True)

    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    heartbeat_thread.start()
    try:
        command = [
            sys.executable,
            "-u",
            str(driver_path),
            "--model",
            model,
            "--variants-file",
            str(variants_path),
            "--candidates",
            str(candidates),
            "--guardrails",
            "public",
            "--warmup-candidates",
            "1",
            "--max-tool-hops",
            "8",
            "--reuse-env",
            "--out",
            str(out),
        ]
        print("[run]", " ".join(command), flush=True)
        with log.open("w", encoding="utf-8") as log_stream:
            process = subprocess.Popen(
                command,
                cwd=repo_root,
                env=runtime.bench_environment(model),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert process.stdout is not None
            for line in process.stdout:
                log_stream.write(line)
                if line.startswith(("[bench]", "[eval]", "[model]", "[progress]", "[checkpoint-summary]")):
                    print(line, end="", flush=True)
            returncode = process.wait()
        if returncode:
            raise subprocess.CalledProcessError(returncode, command)
    finally:
        stop_heartbeat.set()
        heartbeat_thread.join(timeout=2)

    payload = json.loads(out.read_text())
    payload["benchmark_environment"] = {
        "base_repo_commit": BASE_REPO_COMMIT,
        "bench_driver_sha256": _sha256(driver_path),
        "variants_sha256": _sha256(variants_path),
        "runtime": json.loads((root / "runtime.json").read_text()),
        "model_manifest": json.loads((root / "model_manifest.json").read_text())["models"][model],
        **_variant_metadata(variants_path),
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    summary = _compact_summary(payload)
    summary_path = out.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("[result-summary] " + json.dumps(summary, ensure_ascii=False, separators=(",", ":")), flush=True)
    print(f"[run] saved: {out}; summary: {summary_path}; log: {log}", flush=True)
