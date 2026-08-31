"""token_probe.pyをKaggle T4でbuild/push/status/fetchする。"""

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
DRIVER = SCRIPT_DIR / "token_probe.py"
BUILD_DIR = REPO_ROOT / "build" / "token_probe"
TRACK_MODEL = {"gpt": "gpt_oss", "gemma": "gemma_4"}


def _extra_candidate_sources(candidates_path: Path) -> dict[str, str]:
    """Bundle sibling modules explicitly declared by a candidate module."""
    extra_names: tuple[str, ...] = ()
    for node in ast.parse(candidates_path.read_text()).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "EXTRA_CANDIDATE_FILES" for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if not isinstance(value, tuple) or not all(isinstance(name, str) for name in value):
                raise TypeError("EXTRA_CANDIDATE_FILES must be a tuple of file names")
            extra_names = value
            break

    sources: dict[str, str] = {}
    for name in extra_names:
        if Path(name).name != name or not name.endswith(".py"):
            raise ValueError(f"invalid EXTRA_CANDIDATE_FILES entry: {name!r}")
        path = candidates_path.parent / name
        if not path.is_file():
            raise FileNotFoundError(path)
        sources[name] = path.read_text()
    return sources


def _kernel_id(track: str, round_tag: str) -> str:
    return f"{bev.KAGGLE_USER}/aas-token-probe-{track}-{round_tag}"


def build(
    track: str,
    round_tag: str,
    *,
    target_tokens: int,
    preview_tokens: int,
    validation_recipients: str,
    prune_primary_miss: bool,
    prune_primary_output_miss: bool,
    skip_target_likelihood: bool = False,
) -> Path:
    model = TRACK_MODEL[track]
    candidates_path = SCRIPT_DIR / track / f"{round_tag}_candidates.py"
    for path in (bev.DRIVER_PATH, DRIVER, candidates_path):
        if not Path(path).is_file():
            raise FileNotFoundError(path)

    out_dir = BUILD_DIR / track / round_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    guardrail_sources = {
        path.name: path.read_text() for path in sorted(Path(bev.GUARDRAILS_DIR).glob("*.py")) if path.is_file()
    }
    extra_candidate_sources = _extra_candidate_sources(candidates_path)
    model_path = bev.GGUF_PATHS[model]
    path_env = bev.GGUF_PATH_ENVS[model]
    prune_flag = " --prune-primary-miss" if prune_primary_miss else ""
    prune_output_flag = " --prune-primary-output-miss" if prune_primary_output_miss else ""
    skip_likelihood_flag = " --skip-target-likelihood" if skip_target_likelihood else ""
    run_cell = (
        "import json, os\n"
        f'os.environ["{path_env}"] = "{model_path}"\n'
        f'assert os.path.exists("{model_path}")\n'
        "!python /kaggle/working/token_probe.py \\\n"
        "    --candidates-file /kaggle/working/candidates.py \\\n"
        f"    --model {model} --target-tokens {target_tokens} --preview-tokens {preview_tokens} \\\n"
        f"    --validation-recipients {validation_recipients}{prune_flag}{prune_output_flag}{skip_likelihood_flag} \\\n"
        "    --out /kaggle/working/token_probe_results.json\n"
        "_probe_result = json.load(open('/kaggle/working/token_probe_results.json'))\n"
        "print(json.dumps({\n"
        "    'model': _probe_result.get('model'),\n"
        "    'baseline': _probe_result.get('baseline'),\n"
        "    'result_count': len(_probe_result.get('results', {})),\n"
        "}, ensure_ascii=False, indent=2))\n"
    )
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell(f"# token probe — {track} {round_tag}"),
        nbf.v4.new_code_cell(bev._install_cell()),
        nbf.v4.new_code_cell(bev._sdk_cell()),
        nbf.v4.new_code_cell(
            bev._b64_write_cell("eval_driver.py", Path(bev.DRIVER_PATH).read_text(), "/kaggle/working/eval_driver.py")
        ),
        nbf.v4.new_code_cell(
            bev._b64_write_cell("token_probe.py", DRIVER.read_text(), "/kaggle/working/token_probe.py")
        ),
        nbf.v4.new_code_cell(
            bev._b64_write_cell("candidates.py", candidates_path.read_text(), "/kaggle/working/candidates.py")
        ),
        *[
            nbf.v4.new_code_cell(bev._b64_write_cell(name, source, f"/kaggle/working/{name}"))
            for name, source in extra_candidate_sources.items()
        ],
        *[
            nbf.v4.new_code_cell(bev._b64_write_cell(f"guardrail {name}", source, f"/kaggle/working/guardrails/{name}"))
            for name, source in guardrail_sources.items()
        ],
        nbf.v4.new_code_cell(run_cell),
    ]
    nb.metadata["kernelspec"] = {"name": "python3", "language": "python", "display_name": "Python 3"}
    nb.metadata["language_info"] = {"name": "python"}
    nbf.write(nb, str(out_dir / "probe.ipynb"))
    metadata = {
        "id": _kernel_id(track, round_tag),
        "title": f"AAS token probe {track} {round_tag}",
        "code_file": "probe.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": True,
        "keywords": [],
        "dataset_sources": [],
        "kernel_sources": [],
        "competition_sources": [bev.COMPETITION],
        "model_sources": [bev.GGUF_MODEL_SOURCES[model]],
        "machine_shape": bev.MACHINE_SHAPE,
    }
    (out_dir / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"[probe] build {out_dir} id={metadata['id']}")
    return out_dir


def _run(command: list[str]) -> subprocess.CompletedProcess:
    print(f"[probe] $ {' '.join(command)}")
    return subprocess.run(command, check=False, capture_output=True, text=True)


def push(
    track: str,
    round_tag: str,
    *,
    target_tokens: int,
    preview_tokens: int,
    validation_recipients: str,
    prune_primary_miss: bool,
    prune_primary_output_miss: bool,
    skip_target_likelihood: bool = False,
) -> None:
    out_dir = build(
        track,
        round_tag,
        target_tokens=target_tokens,
        preview_tokens=preview_tokens,
        validation_recipients=validation_recipients,
        prune_primary_miss=prune_primary_miss,
        prune_primary_output_miss=prune_primary_output_miss,
        skip_target_likelihood=skip_target_likelihood,
    )
    result = _run(["kaggle", "kernels", "push", "-p", str(out_dir)])
    print(result.stdout)
    if result.returncode != 0 or "successfully pushed" not in (result.stdout + result.stderr).lower():
        raise SystemExit(result.stderr or result.stdout)


def status(track: str, round_tag: str) -> None:
    result = _run(["kaggle", "kernels", "status", _kernel_id(track, round_tag)])
    print(result.stdout)


def fetch(track: str, round_tag: str) -> None:
    result_dir = SCRIPT_DIR / track / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"aas-token-probe-{track}-{round_tag}-") as temp_dir:
        result = _run(["kaggle", "kernels", "output", _kernel_id(track, round_tag), "-p", temp_dir])
        print(result.stdout)
        source = Path(temp_dir) / "token_probe_results.json"
        if not source.is_file():
            raise SystemExit("token_probe_results.jsonを回収できません")
        destination = result_dir / f"{round_tag}_token_probe.json"
        destination.write_text(source.read_text())
    print(f"[probe] fetched {destination}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["build", "push", "status", "fetch"])
    ap.add_argument("--track", choices=["gpt", "gemma"], required=True)
    ap.add_argument("--round", default="r13")
    ap.add_argument("--target-tokens", type=int, default=48)
    ap.add_argument("--preview-tokens", type=int, default=64)
    ap.add_argument("--validation-recipients", default="a,b,c,z,aa,ad")
    ap.add_argument("--prune-primary-miss", action="store_true")
    ap.add_argument("--prune-primary-output-miss", action="store_true")
    ap.add_argument("--skip-target-likelihood", action="store_true")
    args = ap.parse_args()
    kwargs = {
        "target_tokens": args.target_tokens,
        "preview_tokens": args.preview_tokens,
        "validation_recipients": args.validation_recipients,
        "prune_primary_miss": args.prune_primary_miss,
        "prune_primary_output_miss": args.prune_primary_output_miss,
        "skip_target_likelihood": args.skip_target_likelihood,
    }
    if args.action == "build":
        build(args.track, args.round, **kwargs)
    elif args.action == "push":
        push(args.track, args.round, **kwargs)
    elif args.action == "status":
        status(args.track, args.round)
    else:
        fetch(args.track, args.round)


if __name__ == "__main__":
    main()
