"""Kaggle 評価 Notebook へ公式 SDK を届けるための dataset アセット（assets.zip）を生成する。

評価 Notebook（build_eval_notebook.py が生成）は attack.py を手元採点するために `aicomp_sdk`
（vendor/aicomp_sdk_pkg/）を import する。本スクリプトは vendor の SDK を 1 つの `assets.zip` にまとめ、
`dataset-metadata.json` と一緒に `build/sdk_dataset/` へ出力する。Notebook 側でこの zip を展開し、
`--sdk-root` で sys.path に載せる。

SDK は vendor 更新時しか変わらないので、この dataset のアップロードは初回とバージョン更新（bump）時だけで足りる。
GGUF（モデル重み）はサイズが大きいので含めない（Notebook が Internet ON で Hugging Face Hub（HF hub）から取得する）。

zip 1 ファイルにまとめる理由: `kaggle datasets create` のサブディレクトリの扱いに頼らず、ディレクトリ
階層を確実に保てる（展開は Notebook 側の役目）。

使い方:
    uv run python scripts/ops/build_sdk_dataset.py
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

OUT_DIR = Path("build") / "sdk_dataset"
KAGGLE_USER = "rikitomo0526"
DATASET_SLUG = "aiagent-security-sdk"

_IGNORE_DIRS = {"__pycache__", ".ipynb_checkpoints"}
_IGNORE_SUFFIXES = {".pyc", ".pyo", ".pyd"}


def _skip(rel: Path) -> bool:
    if any(part in _IGNORE_DIRS for part in rel.parts):
        return True
    return rel.suffix in _IGNORE_SUFFIXES


def _add_tree(zf: zipfile.ZipFile, src_dir: Path, arc_prefix: str) -> int:
    count = 0
    for path in sorted(src_dir.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(src_dir)
        if _skip(rel):
            continue
        zf.write(path, f"{arc_prefix}/{rel.as_posix()}")
        count += 1
    return count


def build() -> Path:
    """assets.zip と dataset-metadata.json を build/sdk_dataset/ に作る。"""
    vendor_dir = Path("vendor/aicomp_sdk_pkg")
    if not vendor_dir.exists():
        raise FileNotFoundError(f"{vendor_dir} が存在しません（リポジトリ直下で実行してください）")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OUT_DIR / "assets.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        n_sdk = _add_tree(zf, vendor_dir, "vendor/aicomp_sdk_pkg")
    print(f"[sdk-dataset] {zip_path} を生成（SDK {n_sdk} files）")

    meta = {
        "title": "aiagent security sdk",
        "id": f"{KAGGLE_USER}/{DATASET_SLUG}",
        "licenses": [{"name": "CC0-1.0"}],
    }
    meta_path = OUT_DIR / "dataset-metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"[sdk-dataset] {meta_path} を生成（id={meta['id']}）")

    print("\n次の手順で Kaggle へアップロード（実行はユーザー。SDK は vendor 更新時のみ）:")
    print(f"  初回: kaggle datasets create  -p {OUT_DIR}")
    print(f"  更新: kaggle datasets version -p {OUT_DIR} -m 'bump sdk'")
    print(f"  評価 Notebook の Add Input に dataset '{KAGGLE_USER}/{DATASET_SLUG}' を追加して使う。")
    return zip_path


def main() -> None:
    argparse.ArgumentParser(description="Kaggle 評価用 SDK dataset(assets.zip) を生成").parse_args()
    build()


if __name__ == "__main__":
    main()
