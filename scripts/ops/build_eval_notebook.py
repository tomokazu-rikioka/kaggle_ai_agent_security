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
COMPETITION = "ai-agent-security-multi-step-tool-attacks"  # competition_sources（コンペ紐付け）
MACHINE_SHAPE = "NvidiaTeslaT4"  # T4×2（AAS 実績。gpt_oss 11.6GB / gemma 16.9GB とも余裕。P100 は gemma 不可）
MODELS = ("gpt_oss", "gemma_4")

# GGUF は Kaggle Models から Add Input で添付し HF hub DL を回避する（AAS Local Validation 方式）。
# eval_driver の _resolve_gguf_path が *_MODEL_PATH env を優先するので、run セルでこのパスを export する。
GGUF_MODEL_SOURCES = {
    "gpt_oss": "llkh0a/gpt-oss-20b-gguf/pytorch/default/1",
    "gemma_4": "llkh0a/gemma-4-26b-a4b-it-ud-q4-k-m-gguf/pytorch/default/1",
}
GGUF_PATHS = {
    "gpt_oss": "/kaggle/input/models/llkh0a/gpt-oss-20b-gguf/pytorch/default/1/gpt_oss/gpt-oss-20b-Q4_K_M.gguf",
    "gemma_4": (
        "/kaggle/input/models/llkh0a/gemma-4-26b-a4b-it-ud-q4-k-m-gguf/pytorch/default/1/"
        "gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
    ),
}
GGUF_PATH_ENVS = {"gpt_oss": "GPT_OSS_MODEL_PATH", "gemma_4": "GEMMA_MODEL_PATH"}

# SDK は competition data（competition_sources）の公式パッケージを直接使う（AAS 方式）。
# 競技データ直下に aicomp_sdk(v3.1.2)+kaggle_evaluation+fixtures がある。SDK dataset の Add Input は
# competition 添付時に /kaggle/input/datasets/<owner>/<slug>/ へ移動し、直下走査で見つからないため使わない。
SDK_ROOT = f"/kaggle/input/competitions/{COMPETITION}"


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
    """依存導入。llama-cpp-python は CUDA 事前ビルド wheel を使う。

    Kaggle GPU は CUDA 12.8 だが nvcc がなく、``CMAKE_ARGS=-DGGML_CUDA=on`` のソースビルドは
    cmake 構成段階で失敗する（診断カーネルで確認）。abetlen の事前ビルド CUDA wheel(cu124)は
    CUDA 12.8 ランタイム上で後方互換に動作するため、ビルド不要で確実・高速。
    """
    return (
        "!pip -q install gymnasium 'pydantic>=2' huggingface_hub\n"
        "!pip -q install llama-cpp-python "
        "--extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124\n"
        "import llama_cpp; print('llama_cpp OK', llama_cpp.__version__)\n"
    )


def _sdk_cell() -> str:
    """競技データ（competition_sources）の公式 SDK を使う（AAS 方式）。

    SDK dataset は competition 添付時に /kaggle/input/datasets/<owner>/<slug>/ へ移動し、直下走査で
    見つからないため使わず、競技データ直下の aicomp_sdk(v3.1.2) を eval_driver が --sdk-root で載せる。
    """
    return (
        "import os\n"
        f'assert os.path.isdir("{SDK_ROOT}/aicomp_sdk"), '
        f'"competition data に aicomp_sdk が無い（competition_sources 未添付?）: {SDK_ROOT}"\n'
        f'print("SDK OK (competition data) ->", "{SDK_ROOT}")\n'
    )


def _run_cell(exp: str, model: str, candidates: int | None, budget_s: float, guardrails: str) -> str:
    """eval_driver.py を実行して scores.json を書き出すセル。"""
    cand = f" --candidates {candidates}" if candidates is not None else ""
    gguf_path = GGUF_PATHS[model]
    path_env = GGUF_PATH_ENVS[model]
    return (
        "import json, os\n"
        f'os.environ["{path_env}"] = "{gguf_path}"  # Kaggle Models 添付の GGUF（HF hub DL 回避）\n'
        f'assert os.path.exists("{gguf_path}"), "GGUF が見つからない（Add Input 未添付?）: {gguf_path}"\n'
        f'print("GGUF:", "{gguf_path}")\n'
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
            "**Kaggle 設定**: Accelerator=GPU T4×2, Internet=ON, "
            "Add Input=競技データ + GGUF Model。採点には関与しない（提出用とは別物）。"
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
        "dataset_sources": [],  # SDK は competition data（competition_sources）から取る
        "kernel_sources": [],
        "competition_sources": [COMPETITION],
        "model_sources": [GGUF_MODEL_SOURCES[model]],
        "machine_shape": MACHINE_SHAPE,  # T4×2（AAS 実績。gemma は P100 不可なので両モデル T4×2 に統一）
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
