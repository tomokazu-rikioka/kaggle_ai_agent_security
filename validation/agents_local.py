"""ローカル用 agent_factory の構築。

- deterministic : VulnerableDeterministicAgent（モデル不要・GPU 不要）。SDK の factory に委譲。
- gpt_oss / gemma_4 : 公式採点と同一の GGUF + llama.cpp 経路。
    LlamaCppChatTemplateBackend.from_model_path(n_gpu_layers=-1, n_ctx=8192) で
    GGUF を **1 回だけ**ロードし、その backend を共有して agent ラッパを量産する
    （候補ごとに 12GB を再ロードしないため必須）。Colab/Kaggle の GPU（CUDA）で実行する。

GGUF の所在は公式モデルサーバ（gpt_oss_model_server.py / gemma_model_server.py）と
同じ env var で解決する：
    *_MODEL_PATH があればそのローカル .gguf を使用、
    無ければ *_GGUF_REPO / *_GGUF_FILE（既定値あり）から huggingface_hub で取得。
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from aicomp_sdk.agents.factory import build_agent_factory as _sdk_build_agent_factory
from aicomp_sdk.agents.gemma4_agent import DEFAULT_GEMMA4_MODEL_ID, Gemma4Agent
from aicomp_sdk.agents.gpt_oss_agent import DEFAULT_GPT_OSS_MODEL_ID, GPTOSSAgent
from aicomp_sdk.agents.hf_chat_template.backends.llama_cpp import LlamaCppChatTemplateBackend
from aicomp_sdk.agents.hf_chat_template.types import HFBackendConfig

AgentFactory = Callable[[], Any]


@dataclass(frozen=True)
class GgufSpec:
    """公式 GgufModelSpec のローカル版（必要分だけ）。"""

    label: str
    model_id: str
    default_repo: str
    default_file: str
    repo_env: str
    file_env: str
    path_env: str
    create_agent: Callable[[Any], Any]
    n_ctx: int = 8192
    n_gpu_layers: int = -1
    max_new_tokens: int = 1024
    supports_tools: bool = True


# 公式 gpt_oss_model_server.py / gemma_model_server.py の SPEC と同一の既定値
GGUF_SPECS: dict[str, GgufSpec] = {
    "gpt_oss": GgufSpec(
        label="GPT-OSS",
        model_id=DEFAULT_GPT_OSS_MODEL_ID,  # openai/gpt-oss-20b
        default_repo="unsloth/gpt-oss-20b-GGUF",
        default_file="gpt-oss-20b-Q4_K_M.gguf",
        repo_env="GPT_OSS_GGUF_REPO",
        file_env="GPT_OSS_GGUF_FILE",
        path_env="GPT_OSS_MODEL_PATH",
        create_agent=lambda backend: GPTOSSAgent(backend),
    ),
    # 公式「gemma」ターゲットの実体は Gemma4Agent + 26B（gemma_model_server.py:24）。
    "gemma_4": GgufSpec(
        label="Gemma-4-26B",
        model_id=DEFAULT_GEMMA4_MODEL_ID,  # google/gemma-4-26B-A4B-it
        default_repo="unsloth/gemma-4-26B-A4B-it-GGUF",
        default_file="gemma-4-26B-A4B-it-UD-Q4_K_M.gguf",
        repo_env="GEMMA_GGUF_REPO",
        file_env="GEMMA_GGUF_FILE",
        path_env="GEMMA_MODEL_PATH",
        create_agent=lambda backend: Gemma4Agent(backend),
    ),
}

# 採点と同じターゲット名のエイリアス（"gemma" -> 26B の Gemma4）
_ALIASES = {"gemma": "gemma_4"}


def _resolve_gguf_path(spec: GgufSpec) -> str:
    """env のローカル .gguf を優先。無ければ HF から取得（公式 _resolve_model_path と同等）。"""
    local = os.environ.get(spec.path_env, "").strip()
    if local:
        if not os.path.exists(local):
            raise FileNotFoundError(f"{spec.path_env} の指す .gguf が存在しません: {local}")
        print(f"[agents_local] ローカル GGUF を使用: {local}")
        return local

    from huggingface_hub import hf_hub_download

    repo = os.environ.get(spec.repo_env, spec.default_repo)
    filename = os.environ.get(spec.file_env, spec.default_file)
    print(f"[agents_local] GGUF を取得: {repo}/{filename}（初回はダウンロードに時間がかかります）")
    path = hf_hub_download(repo_id=repo, filename=filename)
    print(f"[agents_local] 取得完了: {path}")
    return path


def _build_gguf_agent_factory(kind: str) -> AgentFactory:
    spec = GGUF_SPECS[kind]
    model_path = _resolve_gguf_path(spec)
    n_gpu_layers = int(os.environ.get("LLAMA_N_GPU_LAYERS", spec.n_gpu_layers))
    n_ctx = int(os.environ.get("LLAMA_N_CTX", spec.n_ctx))

    config = HFBackendConfig(
        model_id=spec.model_id,
        model_path=model_path,
        max_new_tokens=spec.max_new_tokens,
    )
    print(f"[agents_local] {spec.label} を llama.cpp でロード中（n_gpu_layers={n_gpu_layers}, n_ctx={n_ctx}）…")
    # GGUF を 1 回だけロードし、backend を共有する
    backend = LlamaCppChatTemplateBackend.from_model_path(
        model_path=model_path,
        config=config,
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,
        supports_tools=spec.supports_tools,
    )
    print(f"[agents_local] {spec.label} ロード完了。")

    # 各 env 構築時に呼ばれる factory。共有 backend を薄くラップするだけ（再ロードしない）。
    return lambda: spec.create_agent(backend)


def build_local_agent_factory(kind: str) -> AgentFactory:
    """検証用 agent_factory を返す。kind: deterministic | gpt_oss | gemma_4(=gemma)。"""
    kind = _ALIASES.get(kind, kind)
    if kind == "deterministic":
        return _sdk_build_agent_factory("deterministic")
    if kind in GGUF_SPECS:
        return _build_gguf_agent_factory(kind)
    raise ValueError(
        f"未知の agent '{kind}'。選択肢: deterministic, gpt_oss, gemma_4(=gemma)"
    )


# GPU 不要で即時に回せるエージェント
NO_GPU_AGENTS = {"deterministic"}
