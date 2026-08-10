"""提出（submission）の採点状況を1回だけ確認するスナップショット出力。

`time_manager.py` は完了まで居座るポーリング（Monitor から背景で張る）だが、これは1回問い合わせて
現在の PENDING / COMPLETE と public/private スコア・経過分を出すだけの非ブロッキング版。
セッションが切れて監視が途切れたあと、日をまたいで結果を回収するときに使う（`/lb-submit` 手順6）。
日次提出枠（5/日）の残りを数えるのにも使う。

使い方:
    uv run scripts/ops/check_submissions.py            # 最新10件を表示
    uv run scripts/ops/check_submissions.py --max 15
"""

import argparse
import datetime

from kaggle.api.kaggle_api_extended import KaggleApi

COMPETITION = "ai-agent-security-multi-step-tool-attacks"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=10, help="表示する最新提出数")
    args = parser.parse_args()

    api = KaggleApi()
    api.authenticate()
    subs = api.competition_submissions(COMPETITION)
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    for s in subs[: args.max]:
        mins = int((now - s.date).total_seconds() / 60) + 1
        status = str(s.status).replace("SubmissionStatus.", "")
        desc = s.description or "No title"
        print(f"{s.ref} | {status} | pub={s.public_score} priv={s.private_score} | {mins}min | {desc}")


if __name__ == "__main__":
    main()
