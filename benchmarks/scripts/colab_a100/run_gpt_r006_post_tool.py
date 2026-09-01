"""Colab A100: suffix固定値除去案のtool後finalを失敗recipient込みで確認する。"""

from __future__ import annotations

import importlib
import subprocess
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
repo_root = runtime_module.REPO_ROOT
root = runtime_module.ROOT
out = root / "results" / "gpt_r006_post_tool.json"
log = root / "logs" / "gpt_r006_post_tool.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks" / "scripts" / "post_tool_probe.py"),
    "--variants-file",
    str(repo_root / "benchmarks" / "scripts" / "gpt" / "r103a_variants.py"),
    "--recipients",
    "a,s,x,ilh,for,nt,abt,acf,acu,csr,fix",
    "--max-new-tokens",
    "32",
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
    if line.startswith("[post]"):
        print(line)
if completed.returncode:
    print(completed.stderr[-8_000:], file=sys.stderr)
completed.check_returncode()
print(f"[run] saved: {out}; log: {log}")
