"""評価用 Kaggle Notebook（eval.ipynb）と kernel-metadata.json を生成する。

Kaggle GPU 上で attack.py を実モデル（gpt_oss / gemma_4）でローカル採点するための薄い Notebook を
組み立てる。Notebook は次を行うだけ:
  1) 依存導入（CUDA 版 llama-cpp-python ほか）
  2) Add Input した SDK dataset を /tmp へ展開し sys.path 解決の準備
  3) attack.py と eval_driver.py を base64 で /kaggle/working へ復元
  4) eval_driver.py を実行して /kaggle/working/scores.json（1 モデル分）を書き出す

採点ロジックは scripts/eval/eval_driver.py（自己完結）に集約済み。本スクリプトは attack.py と
eval_driver.py を **base64 で 1 セルに焼く**（`'''` や任意バイト列に強い）。提出用 build_notebook.py と
同じ技法だが、こちらは Internet ON・GPU・SDK dataset 添付の **評価カーネル**で、提出カーネルとは別物。

出力は experiments/ を汚さないよう build/eval/<exp>/<model>/ に置く。

使い方:
    uv run python scripts/ops/build_eval_notebook.py exp001 --model gpt_oss
    uv run python scripts/ops/build_eval_notebook.py exp001 --model gemma_4 --candidates 30
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

import nbformat as nbf

EXPERIMENTS_DIR = Path("experiments")
EVAL_BUILD_DIR = Path("build") / "eval"
DRIVER_PATH = Path("scripts") / "eval" / "eval_driver.py"
KAGGLE_USER = "rikitomo0526"
SDK_DATASET = f"{KAGGLE_USER}/aiagent-security-sdk"
MODELS = ("gpt_oss", "gemma_4")

# SDK を展開する作業先（/kaggle/working には置かない＝output を小さく保つ）
SDK_WORK_DIR = "/tmp/aas_sdk"
SDK_ROOT = f"{SDK_WORK_DIR}/vendor/aicomp_sdk_pkg"


def _b64_write_cell(comment: str, src: str, dest: str) -> str:
    """src を base64 で埋め込み、実行時に dest へ復元するセル本体。"""
    b64 = base64.b64encode(src.encode("utf-8")).decode("ascii")
    return (
        f"# {comment}\n"
        "import base64, pathlib\n"
        f'_b64 = "{b64}"\n'
        f'_dest = pathlib.Path("{dest}")\n'
        "_dest.parent.mkdir(parents=True, exist_ok=True)\n"
        '_dest.write_text(base64.b64decode(_b64).decode("utf-8"))\n'
        'print("wrote", _dest, ":", _dest.stat().st_size, "bytes")\n'
    )


def _install_cell() -> str:
    """依存導入（CUDA 版 llama-cpp-python）。Kaggle GPU 上で llama.cpp を CUDA ビルドする。"""
    return (
        "import os\n"
        "!pip -q install gymnasium 'pydantic>=2' huggingface_hub\n"
        "os.environ['CMAKE_ARGS'] = '-DGGML_CUDA=on'  # CUDA 版 llama-cpp-python\n"
        "!pip -q install llama-cpp-python\n"
        "import llama_cpp; print('llama_cpp OK')\n"
    )


def _sdk_cell() -> str:
    """Add Input した SDK dataset を /tmp へ展開（assets.zip / 生ファイル 両対応）。"""
    return (
        "import os, glob, zipfile, shutil\n"
        f'SDK_WORK = "{SDK_WORK_DIR}"\n'
        "src = None\n"
        "for c in sorted(glob.glob('/kaggle/input/*')):\n"
        "    if os.path.isfile(os.path.join(c, 'assets.zip')) or os.path.isdir(os.path.join(c, 'vendor')):\n"
        "        src = c; break\n"
        "assert src, 'SDK dataset を Add Input してください（rikitomo0526/aiagent-security-sdk）'\n"
        "os.makedirs(SDK_WORK, exist_ok=True)\n"
        "zip_path = os.path.join(src, 'assets.zip')\n"
        "if os.path.isfile(zip_path):\n"
        "    with zipfile.ZipFile(zip_path) as z: z.extractall(SDK_WORK)\n"
        "    print('assets.zip を展開:', SDK_WORK)\n"
        "else:\n"
        "    shutil.copytree(os.path.join(src, 'vendor'), os.path.join(SDK_WORK, 'vendor'), dirs_exist_ok=True)\n"
        "    print('生ファイルをコピー:', SDK_WORK)\n"
        f'assert os.path.isdir("{SDK_ROOT}/aicomp_sdk"), "SDK が見つからない: {SDK_ROOT}"\n'
        f'print("SDK OK ->", "{SDK_ROOT}")\n'
    )


def _run_cell(exp: str, model: str, candidates: int | None, budget_s: float, guardrails: str) -> str:
    """eval_driver.py を実行して scores.json を書き出すセル。"""
    cand = f" --candidates {candidates}" if candidates is not None else ""
    return (
        "import json\n"
        "!python /kaggle/working/eval_driver.py \\\n"
        "    --attack /kaggle/working/attack.py \\\n"
        f"    --model {model} --guardrails {guardrails} \\\n"
        f"    --sdk-root {SDK_ROOT} --exp {exp}{cand} --budget-s {int(budget_s)} \\\n"
        "    --out /kaggle/working/scores.json\n"
        "print('--- scores.json ---')\n"
        "print(json.dumps(json.load(open('/kaggle/working/scores.json')), ensure_ascii=False, indent=2))\n"
    )


def build(
    exp: str,
    model: str,
    *,
    candidates: int | None = None,
    budget_s: float = 8000.0,
    guardrails: str = "public,strict,provenance",
) -> Path:
    """build/eval/<exp>/<model>/{eval.ipynb, kernel-metadata.json} を生成し、ディレクトリを返す。"""
    if model not in MODELS:
        raise ValueError(f"未知の model '{model}'。選択肢: {', '.join(MODELS)}")
    attack_path = EXPERIMENTS_DIR / exp / "attack.py"
    if not attack_path.is_file():
        raise FileNotFoundError(f"{attack_path} が存在しません")
    if not DRIVER_PATH.is_file():
        raise FileNotFoundError(f"{DRIVER_PATH} が存在しません")

    attack_src = attack_path.read_text()
    driver_src = DRIVER_PATH.read_text()

    out_dir = EVAL_BUILD_DIR / exp / model
    out_dir.mkdir(parents=True, exist_ok=True)

    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell(
            f"# {exp} — eval ({model})\n\n"
            f"attack.py を実モデル **{model}** で `{guardrails}` ガードレールへリプレイ採点する。\n\n"
            "**Kaggle 設定**: Accelerator=GPU（gemma_4 は T4×2 推奨）, Internet=ON, "
            f"Add Input=`{SDK_DATASET}`。この Notebook は採点には関与しない（提出用とは別物）。"
        ),
        nbf.v4.new_markdown_cell("## ① 依存（llama.cpp は CUDA ビルド）"),
        nbf.v4.new_code_cell(_install_cell()),
        nbf.v4.new_markdown_cell("## ② SDK dataset を展開"),
        nbf.v4.new_code_cell(_sdk_cell()),
        nbf.v4.new_markdown_cell("## ③ attack.py / eval_driver.py を復元"),
        nbf.v4.new_code_cell(
            _b64_write_cell("attack.py を /kaggle/working へ復元", attack_src, "/kaggle/working/attack.py")
        ),
        nbf.v4.new_code_cell(
            _b64_write_cell("eval_driver.py を /kaggle/working へ復元", driver_src, "/kaggle/working/eval_driver.py")
        ),
        nbf.v4.new_markdown_cell(f"## ④ 採点実行（{model}）→ /kaggle/working/scores.json"),
        nbf.v4.new_code_cell(_run_cell(exp, model, candidates, budget_s, guardrails)),
    ]
    nb.metadata["kernelspec"] = {"name": "python3", "language": "python", "display_name": "Python 3"}
    nb.metadata["language_info"] = {"name": "python"}

    nb_path = out_dir / "eval.ipynb"
    nbf.write(nb, str(nb_path))
    print(f"[build-eval] {nb_path} を生成（attack {len(attack_src)}B / driver {len(driver_src)}B）")

    _write_kernel_metadata(exp, model, out_dir)
    return out_dir


def _write_kernel_metadata(exp: str, model: str, out_dir: Path) -> None:
    """評価カーネルの kernel-metadata.json を生成（GPU/Internet ON・SDK dataset 添付）。"""
    slug_model = model.replace("_", "-")  # Kaggle slug は underscore 不可
    km = {
        "id": f"{KAGGLE_USER}/ai-agent-security-eval-{exp.replace('_', '-')}-{slug_model}",
        "title": f"AI Agent Security - Eval {exp} {model}",
        "code_file": "eval.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": True,  # GGUF DL と llama-cpp CUDA ビルドに必須
        "keywords": [],
        "dataset_sources": [SDK_DATASET],
        "kernel_sources": [],
        "competition_sources": [],
        "model_sources": [],
    }
    km_path = out_dir / "kernel-metadata.json"
    km_path.write_text(json.dumps(km, indent=2) + "\n")
    print(f"[build-eval] {km_path} を生成（id={km['id']}）")


def main() -> None:
    parser = argparse.ArgumentParser(description="評価用 eval.ipynb を生成（attack.py + eval_driver を焼く）")
    parser.add_argument("exp", help="実験名 (例: exp001)")
    parser.add_argument("--model", default="gpt_oss", choices=list(MODELS))
    parser.add_argument("--candidates", type=int, default=None, help="候補数の上限（smoke 用）")
    parser.add_argument("--budget-s", type=float, default=8000.0, help="生成フェーズの時間予算（秒）")
    parser.add_argument("--guardrails", default="public,strict,provenance", help="採点ガードレール（カンマ区切り）")
    args = parser.parse_args()
    build(
        args.exp,
        args.model,
        candidates=args.candidates,
        budget_s=args.budget_s,
        guardrails=args.guardrails,
    )


if __name__ == "__main__":
    main()
