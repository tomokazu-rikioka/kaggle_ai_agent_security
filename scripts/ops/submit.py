"""experiments/<exp> をビルドして Kaggle へ push する。

1. build_notebook.build(exp) で submission.ipynb を生成し kernel-metadata.json を同期
2. `kaggle kernels push -p experiments/<exp>` で push
push 後はカーネルが実行され、評価基盤が submission.csv（4 スコア）を生成する。
実行状態は `make status EXP=<exp>` で確認できる。

使い方:
    uv run python scripts/ops/submit.py exp001
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from build_notebook import EXPERIMENTS_DIR, build


def main() -> None:
    parser = argparse.ArgumentParser(description="ビルドして Kaggle へ push する")
    parser.add_argument("exp", help="実験名 (例: exp001)")
    parser.add_argument("--dry-run", action="store_true", help="push せずビルドのみ")
    args = parser.parse_args()

    build(args.exp)
    exp_dir = EXPERIMENTS_DIR / args.exp

    if args.dry_run:
        print(f"[submit] --dry-run: push をスキップ（{exp_dir}）")
        return

    cmd = ["kaggle", "kernels", "push", "-p", str(exp_dir)]
    print(f"[submit] $ {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"[submit] push に失敗しました（exit {result.returncode}）", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"[submit] push 完了。`make status EXP={args.exp}` で実行状態を確認。")


if __name__ == "__main__":
    main()
