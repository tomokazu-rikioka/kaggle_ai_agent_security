"""公式 `kaggle` CLI を subprocess で叩く薄いラッパ。

認証は CLI 側（`~/.kaggle/kaggle.json` か `KAGGLE_USERNAME`/`KAGGLE_KEY`）に委ねる。
既存 `scripts/ops/run_eval.py::_run` と同じ流儀（capture_output/text/check=False）。
"""

from __future__ import annotations

import csv
import io
import subprocess


def run_kaggle(args: list[str]) -> subprocess.CompletedProcess:
    """`kaggle <args...>` を実行して CompletedProcess を返す（例外は投げない）。"""
    cmd = ["kaggle", *args]
    print(f"[research] $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def kaggle_list_csv(args: list[str]) -> list[dict[str, str]]:
    """`kaggle ... -v`（CSV 出力）を実行し、行を dict のリストで返す。

    `-v`（--csv）を付けて呼ぶこと。出力が空 or ヘッダのみなら空リストを返す。
    レート制限やエラー時は RuntimeError を送出する。
    """
    res = run_kaggle([*args, "-v"])
    if res.returncode != 0:
        raise RuntimeError(f"kaggle CLI に失敗（exit {res.returncode}）: {res.stderr.strip()}")
    text = res.stdout.strip()
    if not text:
        return []
    # CLI は結果ゼロ時に "No kernels found" などを stdout に出すことがある（CSV でない）
    first_line = text.splitlines()[0]
    if "," not in first_line:
        return []
    reader = csv.DictReader(io.StringIO(text))
    return [dict(r) for r in reader]
