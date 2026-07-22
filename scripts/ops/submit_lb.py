"""experiments/<exp> の（既に push 済みの）カーネルを LB（リーダーボード）へ提出する。

`make submit` はカーネルを push して実行するだけで、LB への提出（Submit to Competition）は
行わない。本スクリプトはその最後の一手を担う。code competition なので
`kaggle competitions submit -k <owner/slug> -f submission.csv -m <msg>` に相当する API
（competition_submit_code）を叩く。バージョンは省略時に最新版が使われる。

重要（運用ルール）:
- **ユーザから明示的に指示された場合のみ実行する**。LB 提出は日次上限（5/日・最終2件）を
  消費する不可逆な外部アクション。エージェントが自動で呼んではいけない（AGENTS.md 参照）。
- 提出前にカーネルが COMPLETE であることを確認する（走行中は提出できない）。
- 既定で対話確認プロンプトを出す。`--yes` で省略できる。

使い方:
    uv run python scripts/ops/submit_lb.py exp020
    uv run python scripts/ops/submit_lb.py exp020 --message "core5→11 移植版" --yes
"""

from __future__ import annotations

import argparse
import json

from build_notebook import EXPERIMENTS_DIR

COMPETITION = "ai-agent-security-multi-step-tool-attacks"
OUTPUT_FILE = "submission.csv"  # 評価器の serve() が生成する採点出力ファイル


def _kernel_slug(exp: str) -> str:
    """kernel-metadata.json の id からカーネルスラッグ（owner/slug）を返す。"""
    meta_path = EXPERIMENTS_DIR / exp / "kernel-metadata.json"
    if not meta_path.exists():
        raise SystemExit(f"[submit-lb] kernel-metadata.json が見つからない: {meta_path}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    kernel_id = meta.get("id")
    if not kernel_id or "/" not in kernel_id:
        raise SystemExit(f"[submit-lb] 不正な kernel id: {kernel_id!r}")
    return kernel_id


def main() -> None:
    parser = argparse.ArgumentParser(description="push 済みカーネルを LB へ提出する（明示指示時のみ）")
    parser.add_argument("exp", help="実験名 (例: exp020)")
    parser.add_argument("--message", "-m", default=None, help="提出メッセージ（既定: 実験名）")
    parser.add_argument("--yes", "-y", action="store_true", help="確認プロンプトを省略")
    args = parser.parse_args()

    kernel = _kernel_slug(args.exp)
    message = args.message or args.exp

    # 遅延 import（kaggle 認証を伴うため、slug 解決の失敗を先に出す）
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    # 走行中は提出できないので COMPLETE を確認
    status = str(api.kernels_status(kernel).status)
    if "COMPLETE" not in status:
        raise SystemExit(
            f"[submit-lb] カーネルが COMPLETE ではありません（status={status}）。"
            f"実行完了を待ってから再実行してください。"
        )

    print(f"[submit-lb] competition = {COMPETITION}")
    print(f"[submit-lb] kernel      = {kernel}（最新版を提出）")
    print(f"[submit-lb] message     = {message!r}")
    print("[submit-lb] 注意: LB 提出は日次上限（5/日・最終2件）を消費します。")

    if not args.yes:
        try:
            reply = input("[submit-lb] 提出しますか？ [y/N] ").strip().lower()
        except EOFError:
            reply = ""
        if reply not in ("y", "yes"):
            print("[submit-lb] 中止しました（提出していません）。")
            return

    resp = api.competition_submit_code(
        file_name=OUTPUT_FILE,
        message=message,
        competition=COMPETITION,
        kernel=kernel,
    )
    print(f"[submit-lb] 提出完了: {resp}")
    print("[submit-lb] 採点状況は `uv run scripts/ops/check_submissions.py` で確認できます。")


if __name__ == "__main__":
    main()
