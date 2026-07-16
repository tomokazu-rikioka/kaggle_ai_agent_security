"""公式 `kaggle` CLI を subprocess で呼び出す薄い包み（ラッパ）。

認証は CLI 側（`~/.kaggle/kaggle.json` か `KAGGLE_USERNAME`/`KAGGLE_KEY`）に任せる。
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
    """`kaggle ... -v`（CSV 出力）を実行し、各行を dict にした一覧を返す。

    `-v`（--csv）を付けて呼ぶこと。出力が空、またはヘッダ行だけなら空リストを返す。
    レート制限やエラーのときは RuntimeError を投げる。
    """
    res = run_kaggle([*args, "-v"])
    if res.returncode != 0:
        raise RuntimeError(f"kaggle CLI に失敗（exit {res.returncode}）: {res.stderr.strip()}")
    text = res.stdout.strip()
    if not text:
        return []
    # 結果ゼロのとき CLI は "No kernels found" などを stdout に出すことがある（CSV 形式ではない）
    first_line = text.splitlines()[0]
    if "," not in first_line:
        return []
    reader = csv.DictReader(io.StringIO(text))
    return [dict(r) for r in reader]
