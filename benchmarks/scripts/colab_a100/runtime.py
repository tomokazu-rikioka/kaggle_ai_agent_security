"""Colab A100 上で公式と同じ GGUF を取得・検証する共通処理。"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path("/content/aas-a100")
REPO_ROOT = Path("/content/aas")
MANIFEST_PATH = ROOT / "model_manifest.json"

MODELS: dict[str, dict[str, Any]] = {
    "gpt_oss": {
        "repo": "unsloth/gpt-oss-20b-GGUF",
        "filename": "gpt-oss-20b-Q4_K_M.gguf",
        "size_bytes": 11_624_759_488,
        "sha256": "c27536640e410032865dc68781d80a08b98f8db5e93575919af8ccc0568aeb4f",
        "kaggle_handle": "llkh0a/gpt-oss-20b-gguf/pyTorch/default/1",
        "kaggle_path": "gpt_oss/gpt-oss-20b-Q4_K_M.gguf",
        "path_env": "GPT_OSS_MODEL_PATH",
    },
    "gemma_4": {
        "repo": "unsloth/gemma-4-26B-A4B-it-GGUF",
        "filename": "gemma-4-26B-A4B-it-UD-Q4_K_M.gguf",
        # mainのGGUF metadata/chat templateは更新され得る。競技添付版と同じ
        # size/SHAを持つrevisionへ固定し、A100の比較母集団を変えない。
        "revision": "c462057f7ed65ccdb7f7e0778fae67894d425d92",
        "size_bytes": 16_947_539_744,
        "sha256": "34c746b1d50ab813e29cd46c4796e3f43c741901a582f93a67b55b9fc9687b35",
        "kaggle_handle": "llkh0a/gemma-4-26b-a4b-it-ud-q4-k-m-gguf/pyTorch/default/1",
        "kaggle_path": "gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf",
        "path_env": "GEMMA_MODEL_PATH",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _read_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.is_file():
        return {"models": {}}
    return json.loads(MANIFEST_PATH.read_text())


def ensure_model(kind: str) -> Path:
    """Kaggle T4 評価で添付した GGUF と同じ実体をサイズ/SHA-256まで固定する。"""

    import kagglehub

    spec = MODELS[kind]
    manifest = _read_manifest()
    previous = manifest.setdefault("models", {}).get(kind, {})
    previous_path = Path(previous.get("path", ""))
    if (
        previous_path.is_file()
        and previous_path.stat().st_size == spec["size_bytes"]
        and previous.get("sha256") == spec["sha256"]
    ):
        path = previous_path
    else:
        try:
            path = Path(
                kagglehub.model_download(
                    spec["kaggle_handle"],
                    path=spec["kaggle_path"],
                    output_dir=str(ROOT / "kaggle-models" / kind),
                )
            )
        except Exception as error:
            from huggingface_hub import hf_hub_download

            print(f"[model] Kaggle Models取得失敗。HF Hubへフォールバック: {type(error).__name__}: {error}")
            path = Path(
                hf_hub_download(
                    repo_id=spec["repo"],
                    filename=spec["filename"],
                    revision=spec.get("revision"),
                    local_dir=str(ROOT / "hf-models" / kind / str(spec.get("revision", "main"))[:12]),
                )
            )
    actual_size = path.stat().st_size
    if actual_size != spec["size_bytes"]:
        raise RuntimeError(
            f"GGUF size mismatch: {kind} expected={spec['size_bytes']} actual={actual_size} path={path}"
        )

    sha256 = previous.get("sha256") if previous.get("path") == str(path) else None
    if not sha256:
        print(f"[model] SHA-256を計算中: {path}")
        sha256 = _sha256(path)
    if sha256 != spec["sha256"]:
        raise RuntimeError(f"GGUF SHA-256 mismatch: {kind} expected={spec['sha256']} actual={sha256}")
    manifest["models"][kind] = {
        **spec,
        "path": str(path),
        "actual_size_bytes": actual_size,
        "actual_sha256": sha256,
    }
    ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    os.environ[spec["path_env"]] = str(path)
    print(json.dumps(manifest["models"][kind], ensure_ascii=False, indent=2))
    return path


def bench_environment(kind: str) -> dict[str, str]:
    """bench_driver が repo 配置と SDK/model を確実に見つけられる環境を返す。"""

    model_path = ensure_model(kind)
    env = dict(os.environ)
    env[MODELS[kind]["path_env"]] = str(model_path)
    env["AICOMP_SDK_ROOT"] = str(REPO_ROOT / "vendor" / "aicomp_sdk_pkg")
    env["LLAMA_N_GPU_LAYERS"] = "-1"
    env["LLAMA_N_CTX"] = "8192"
    python_paths = [
        str(REPO_ROOT / "scripts" / "eval"),
        str(REPO_ROOT),
        str(REPO_ROOT / "vendor" / "aicomp_sdk_pkg"),
    ]
    old_path = env.get("PYTHONPATH")
    env["PYTHONPATH"] = os.pathsep.join(python_paths + ([old_path] if old_path else []))
    return env
