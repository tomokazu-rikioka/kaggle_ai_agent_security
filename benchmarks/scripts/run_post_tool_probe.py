"""Build, run, and fetch the GPT post-tool continuation probe on Kaggle."""

from __future__ import annotations

import argparse
import ast
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
DRIVER = SCRIPT_DIR / "post_tool_probe.py"
BUILD_DIR = REPO_ROOT / "build" / "post_tool_probe"


def _kernel_id(round_tag: str) -> str:
    return f"{bev.KAGGLE_USER}/aas-post-tool-probe-gpt-{round_tag}"


def _extra_variant_sources(variants: Path) -> dict[str, str]:
    """Bundle sibling modules explicitly declared by the variants module."""
    extra_names: tuple[str, ...] = ()
    for node in ast.parse(variants.read_text()).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "EXTRA_VARIANT_FILES" for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if not isinstance(value, tuple) or not all(isinstance(name, str) for name in value):
                raise TypeError("EXTRA_VARIANT_FILES must be a tuple of file names")
            extra_names = value
            break

    sources: dict[str, str] = {}
    for name in extra_names:
        if Path(name).name != name or not name.endswith(".py"):
            raise ValueError(f"invalid EXTRA_VARIANT_FILES entry: {name!r}")
        path = variants.parent / name
        if not path.is_file():
            raise FileNotFoundError(path)
        sources[name] = path.read_text()
    return sources


def build(round_tag: str, recipients: str) -> Path:
    variants = SCRIPT_DIR / "gpt" / f"{round_tag}_variants.py"
    for path in (bev.DRIVER_PATH, DRIVER, variants):
        if not Path(path).is_file():
            raise FileNotFoundError(path)
    out_dir = BUILD_DIR / round_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    guardrail_sources = {
        path.name: path.read_text() for path in sorted(Path(bev.GUARDRAILS_DIR).glob("*.py")) if path.is_file()
    }
    extra_variant_sources = _extra_variant_sources(variants)
    model_path = bev.GGUF_PATHS["gpt_oss"]
    path_env = bev.GGUF_PATH_ENVS["gpt_oss"]
    run_cell = (
        "import json, os\n"
        f'os.environ["{path_env}"] = "{model_path}"\n'
        f'assert os.path.exists("{model_path}")\n'
        "!python /kaggle/working/post_tool_probe.py "
        "--variants-file /kaggle/working/variants.py "
        f"--recipients {recipients} --out /kaggle/working/post_tool_probe.json\n"
        "print(json.dumps(json.load(open('/kaggle/working/post_tool_probe.json')), ensure_ascii=False)[:5000])\n"
    )
    notebook = nbf.v4.new_notebook()
    notebook.cells = [
        nbf.v4.new_markdown_cell(f"# GPT post-tool probe — {round_tag}"),
        nbf.v4.new_code_cell(bev._install_cell()),
        nbf.v4.new_code_cell(bev._sdk_cell()),
        nbf.v4.new_code_cell(
            bev._b64_write_cell("eval_driver.py", Path(bev.DRIVER_PATH).read_text(), "/kaggle/working/eval_driver.py")
        ),
        nbf.v4.new_code_cell(
            bev._b64_write_cell("post_tool_probe.py", DRIVER.read_text(), "/kaggle/working/post_tool_probe.py")
        ),
        nbf.v4.new_code_cell(bev._b64_write_cell("variants.py", variants.read_text(), "/kaggle/working/variants.py")),
        *[
            nbf.v4.new_code_cell(bev._b64_write_cell(name, source, f"/kaggle/working/{name}"))
            for name, source in extra_variant_sources.items()
        ],
        *[
            nbf.v4.new_code_cell(bev._b64_write_cell(name, source, f"/kaggle/working/guardrails/{name}"))
            for name, source in guardrail_sources.items()
        ],
        nbf.v4.new_code_cell(run_cell),
    ]
    notebook.metadata["kernelspec"] = {"name": "python3", "language": "python", "display_name": "Python 3"}
    nbf.write(notebook, str(out_dir / "probe.ipynb"))
    metadata = {
        "id": _kernel_id(round_tag),
        "title": f"AAS post-tool probe GPT {round_tag}",
        "code_file": "probe.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": True,
        "dataset_sources": [],
        "kernel_sources": [],
        "competition_sources": [bev.COMPETITION],
        "model_sources": [bev.GGUF_MODEL_SOURCES["gpt_oss"]],
        "machine_shape": bev.MACHINE_SHAPE,
    }
    (out_dir / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return out_dir


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "push", "status", "fetch"))
    parser.add_argument("--round", default="r40")
    parser.add_argument("--recipients", default="a,b,c,z,aa,ad")
    args = parser.parse_args()
    kernel_id = _kernel_id(args.round)
    if args.action == "build":
        print(build(args.round, args.recipients))
        return
    if args.action == "push":
        result = _run(["kaggle", "kernels", "push", "-p", str(build(args.round, args.recipients))])
        print(result.stdout)
        if result.returncode or "successfully pushed" not in (result.stdout + result.stderr).lower():
            raise SystemExit(result.stderr or result.stdout)
        return
    if args.action == "status":
        print(_run(["kaggle", "kernels", "status", kernel_id]).stdout)
        return
    destination = SCRIPT_DIR / "gpt" / "results" / f"{args.round}_post_tool_probe.json"
    with tempfile.TemporaryDirectory(prefix=f"aas-post-tool-{args.round}-") as temp_dir:
        result = _run(["kaggle", "kernels", "output", kernel_id, "-p", temp_dir])
        print(result.stdout)
        source = Path(temp_dir) / "post_tool_probe.json"
        if not source.is_file():
            raise SystemExit("post_tool_probe.jsonを回収できません")
        destination.write_text(source.read_text())
    print(destination)


if __name__ == "__main__":
    main()
