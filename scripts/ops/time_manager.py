"""提出（submission）の採点完了までの所要時間を計測するモニタ。

いま PENDING の提出をポーリングし、完了したら経過時間と public/private スコアを表示する。
このコンペは kernel 提出なので、`kaggle competitions submissions <slug>` の結果を追う。

使い方:
    uv run scripts/ops/time_manager.py
    uv run scripts/ops/time_manager.py --max 5   # 監視する最新提出数（既定 5）
"""

import argparse
import datetime
import time
from datetime import timezone

from kaggle.api.kaggle_api_extended import KaggleApi

COMPETITION = "ai-agent-security-multi-step-tool-attacks"


def elapsed_minutes(submit_time: datetime.datetime) -> int:
    """提出時刻からの経過分（切り上げ）。UTC naive 同士で引く。"""
    now = datetime.datetime.now(timezone.utc).replace(tzinfo=None)
    return int((now - submit_time).total_seconds() / 60) + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=5, help="監視する最新提出数")
    parser.add_argument("--interval", type=int, default=60, help="ポーリング間隔（秒）")
    args = parser.parse_args()

    api = KaggleApi()
    api.authenticate()

    submissions_list = api.competition_submissions(COMPETITION)
    monitoring = {}
    for submission in submissions_list[: args.max]:
        if str(submission.status) != "SubmissionStatus.COMPLETE":
            monitoring[str(submission.ref)] = {
                "submit_time": submission.date,
                "notified": False,
            }

    print(f"Monitoring {len(monitoring)} submissions...")

    while monitoring:
        current = api.competition_submissions(COMPETITION)
        completed_refs = []
        status_line = []

        for ref, data in monitoring.items():
            for sub in current:
                if str(sub.ref) != ref:
                    continue
                mins = elapsed_minutes(data["submit_time"])
                title = sub.description if sub.description else "No title"
                if str(sub.status) == "SubmissionStatus.COMPLETE" and not data["notified"]:
                    print(
                        f"\n'{title}' completed! "
                        f"public={sub.public_score} private={sub.private_score} ({mins}min)"
                    )
                    data["notified"] = True
                    completed_refs.append(ref)
                elif str(sub.status) != "SubmissionStatus.COMPLETE":
                    status_line.append(f"'{title}': {mins}min")
                break

        for ref in completed_refs:
            del monitoring[ref]

        if monitoring:
            display = " | ".join(status_line) + f" | ({len(monitoring)} remaining)"
            print(f"\r{display}", end="", flush=True)
            time.sleep(args.interval)
        else:
            print("\nAll monitored submissions completed!")


if __name__ == "__main__":
    main()
