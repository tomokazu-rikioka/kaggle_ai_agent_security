"""Gemma recipient語彙探索をKaggle CPUでbuild/push/status/fetchする。"""

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
DRIVER = SCRIPT_DIR / "recipient_vocab.py"
BUILD_DIR = REPO_ROOT / "build" / "recipient_vocab"


def _kernel_id(round_tag: str) -> str:
    return f"{bev.KAGGLE_USER}/aas-gemma-recipient-vocabulary-{round_tag}"


def build(round_tag: str, top: int, profile: str) -> Path:
    out_dir = BUILD_DIR / round_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = bev.GGUF_PATHS["gemma_4"]
    run_cell = (
        "import json, os\n"
        f'os.environ["GEMMA_MODEL_PATH"] = "{model_path}"\n'
        f'assert os.path.exists("{model_path}")\n'
        "!python /kaggle/working/recipient_vocab.py "
        f"--top {top} --profile {profile} --out /kaggle/working/recipient_vocab.json\n"
        "print(json.dumps(json.load(open('/kaggle/working/recipient_vocab.json')), ensure_ascii=False)[:3000])\n"
    )
    notebook = nbf.v4.new_notebook()
    notebook.cells = [
        nbf.v4.new_markdown_cell(f"# Gemma recipient vocabulary search — {round_tag}"),
        nbf.v4.new_code_cell(
            "!pip -q install llama-cpp-python --extra-index-url "
            "https://abetlen.github.io/llama-cpp-python/whl/cpu\n"
            "import llama_cpp; print('llama_cpp CPU OK', llama_cpp.__version__)"
        ),
        nbf.v4.new_code_cell(
            bev._b64_write_cell("recipient_vocab.py", DRIVER.read_text(), "/kaggle/working/recipient_vocab.py")
        ),
        nbf.v4.new_code_cell(run_cell),
    ]
    notebook.metadata["kernelspec"] = {"name": "python3", "language": "python", "display_name": "Python 3"}
    nbf.write(notebook, str(out_dir / "search.ipynb"))
    metadata = {
        "id": _kernel_id(round_tag),
        "title": f"AAS Gemma recipient vocabulary {round_tag}",
        "code_file": "search.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": True,
        "dataset_sources": [],
        "kernel_sources": [],
        "competition_sources": [bev.COMPETITION],
        "model_sources": [bev.GGUF_MODEL_SOURCES["gemma_4"]],
    }
    (out_dir / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return out_dir


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "push", "status", "fetch"))
    parser.add_argument("--round", default="r31v")
    parser.add_argument("--top", type=int, default=10000)
    parser.add_argument(
        "--profile",
        choices=(
            "native",
            "ascii",
            "single_quote",
            "mixed_quotes",
            "mixed_delimiters",
            "extended",
            "extended_orders",
            "extended_all",
            "suffix",
        ),
        default="native",
    )
    args = parser.parse_args()
    kernel_id = _kernel_id(args.round)
    if args.action == "build":
        print(build(args.round, args.top, args.profile))
        return
    if args.action == "push":
        result = _run(
            ["kaggle", "kernels", "push", "-p", str(build(args.round, args.top, args.profile))]
        )
        print(result.stdout)
        if result.returncode or "successfully pushed" not in (result.stdout + result.stderr).lower():
            raise SystemExit(result.stderr or result.stdout)
        return
    if args.action == "status":
        print(_run(["kaggle", "kernels", "status", kernel_id]).stdout)
        return
    destination = SCRIPT_DIR / "gemma" / "results" / f"{args.round}_recipient_vocab.json"
    with tempfile.TemporaryDirectory(prefix=f"aas-recipient-vocab-{args.round}-") as temp_dir:
        result = _run(["kaggle", "kernels", "output", kernel_id, "-p", temp_dir])
        print(result.stdout)
        source = Path(temp_dir) / "recipient_vocab.json"
        if not source.is_file():
            raise SystemExit("recipient_vocab.jsonを回収できません")
        destination.write_text(source.read_text())
    print(destination)


if __name__ == "__main__":
    main()
