"""新しい攻撃アルゴリズム実験ディレクトリを作成する。

experiments/_template/（または既存 exp）を複製して experiments/<name>/ を作る。
ビルド生成物（submission.ipynb）と __pycache__ はコピーしない。

使い方:
    uv run python scripts/ops/new_experiment.py exp001
    uv run python scripts/ops/new_experiment.py exp002 --base exp001
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

EXPERIMENTS_DIR = Path("experiments")
IGNORE = shutil.ignore_patterns("__pycache__", "submission.ipynb")


def main() -> None:
    parser = argparse.ArgumentParser(description="新しい攻撃アルゴリズム実験を作成する")
    parser.add_argument("name", help="新実験名 (例: exp001)")
    parser.add_argument("--base", default="_template", help="コピー元 (デフォルト: _template)")
    args = parser.parse_args()

    base_dir = EXPERIMENTS_DIR / args.base
    new_dir = EXPERIMENTS_DIR / args.name

    if not base_dir.exists():
        print(f"Error: コピー元 {base_dir} が存在しません")
        sys.exit(1)
    if new_dir.exists():
        print(f"Error: {new_dir} は既に存在します")
        sys.exit(1)

    shutil.copytree(base_dir, new_dir, ignore=IGNORE)

    created = sorted(f.name for f in new_dir.iterdir())
    print(f"Created {new_dir} (base: {base_dir})")
    print(f"Files: {created}")
    print()
    print("次のステップ:")
    print("  1. docs/knowledges/04-レバー台帳.md の事前判定ルーブリックで施策の赤/緑を確認")
    print(f"  2. {new_dir}/attack.py を編集（兄弟 import 不可・単一ファイル自己完結）")
    print(f"     - kernel-metadata.json の id/title を {args.name} へ書き換える")
    print(f"  3. make eval EXP={args.name} CANDIDATES=30   # Kaggle で smoke 採点（build→push→wait→fetch）")
    print(f"  4. experiments/{args.name}/scores.json を docs/SCORE.md の local 列へ記入")
    print(f"  5. make build EXP={args.name} && make submit EXP={args.name}")
    print(f"  6. /lb-submit {args.name}                    # LB 提出＋結果記録（★ユーザ明示指示時のみ）")


if __name__ == "__main__":
    main()
