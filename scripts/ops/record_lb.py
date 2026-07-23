"""LB 提出の採点完了を監視し、public スコアと所要時間（提出→COMPLETE 検知）を回収する。

`docs/SCORE.md` の `lb_public` 列・`lb_time` 列を埋めるための取得スクリプト。
このコンペは kernel 提出なので `kaggle competitions submissions <slug>` の結果を追う。

出力は JSON（既定は scratchpad へ）で、対象 exp ごとに次を持つ:
  {"exp021": {"status": "COMPLETE", "public": 88.560, "time_min": 812,
              "submit_utc": "2026-07-22 14:43:13", "version": "Version 2"}, ...}

SCORE.md への転記は Claude が Edit で行う（SCORE.md はスクリプトで書かない運用のため）。

使い方:
    # 現状を1回だけ確認（待たない）。PENDING は time_min=経過分・public=None のまま。
    uv run scripts/ops/record_lb.py --exps exp021-exp025 --once

    # 全対象が COMPLETE になるまでポーリングし、確定 public と確定 time_min を回収。
    uv run scripts/ops/record_lb.py --exps exp021-exp025 --wait

    # 出力先を指定
    uv run scripts/ops/record_lb.py --exps exp021 --out /path/lb_results.json
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import time
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

COMPETITION = "ai-agent-security-multi-step-tool-attacks"
# 提出 description に含まれる exp 名を拾う（例: "... Attack script exp021 | Version 2"）。
EXP_RE = re.compile(r"script\s+(exp\d{3})", re.IGNORECASE)


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


def elapsed_minutes(submit_time: datetime.datetime, until: datetime.datetime | None = None) -> int:
    """提出時刻からの経過分（切り上げ）。UTC naive 同士で引く。"""
    end = until or _now_utc()
    return int((end - submit_time).total_seconds() / 60) + 1


def parse_exps(spec: str) -> list[str]:
    """"exp021-exp025" / "exp021,exp023" / "exp021" を exp 名リストへ展開する。"""
    out: list[str] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        m = re.fullmatch(r"exp(\d{3})-exp(\d{3})", token)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            out.extend(f"exp{n:03d}" for n in range(lo, hi + 1))
        else:
            out.append(token)
    # 重複除去（順序保持）
    seen: set[str] = set()
    return [e for e in out if not (e in seen or seen.add(e))]


def latest_by_exp(api: KaggleApi, targets: set[str]) -> dict[str, object]:
    """対象 exp ごとに最新（先頭）の提出を返す。submissions は新しい順。"""
    found: dict[str, object] = {}
    for sub in api.competition_submissions(COMPETITION):
        m = EXP_RE.search(sub.description or "")
        if not m:
            continue
        exp = m.group(1).lower()
        if exp in targets and exp not in found:
            found[exp] = sub
    return found


def snapshot(api: KaggleApi, exps: list[str], detected: dict[str, int]) -> dict[str, dict]:
    """現時点の各 exp の状態を dict 化。detected[exp]=完了検知時の time_min（確定用）。"""
    subs = latest_by_exp(api, set(exps))
    result: dict[str, dict] = {}
    for exp in exps:
        sub = subs.get(exp)
        if sub is None:
            result[exp] = {"status": "NOT_FOUND", "public": None, "time_min": None}
            continue
        status = str(sub.status).replace("SubmissionStatus.", "")
        complete = status == "COMPLETE"
        # 完了検知済みならその瞬間の分数を確定値に、未完なら現在までの経過分。
        time_min = detected.get(exp) if complete else elapsed_minutes(sub.date)
        public = sub.public_score if complete else None
        result[exp] = {
            "status": status,
            "public": float(public) if public not in (None, "") else None,
            "time_min": time_min,
            "submit_utc": str(sub.date),
            "version": (sub.description or "").split("|")[-1].strip() or None,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exps", required=True, help="対象 exp。例: exp021-exp025 / exp021,exp023")
    parser.add_argument("--wait", action="store_true", help="全対象が COMPLETE になるまでポーリング")
    parser.add_argument("--once", action="store_true", help="1回だけ確認して終了（既定）")
    parser.add_argument("--interval", type=int, default=120, help="ポーリング間隔（秒）")
    parser.add_argument("--out", default=None, help="結果 JSON の出力先")
    args = parser.parse_args()

    exps = parse_exps(args.exps)
    out_path = Path(args.out) if args.out else Path("build") / "lb_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    api = KaggleApi()
    api.authenticate()

    # 完了を検知した瞬間の経過分を記録（確定 time_min）。
    detected: dict[str, int] = {}

    def poll_once() -> dict[str, dict]:
        subs = latest_by_exp(api, set(exps))
        for exp in exps:
            sub = subs.get(exp)
            if sub is None or exp in detected:
                continue
            if str(sub.status) == "SubmissionStatus.COMPLETE":
                detected[exp] = elapsed_minutes(sub.date)
        return snapshot(api, exps, detected)

    snap = poll_once()
    if args.wait:
        while any(v["status"] not in ("COMPLETE", "NOT_FOUND") for v in snap.values()):
            pending = [e for e, v in snap.items() if v["status"] not in ("COMPLETE", "NOT_FOUND")]
            line = " | ".join(f"{e}:{snap[e]['status']}({snap[e]['time_min']}min)" for e in pending)
            print(f"\r待機中: {line}", end="", flush=True)
            time.sleep(args.interval)
            snap = poll_once()
        print()

    out_path.write_text(json.dumps(snap, ensure_ascii=False, indent=2))
    print(f"\n書き出し: {out_path}\n")
    for exp in exps:
        v = snap[exp]
        pub = "-" if v["public"] is None else f"{v['public']:.3f}"
        tmin = "-" if v["time_min"] is None else f"{v['time_min']}分"
        print(f"  {exp}: status={v['status']:9s} lb_public={pub:8s} lb_time={tmin}")


if __name__ == "__main__":
    main()
