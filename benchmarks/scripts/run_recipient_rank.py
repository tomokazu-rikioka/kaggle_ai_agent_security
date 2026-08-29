"""recipient_rank.pyをKaggleでbuild/push/status/fetchする。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import nbformat as nbf

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "ops"))

import build_eval_notebook as bev  # noqa: E402

SCRIPT_DIR = REPO_ROOT / "benchmarks" / "scripts"
DRIVER = SCRIPT_DIR / "recipient_rank.py"
BUILD_DIR = REPO_ROOT / "build" / "recipient_rank"
TRACK_MODEL = {"gpt": "gpt_oss", "gemma": "gemma_4"}


def _kernel_id(track: str) -> str:
    return f"{bev.KAGGLE_USER}/aas-recipient-rank-{track}-r20"


def build(track: str) -> Path:
    model = TRACK_MODEL[track]
    out_dir = BUILD_DIR / track / "r20"
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = bev.GGUF_PATHS[model]
    path_env = bev.GGUF_PATH_ENVS[model]
    run_cell = (
        "import json, os\n"
        f'os.environ["{path_env}"] = "{model_path}"\n'
        "!python /kaggle/working/recipient_rank.py "
        f"--track {track} --out /kaggle/working/recipient_rank.json\n"
        "print(json.dumps(json.load(open('/kaggle/working/recipient_rank.json')), ensure_ascii=False)[:2000])\n"
    )
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell(f"# recipient rank — {track} r20"),
        nbf.v4.new_code_cell(bev._install_cell()),
        nbf.v4.new_code_cell(
            bev._b64_write_cell("recipient_rank.py", DRIVER.read_text(), "/kaggle/working/recipient_rank.py")
        ),
        nbf.v4.new_code_cell(run_cell),
    ]
    nb.metadata["kernelspec"] = {"name": "python3", "language": "python", "display_name": "Python 3"}
    nbf.write(nb, str(out_dir / "rank.ipynb"))
    metadata = {
        "id": _kernel_id(track),
        "title": f"AAS recipient rank {track} r20",
        "code_file": "rank.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": True,
        "dataset_sources": [],
        "kernel_sources": [],
        "competition_sources": [bev.COMPETITION],
        "model_sources": [bev.GGUF_MODEL_SOURCES[model]],
        "machine_shape": bev.MACHINE_SHAPE,
    }
    (out_dir / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return out_dir


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("build", "push", "status", "fetch"))
    ap.add_argument("--track", choices=("gpt", "gemma"), required=True)
    args = ap.parse_args()
    if args.action == "build":
        print(build(args.track))
        return
    kernel_id = _kernel_id(args.track)
    if args.action == "push":
        result = _run(["kaggle", "kernels", "push", "-p", str(build(args.track))])
        print(result.stdout)
        if result.returncode or "successfully pushed" not in (result.stdout + result.stderr).lower():
            raise SystemExit(result.stderr or result.stdout)
        return
    if args.action == "status":
        print(_run(["kaggle", "kernels", "status", kernel_id]).stdout)
        return
    destination = SCRIPT_DIR / args.track / "results" / "r20_recipient_rank.json"
    with tempfile.TemporaryDirectory(prefix=f"aas-recipient-rank-{args.track}-") as temp_dir:
        result = _run(["kaggle", "kernels", "output", kernel_id, "-p", temp_dir])
        print(result.stdout)
        source = Path(temp_dir) / "recipient_rank.json"
        if not source.is_file():
            raise SystemExit("recipient_rank.jsonを回収できません")
        destination.write_text(source.read_text())
    print(destination)


if __name__ == "__main__":
    main()
