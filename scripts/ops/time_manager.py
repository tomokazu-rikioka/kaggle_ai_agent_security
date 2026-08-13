"""LB 提出（submission）の採点完了を監視し、public スコアと所要時間を1行ずつ報告するモニタ。

`/lb-submit` スキルから **Monitor ツールで背景に張って**使う前提で、
**1 ポーリング＝改行付き 1 行**を stdout に流す（1 行がそのまま 1 通知になる）。
既定の間隔は 1 時間なので、放っておくと1時間おきに状況が届く。

このコンペは kernel 提出なので `kaggle competitions submissions <slug>` の結果を追う。
起動時点で既に COMPLETE の提出は「後追い」として即報告するので、
採点が終わったあとに1回だけ回して結果を回収する使い方もできる。

使い方:
    # exp を指定して監視（推奨）。範囲 / カンマ列挙 / 単体に対応。
    uv run scripts/ops/time_manager.py --exps exp076-exp080

    # exp 指定なし。最新 --max 件のうち未完了のものを監視。
    uv run scripts/ops/time_manager.py --max 5 --interval 600

出力（すべて改行付き・flush 済みの 1 行）:
    [monitor]  監視開始: exp076,exp077 (2件) interval=3600s
    [status]   exp076=PENDING(60min) exp077=PENDING(60min)
    [done]     exp076 COMPLETE public=88.155 private=- 952min
    [failed]   exp077 ERROR 120min
    [all-done] 2件すべて終了
    [error]    submissions の取得に失敗: ...        ← 非ゼロ終了

`public=-` は「COMPLETE だがスコアが空」＝ VOID（live の時間切れ）を意味する。
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
import time
from typing import Any

from kaggle.api.kaggle_api_extended import KaggleApi

COMPETITION = "ai-agent-security-multi-step-tool-attacks"
# 提出 description から exp 名を拾う（例: "AI Agent Security - Attack script exp076 | Version 2"）。
# 実提出の既定文は "Attack script expNNN"。"script" 有無どちらも拾えるようにしておく。
EXP_RE = re.compile(r"Attack\s+(?:script\s+)?(exp\d{3})", re.IGNORECASE)


def emit(line: str) -> None:
    """1 行 1 イベントとして stdout へ流す（Monitor がこの 1 行を 1 通知にする）。"""
    print(line, flush=True)


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


def elapsed_minutes(submit_time: datetime.datetime) -> int:
    """提出時刻からの経過分（切り上げ）。UTC naive 同士で引く。"""
    return int((_now_utc() - submit_time).total_seconds() / 60) + 1


def parse_exps(spec: str) -> list[str]:
    """`exp021-exp025` / `exp021,exp023` / `exp021` を exp 名リストへ展開する。"""
    out: list[str] = []
    for raw in spec.split(","):
        token = raw.strip()
        if not token:
            continue
        m = re.fullmatch(r"exp(\d{3})-exp(\d{3})", token)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            out.extend(f"exp{n:03d}" for n in range(lo, hi + 1))
        else:
            out.append(token.lower())
    seen: set[str] = set()
    return [e for e in out if not (e in seen or seen.add(e))]


def status_of(sub: Any) -> str:
    """`SubmissionStatus.COMPLETE` を `COMPLETE` に短縮して返す。"""
    return str(sub.status).replace("SubmissionStatus.", "")


def exp_of(sub: Any) -> str | None:
    """提出 description から exp 名を取り出す（取れなければ None）。"""
    m = EXP_RE.search(sub.description or "")
    return m.group(1).lower() if m else None


def fetch(api: KaggleApi) -> list[Any]:
    """submissions 一覧（新しい順）を取得。一時エラーは1回だけリトライする。"""
    for attempt in (1, 2):
        try:
            return list(api.competition_submissions(COMPETITION))
        except Exception as exc:  # noqa: BLE001 - API 側の例外種別は不定
            if attempt == 2:
                emit(f"[error] submissions の取得に失敗: {exc}")
                sys.exit(1)
            time.sleep(10)
    return []


def pick_targets(subs: list[Any], exps: list[str], max_n: int) -> list[dict[str, Any]]:
    """監視対象を選ぶ。exps 指定時は exp ごとに最新1件、未指定時は最新 max_n 件。"""
    targets: list[dict[str, Any]] = []
    if exps:
        found: set[str] = set()
        for sub in subs:  # 新しい順なので最初に当たったものが最新
            exp = exp_of(sub)
            if exp in exps and exp not in found:
                found.add(exp)
                targets.append({"key": exp, "ref": str(sub.ref), "submit_time": sub.date, "sub": sub})
        missing = [e for e in exps if e not in found]
        if missing:
            emit(f"[monitor] 提出が見つからない exp: {','.join(missing)}")
    else:
        for sub in subs[:max_n]:
            key = exp_of(sub) or str(sub.ref)
            targets.append({"key": key, "ref": str(sub.ref), "submit_time": sub.date, "sub": sub})
    return targets


def _score(value: Any) -> str:
    """スコア表示。空（VOID）は "-"。"""
    return "-" if value in (None, "") else str(value)


def done_line(key: str, sub: Any, minutes: int, *, late: bool = False) -> str:
    """完了1件の報告行。late=True は起動時点で既に完了していた（後追い＝上限目安）ケース。"""
    mark = "（後追い・上限目安）" if late else ""
    return (
        f"[done] {key} COMPLETE public={_score(sub.public_score)} "
        f"private={_score(sub.private_score)} {minutes}min{mark}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="LB 提出の採点完了を監視する")
    parser.add_argument("--exps", default=None, help="対象 exp。例: exp076-exp080 / exp076,exp078 / exp076")
    parser.add_argument("--max", type=int, default=5, help="--exps 未指定時に監視する最新提出数")
    parser.add_argument("--interval", type=int, default=3600, help="ポーリング間隔（秒）。既定は1時間")
    args = parser.parse_args()

    exps = parse_exps(args.exps) if args.exps else []

    api = KaggleApi()
    api.authenticate()

    targets = pick_targets(fetch(api), exps, args.max)
    if not targets:
        emit("[monitor] 対象の提出が見つかりません")
        return

    # 起動時点で終端状態のものは「後追い」として即報告し、監視対象からは外す。
    pending: dict[str, dict[str, Any]] = {}
    for t in targets:
        status = status_of(t["sub"])
        if status == "COMPLETE":
            emit(done_line(t["key"], t["sub"], elapsed_minutes(t["submit_time"]), late=True))
        elif status == "ERROR":
            emit(f"[failed] {t['key']} ERROR {elapsed_minutes(t['submit_time'])}min（後追い）")
        else:
            pending[t["ref"]] = t

    if not pending:
        emit("[all-done] 監視対象の未完了提出はありません")
        return

    keys = ",".join(t["key"] for t in pending.values())
    emit(f"[monitor] 監視開始: {keys} ({len(pending)}件) interval={args.interval}s")

    total = len(pending)
    while pending:
        time.sleep(args.interval)
        current = {str(s.ref): s for s in fetch(api)}
        for ref in list(pending):
            t = pending[ref]
            sub = current.get(ref)
            if sub is None:
                continue
            status = status_of(sub)
            if status == "COMPLETE":
                emit(done_line(t["key"], sub, elapsed_minutes(t["submit_time"])))
                del pending[ref]
            elif status == "ERROR":
                emit(f"[failed] {t['key']} ERROR {elapsed_minutes(t['submit_time'])}min")
                del pending[ref]
        if pending:
            parts = " ".join(
                f"{t['key']}={status_of(current[ref]) if ref in current else 'NOT_FOUND'}"
                f"({elapsed_minutes(t['submit_time'])}min)"
                for ref, t in pending.items()
            )
            emit(f"[status] {parts}")

    emit(f"[all-done] {total}件すべて終了")


if __name__ == "__main__":
    main()
