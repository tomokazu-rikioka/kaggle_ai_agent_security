"""ベンチ用 Kaggle カーネルの build / push / status / fetch を 1 コマンドで回す。

1 トラック（gpt or gemma）= 1 カーネル。モデルを 1 回だけロードして、そのトラックの
`variants_<track>.py` が定義する全変種の発火率・候補速度を計測する（bench_driver.py）。
GPT と Gemma は別カーネルなので 2 枠並列で同時に走らせられる。

再利用: 評価ノートブックのセル（依存導入・SDK 解決・base64 復元）は
`scripts/ops/build_eval_notebook.py` の関数をそのまま使う（提出/評価と同じ土台で焼く）。

ラウンド（r1, r2, ...）で順番が分かるように、変種ファイル・カーネル id・結果ファイルを
すべて `--round` でタグ付けする。変種ファイルは `benchmarks/scripts/<track>/<round>_variants.py`。

使い方（リポジトリ直下から）:
    uv run python benchmarks/scripts/run_bench.py push  --track gpt   --round r1 --candidates 30
    uv run python benchmarks/scripts/run_bench.py push  --track gemma --round r1 --candidates 30
    uv run python benchmarks/scripts/run_bench.py status --track gpt --round r1
    uv run python benchmarks/scripts/run_bench.py fetch  --track gpt --round r1
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import nbformat as nbf

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "ops"))

import build_eval_notebook as bev  # noqa: E402  （依存導入・SDK 解決・base64 セルを再利用）

BENCH_DIR = REPO_ROOT / "benchmarks" / "scripts"
BUILD_DIR = REPO_ROOT / "build" / "bench"
BENCH_DRIVER = BENCH_DIR / "bench_driver.py"

TRACK_MODEL = {"gpt": "gpt_oss", "gemma": "gemma_4"}


def _variants_path(track: str, round_tag: str) -> Path:
    return BENCH_DIR / track / f"{round_tag}_variants.py"


def _kernel_id(track: str, round_tag: str) -> str:
    return f"{bev.KAGGLE_USER}/aas-bench-{track}-{round_tag}"


def _b64_cell(comment: str, src: str, dest: str) -> str:
    return bev._b64_write_cell(comment, src, dest)


def _bench_run_cell(track: str, candidates: int, budget_s: float, guardrails: str) -> str:
    model = TRACK_MODEL[track]
    gguf_path = bev.GGUF_PATHS[model]
    path_env = bev.GGUF_PATH_ENVS[model]
    return (
        "import json, os\n"
        f'os.environ["{path_env}"] = "{gguf_path}"  # Kaggle Models 添付の GGUF（HF hub DL 回避）\n'
        f'assert os.path.exists("{gguf_path}"), "GGUF 未添付?: {gguf_path}"\n'
        f'print("GGUF:", "{gguf_path}")\n'
        "!python /kaggle/working/bench_driver.py \\\n"
        "    --variants-file /kaggle/working/variants.py \\\n"
        f"    --model {model} --candidates {candidates} --guardrails {guardrails} \\\n"
        f"    --budget-s {int(budget_s)} --out /kaggle/working/bench_results.json\n"
        "print('--- bench_results.json ---')\n"
        "print(json.dumps(json.load(open('/kaggle/working/bench_results.json')), ensure_ascii=False, indent=2))\n"
    )


def build(track: str, round_tag: str, *, candidates: int, budget_s: float, guardrails: str) -> Path:
    if track not in TRACK_MODEL:
        raise ValueError(f"未知の track '{track}'（gpt|gemma）")
    model = TRACK_MODEL[track]
    variants_path = _variants_path(track, round_tag)
    for p in (bev.DRIVER_PATH, BENCH_DRIVER, variants_path):
        if not Path(p).is_file():
            raise FileNotFoundError(f"必要ファイルが無い: {p}")

    driver_src = Path(bev.DRIVER_PATH).read_text()
    bench_src = BENCH_DRIVER.read_text()
    variants_src = variants_path.read_text()
    guardrail_sources = {
        p.name: p.read_text() for p in sorted(Path(bev.GUARDRAILS_DIR).glob("*.py")) if p.is_file()
    }

    out_dir = BUILD_DIR / track / round_tag
    out_dir.mkdir(parents=True, exist_ok=True)

    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell(
            f"# bench — {track} {round_tag} ({model})\n\n"
            f"`{round_tag}_variants.py` の全変種を **{model}** で `{guardrails}` へリプレイし、"
            f"発火率(findings/N)と候補速度(replay_mean_s)を計測（N={candidates}）。モデルロードは 1 回。"
        ),
        nbf.v4.new_markdown_cell("## ① 依存"),
        nbf.v4.new_code_cell(bev._install_cell()),
        nbf.v4.new_markdown_cell("## ② SDK 解決"),
        nbf.v4.new_code_cell(bev._sdk_cell()),
        nbf.v4.new_markdown_cell("## ③ driver / bench_driver / variants / guardrails 復元"),
        nbf.v4.new_code_cell(_b64_cell("eval_driver.py", driver_src, "/kaggle/working/eval_driver.py")),
        nbf.v4.new_code_cell(_b64_cell("bench_driver.py", bench_src, "/kaggle/working/bench_driver.py")),
        nbf.v4.new_code_cell(_b64_cell("variants.py", variants_src, "/kaggle/working/variants.py")),
        *[
            nbf.v4.new_code_cell(_b64_cell(f"guardrail {name}", src, f"/kaggle/working/guardrails/{name}"))
            for name, src in guardrail_sources.items()
        ],
        nbf.v4.new_markdown_cell(f"## ④ 計測（{model}）→ bench_results.json"),
        nbf.v4.new_code_cell(_bench_run_cell(track, candidates, budget_s, guardrails)),
    ]
    nb.metadata["kernelspec"] = {"name": "python3", "language": "python", "display_name": "Python 3"}
    nb.metadata["language_info"] = {"name": "python"}
    nb_path = out_dir / "bench.ipynb"
    nbf.write(nb, str(nb_path))

    km = {
        "id": _kernel_id(track, round_tag),
        "title": f"AAS bench {track} {round_tag}",
        "code_file": "bench.ipynb",
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
    (out_dir / "kernel-metadata.json").write_text(json.dumps(km, indent=2) + "\n")
    print(f"[bench] build: {nb_path} (id={km['id']}, variants={variants_path.name})")
    return out_dir


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    print(f"[bench] $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def push(track: str, round_tag: str, **kw) -> None:
    out_dir = build(track, round_tag, **kw)
    res = _run(["kaggle", "kernels", "push", "-p", str(out_dir)])
    sys.stdout.write(res.stdout)
    sys.stderr.write(res.stderr)
    # kaggle CLI は失敗しても exit 0 で stdout に "error" を出すことがある（GPU 枠不足など）。
    # "successfully pushed" が無ければ失敗扱いにする（2 枠上限や一時失敗を握り潰さない）。
    combined = (res.stdout + res.stderr).lower()
    if res.returncode != 0 or "successfully pushed" not in combined:
        raise SystemExit(f"push 失敗（GPU 枠上限や一時失敗の可能性）: {out_dir}")
    print(f"[bench] pushed {_kernel_id(track, round_tag)} — status で監視、complete 後に fetch")


def status(track: str, round_tag: str) -> None:
    res = _run(["kaggle", "kernels", "status", _kernel_id(track, round_tag)])
    sys.stdout.write(res.stdout)
    sys.stderr.write(res.stderr)


def fetch(track: str, round_tag: str) -> None:
    kid = _kernel_id(track, round_tag)
    dest = BENCH_DIR / track / "results"
    dest.mkdir(parents=True, exist_ok=True)
    res = _run(["kaggle", "kernels", "output", kid, "-p", str(dest)])
    sys.stdout.write(res.stdout)
    src = dest / "bench_results.json"
    if not src.is_file():
        sys.stderr.write(f"[bench] bench_results.json を回収できず（まだ complete でない?）: {dest}\n")
        raise SystemExit(1)
    tagged = dest / f"{round_tag}.json"
    tagged.write_text(src.read_text())
    src.unlink()  # タグ無しの生成物は消してラウンドタグ付きだけ残す
    print(f"[bench] fetched → {tagged}")
    data = json.loads(tagged.read_text())
    _print_table(track, data)


def _print_table(track: str, data: dict) -> None:
    print("\n" + "=" * 92)
    print(f"bench {track} — model={data.get('model')} N={data.get('candidates_per_variant')}")
    print("=" * 92)
    print(
        f"{'variant':22} {'guard':8} {'fire':>6} {'emit_ok':>8} {'emit_any':>9} "
        f"{'mean_s':>7} {'raw':>8} {'cells':>6} {'len':>5}"
    )
    print("-" * 92)
    for vname, v in data.get("results", {}).items():
        slen = v.get("sample_len", "")
        for gname, g in v.get("guardrails", {}).items():
            print(
                f"{vname:22} {gname:8} {g['fire_rate']:>6.3f} {g.get('emit_ok_rate', 0):>8.3f} "
                f"{g.get('emit_any_rate', 0):>9.3f} {g['replay_mean_s']:>7.2f} "
                f"{g['score_raw']:>8.1f} {g['unique_cells']:>6} {slen:>5}"
            )
    print("=" * 92)


def main() -> None:
    ap = argparse.ArgumentParser(description="ベンチ用 Kaggle カーネルの build/push/status/fetch")
    ap.add_argument("action", choices=["build", "push", "status", "fetch"])
    ap.add_argument("--track", required=True, choices=["gpt", "gemma"])
    ap.add_argument("--round", default="r1", help="ラウンドタグ（r1, r2, ...）。変種ファイル/カーネル/結果に付く")
    ap.add_argument("--candidates", type=int, default=30)
    ap.add_argument("--budget-s", type=float, default=8000.0)
    ap.add_argument("--guardrails", default="public,private")
    args = ap.parse_args()

    kw = dict(candidates=args.candidates, budget_s=args.budget_s, guardrails=args.guardrails)
    if args.action == "build":
        build(args.track, args.round, **kw)
    elif args.action == "push":
        push(args.track, args.round, **kw)
    elif args.action == "status":
        status(args.track, args.round)
    elif args.action == "fetch":
        fetch(args.track, args.round)


if __name__ == "__main__":
    main()
