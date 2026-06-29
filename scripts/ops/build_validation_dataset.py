"""Kaggle で実モデル検証するための dataset アセット（assets.zip）を生成する。

Kaggle notebook 上で `validation/run_validation.py` を実モデル（gpt_oss）で回すには、
`validation/`・`vendor/aicomp_sdk_pkg/`（公式 SDK）・対象 `attack.py` を notebook へ持ち込む
必要がある。本スクリプトはこれらを 1 つの `assets.zip` に固め、`dataset-metadata.json` と共に
`build/validation_dataset/` へ出力する。notebook 側でこの zip を `/kaggle/working` に展開すれば
`python -m validation.run_validation` がそのまま動く（paths.py が vendor/ を相対解決する）。

zip 1 ファイルにまとめる理由: `kaggle datasets create --dir-mode` のサブディレクトリ扱いに依存せず、
ディレクトリ階層を確実に保持できる（展開は notebook 側の責務）。GGUF はサイズが大きいため含めない
（notebook で `download_models.py` が HF hub から取得する）。

出力後、初回/更新それぞれの `kaggle datasets` コマンドを案内する（アップロードはユーザーが実行）。

使い方:
    uv run python scripts/ops/build_validation_dataset.py            # 既定 exp001
    uv run python scripts/ops/build_validation_dataset.py exp002
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

OUT_DIR = Path("build") / "validation_dataset"
KAGGLE_USER = "rikitomo0526"
DATASET_SLUG = "aiagent-security-validation"

# zip に含めないディレクトリ名・拡張子
_IGNORE_DIRS = {"__pycache__", ".ipynb_checkpoints"}
_IGNORE_SUFFIXES = {".pyc", ".pyo", ".pyd"}


def _skip(rel: Path) -> bool:
    """相対パスが除外対象（キャッシュ等）か。"""
    if any(part in _IGNORE_DIRS for part in rel.parts):
        return True
    return rel.suffix in _IGNORE_SUFFIXES


def _add_tree(zf: zipfile.ZipFile, src_dir: Path, arc_prefix: str, *, skip_top: set[str]) -> int:
    """src_dir 配下のファイルを arc_prefix/ 以下として zip に追加。追加件数を返す。

    skip_top: src_dir 直下の除外したいディレクトリ名（例: validation/runs）。
    """
    count = 0
    for path in sorted(src_dir.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(src_dir)
        if rel.parts and rel.parts[0] in skip_top:
            continue
        if _skip(rel):
            continue
        zf.write(path, f"{arc_prefix}/{rel.as_posix()}")
        count += 1
    return count


def build(exp: str = "exp001") -> Path:
    """assets.zip と dataset-metadata.json を build/validation_dataset/ に生成する。"""
    validation_dir = Path("validation")
    vendor_dir = Path("vendor/aicomp_sdk_pkg")
    attack_path = Path("experiments") / exp / "attack.py"
    for required in (validation_dir, vendor_dir, attack_path):
        if not required.exists():
            raise FileNotFoundError(f"{required} が存在しません（リポジトリ直下で実行してください）")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OUT_DIR / "assets.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        n_val = _add_tree(zf, validation_dir, "validation", skip_top={"runs"})
        n_sdk = _add_tree(zf, vendor_dir, "vendor/aicomp_sdk_pkg", skip_top=set())
        zf.write(attack_path, "attack.py")
    print(f"[dataset] {zip_path} を生成（validation {n_val} files / SDK {n_sdk} files / attack.py 1）")

    meta = {
        "title": "aiagent security validation",
        "id": f"{KAGGLE_USER}/{DATASET_SLUG}",
        "licenses": [{"name": "CC0-1.0"}],
    }
    meta_path = OUT_DIR / "dataset-metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"[dataset] {meta_path} を生成（id={meta['id']}）")

    print("\n次の手順で Kaggle へアップロード（実行はユーザー）:")
    print(f"  初回: kaggle datasets create  -p {OUT_DIR}")
    print(f"  更新: kaggle datasets version -p {OUT_DIR} -m 'update {exp}'")
    print(f"  notebook の Add Input に dataset '{KAGGLE_USER}/{DATASET_SLUG}' を追加して使う。")
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Kaggle 実モデル検証用 dataset(assets.zip) を生成")
    parser.add_argument("exp", nargs="?", default="exp001", help="対象実験名（既定: exp001）")
    args = parser.parse_args()
    build(args.exp)


if __name__ == "__main__":
    main()
