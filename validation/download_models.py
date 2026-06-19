"""GGUF 取得ヘルパー（公式採点と同一の repo/file 既定値）。

使い方:
    python -m validation.download_models gpt_oss
    python -m validation.download_models gemma_4
    python -m validation.download_models gpt_oss --local-dir ~/models

env で repo/file を上書き可能（agents_local.py と同じ env var）。
取得後はパスを表示する。`*_MODEL_PATH` にそのパスを export すれば再ダウンロード不要。
"""

from __future__ import annotations

import argparse
import os

import validation.paths  # noqa: F401  sys.path 整備（一貫性のため）
from validation.agents_local import GGUF_SPECS, _ALIASES


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="GGUF ダウンロード（gpt_oss / gemma_4）")
    ap.add_argument("model", choices=list(GGUF_SPECS) + list(_ALIASES))
    ap.add_argument("--local-dir", default=None, help="保存先ディレクトリ（既定は HF キャッシュ）")
    args = ap.parse_args(argv)

    kind = _ALIASES.get(args.model, args.model)
    spec = GGUF_SPECS[kind]
    repo = os.environ.get(spec.repo_env, spec.default_repo)
    filename = os.environ.get(spec.file_env, spec.default_file)

    from huggingface_hub import hf_hub_download

    print(f"取得中: {repo}/{filename}（初回は 12〜16GB のため時間がかかります）")
    path = hf_hub_download(repo_id=repo, filename=filename, local_dir=args.local_dir)
    print(f"\n完了: {path}")
    print(f"次回から再ダウンロードを避けるには:\n  export {spec.path_env}={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
