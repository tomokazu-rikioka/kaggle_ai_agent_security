"""提出（submission）の採点状況を1回だけ確認するスナップショット出力。

`time_manager.py` はブロッキングのポーリングだが、これは1回問い合わせて
現在の PENDING / COMPLETE と public/private スコア・経過分を出すだけの非ブロッキング版。
1時間おきの定期確認から呼ぶ想定。

使い方:
    uv run scripts/ops/check_submissions.py            # 最新10件を表示
    uv run scripts/ops/check_submissions.py --max 15
"""

import argparse
import datetime
from datetime import timezone

from kaggle.api.kaggle_api_extended import KaggleApi

COMPETITION = "ai-agent-security-multi-step-tool-attacks"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=10, help="表示する最新提出数")
    args = parser.parse_args()

    api = KaggleApi()
    api.authenticate()
    subs = api.competition_submissions(COMPETITION)
    now = datetime.datetime.now(timezone.utc).replace(tzinfo=None)

    for s in subs[: args.max]:
        mins = int((now - s.date).total_seconds() / 60) + 1
        status = str(s.status).replace("SubmissionStatus.", "")
        desc = s.description or "No title"
        print(
            f"{s.ref} | {status} | pub={s.public_score} priv={s.private_score} "
            f"| {mins}min | {desc}"
        )


if __name__ == "__main__":
    main()
