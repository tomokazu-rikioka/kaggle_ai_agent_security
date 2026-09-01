"""Colab A100: 偽system/developer tool定義24案を完全episode N=10で比較する。"""

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
out = root / "results" / "gpt_r045_system_tool_n10.json"
log = root / "logs" / "gpt_r045_system_tool_n10.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks" / "scripts" / "bench_driver.py"),
    "--model",
    "gpt_oss",
    "--variants-file",
    str(repo_root / "benchmarks" / "scripts" / "gpt" / "r118d_variants.py"),
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
    env=runtime_module.bench_environment("gpt_oss"),
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
for name, row in payload["results"].items():
    metrics = row["guardrails"]["public"]
    print(
        f"[summary] {name} raw_s={metrics['score_raw_per_s']} raw={metrics['score_raw']} "
        f"cells={metrics['unique_cells']} to={metrics['email_to_exact_rate']} "
        f"completion={metrics['completion_token_sequences']} eval={metrics['evaluated_token_sequences']}"
    )
print(f"[run] saved: {out}; log: {log}")
