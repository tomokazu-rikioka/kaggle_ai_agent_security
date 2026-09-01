"""Colab CLI runtimeの作業ディレクトリと結果ファイルを読み取り専用で確認する。"""

from pathlib import Path

for root in (Path("/content/aas-a100"), Path("/content/aas")):
    print(f"[inspect] {root} exists={root.exists()}")
    if root.exists():
        for path in sorted(root.glob("results/gemma_r*.json"))[-20:]:
            print(f"[result] {path} size={path.stat().st_size}")
