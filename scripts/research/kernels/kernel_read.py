"""CLI: カーネル本文を取得（公式 kaggle kernels pull）してキャッシュし、code+markdown を表示する。

使い方:
    uv run python scripts/research/kernels/kernel_read.py <owner/slug> [--comp SLUG] [--raw] [--force]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.research.common.config import COMPETITION_SLUG, NOTEBOOKS_DIR  # noqa: E402
from scripts.research.common.kaggle_cli import run_kaggle  # noqa: E402
from scripts.research.kernels.notebook_reader import read_notebook, render_notebook  # noqa: E402


def _normalize_ref(ref: str) -> str:
    """Kaggle URL 形式でも owner/slug を取り出す。"""
    ref = ref.strip().rstrip("/")
    marker = "kaggle.com/code/"
    if marker in ref:
        ref = ref.split(marker, 1)[1]
    return ref


def cache_dir_for(comp: str, ref: str) -> Path:
    """カーネルの .ipynb キャッシュ先ディレクトリ。"""
    safe = ref.replace("/", "__")
    return NOTEBOOKS_DIR / comp / safe


def pull_kernel(ref: str, dest: Path, *, force: bool) -> Path:
    """`kaggle kernels pull` で .ipynb を dest に取得し、そのパスを返す。

    既存キャッシュがあり force でなければ再取得しない。
    """
    dest.mkdir(parents=True, exist_ok=True)
    existing = sorted(dest.glob("*.ipynb"))
    if existing and not force:
        return existing[0]
    res = run_kaggle(["kernels", "pull", ref, "-p", str(dest)])
    if res.returncode != 0:
        raise RuntimeError(f"kernels pull に失敗（exit {res.returncode}）: {res.stderr.strip()}")
    ipynbs = sorted(dest.glob("*.ipynb"))
    if not ipynbs:
        # スクリプト型カーネル（.py/.r）等は .ipynb を持たない
        others = sorted(p for p in dest.glob("*") if p.suffix in {".py", ".r", ".R"})
        if others:
            return others[0]
        raise RuntimeError(f"pull 後に本文ファイルが見つからない: {dest}")
    return ipynbs[0]


def read_kernel(ref: str, *, comp: str, raw: bool, force: bool) -> str:
    """カーネルを取得して整形済みテキストを返す。"""
    ref = _normalize_ref(ref)
    dest = cache_dir_for(comp, ref)
    path = pull_kernel(ref, dest, force=force)
    if path.suffix == ".ipynb":
        return render_notebook(read_notebook(path), raw=raw)
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    ap = argparse.ArgumentParser(description="カーネル本文を取得して表示")
    ap.add_argument("kernel_ref", help="owner/kernel-slug または Kaggle URL")
    ap.add_argument("--comp", default=COMPETITION_SLUG, help="キャッシュ分類用のコンペ slug")
    ap.add_argument("--raw", action="store_true", help="整形せず source を連結")
    ap.add_argument("--force", action="store_true", help="キャッシュを無視して再取得")
    args = ap.parse_args()

    print(read_kernel(args.kernel_ref, comp=args.comp, raw=args.raw, force=args.force))


if __name__ == "__main__":
    main()
