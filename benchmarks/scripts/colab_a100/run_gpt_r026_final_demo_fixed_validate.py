"""Colab A100: r024の42–43 token成功案を11 recipientで検証する。"""

from __future__ import annotations

import importlib
import subprocess
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
repo_root = runtime_module.REPO_ROOT
root = runtime_module.ROOT
out = root / "results" / "gpt_r026_final_demo_fixed_validate.json"
log = root / "logs" / "gpt_r026_final_demo_fixed_validate.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks" / "scripts" / "token_probe.py"),
    "--model",
    "gpt_oss",
    "--candidates-file",
    str(repo_root / "benchmarks" / "scripts" / "gpt" / "r113b_candidates.py"),
    "--recipient",
    "a",
    "--validation-recipients",
    "a,s,x,ilh,for,nt,abt,acf,acu,csr,fix",
    "--preview-tokens",
    "32",
    "--target-tokens",
    "32",
    "--prune-primary-miss",
    "--skip-target-likelihood",
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
summary = [line for line in completed.stdout.splitlines() if line.startswith("[probe]")]
print(f"[run] probe rows={len(summary)}")
for line in summary:
    print(line)
if completed.returncode:
    print(completed.stderr[-8_000:], file=sys.stderr)
completed.check_returncode()
print(f"[run] saved: {out}; log: {log}")
