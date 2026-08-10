"""公式 `kaggle` CLI を subprocess で呼び出す薄い包み（ラッパ）。

認証は CLI 側（`~/.kaggle/kaggle.json` か `KAGGLE_USERNAME`/`KAGGLE_KEY`）に任せる。
既存 `scripts/ops/run_eval.py::_run` と同じ流儀（capture_output/text/check=False）。
"""

from __future__ import annotations

import csv
import io
import os
import subprocess
import time


def run_kaggle(args: list[str]) -> subprocess.CompletedProcess:
    """`kaggle <args...>` を実行して CompletedProcess を返す（例外は投げない）。

    `KAGGLE_API_TOKEN` は内部 API（discussions / kernel scores）用の別物だが、
    公式 CLI もこれを認証に使うため、設定されていると kaggle.json を無視して
    認証に失敗する（exit 1・stderr 空）。CLI には渡さない。
    """
    cmd = ["kaggle", *args]
    print(f"[research] $ {' '.join(cmd)}")
    env = {k: v for k, v in os.environ.items() if k != "KAGGLE_API_TOKEN"}
    return subprocess.run(cmd, check=False, capture_output=True, text=True, env=env)


def kaggle_list_csv(args: list[str], *, max_retries: int = 5, retry_wait_s: float = 15.0) -> list[dict[str, str]]:
    """`kaggle ... -v`（CSV 出力）を実行し、各行を dict にした一覧を返す。

    `-v`（--csv）を付けて呼ぶこと。出力が空、またはヘッダ行だけなら空リストを返す。
    ページを続けて叩くと CLI が散発的に exit 1（stderr 空）を返すので、間を置いて再試行する。
    それでも駄目なら RuntimeError を投げる。
    """
    res = run_kaggle([*args, "-v"])
    for attempt in range(1, max_retries):
        if res.returncode == 0:
            break
        wait = retry_wait_s * attempt
        print(f"[research] kaggle CLI が exit {res.returncode}。{wait:.0f}s 待って再試行 {attempt}/{max_retries - 1}")
        time.sleep(wait)
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
