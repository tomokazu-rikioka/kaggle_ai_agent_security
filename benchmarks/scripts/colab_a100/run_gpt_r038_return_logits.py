"""Colab A100: r111a全候補のtool成功直後におけるreturn token順位を直接測る。"""

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
out = root / "results" / "gpt_r038_return_logits.json"
log = root / "logs" / "gpt_r038_return_logits.log"
out.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
command = [
    sys.executable,
    str(repo_root / "benchmarks" / "scripts" / "gpt_return_logit_probe.py"),
    "--variants-file",
    str(repo_root / "benchmarks" / "scripts" / "gpt" / "r111a_candidates.py"),
    "--recipients",
    "a",
    "--top-k",
    "12",
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
    print(completed.stdout[-8_000:])
    print(completed.stderr[-8_000:], file=sys.stderr)
completed.check_returncode()
payload = json.loads(out.read_text())
ranked = sorted(
    payload["results"].items(),
    key=lambda item: (item[1]["return_rank_max"], -item[1]["return_logp_mean"]),
)
for name, row in ranked[:20]:
    print(
        f"[return-top] {name:16} tok={row['message_tokens']:3} "
        f"rank={row['return_rank_max']:6} logp={row['return_logp_mean']:.4f}"
    )
print(f"[run] saved: {out}; log: {log}")
