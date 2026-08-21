"""手元から Kaggle API で attack.py を評価する 1 コマンドの入口。

各モデルについて:
  1) build_eval_notebook.build(exp, model) で build/eval/<exp>/<model>/ を生成
  2) kaggle kernels push -p build/eval/<exp>/<model>
  3) kaggle kernels status <id> を complete/error まで定期確認（ポーリング）
  4) kaggle kernels output <id> -p .../output で scores.json を取得（回収）
最後に全モデルを experiments/<exp>/scores.json にマージし、サマリ表を表示する。

モデルごとに別カーネルにするのは、T4 メモリのメモリ不足（OOM）回避（gpt_oss 12GB / gemma_4 16GB を
同じカーネルで続けてロードしない）と、片方の失敗が他方を巻き込まないため。Kaggle の同時 GPU
枠しだいで順番に実行され得るが、push は全モデルを先に出してから一括で定期確認する。

使い方:
    uv run python scripts/ops/run_eval.py exp001                       # gpt_oss,gemma_4 両方
    uv run python scripts/ops/run_eval.py exp001 --models gpt_oss --candidates 30
    uv run python scripts/ops/run_eval.py exp001 --dry-run             # build のみ（push しない）
    uv run python scripts/ops/run_eval.py exp001 --no-wait             # push のみ（ポーリングしない）
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from build_eval_notebook import EXPERIMENTS_DIR, MODELS, build

POLL_INTERVAL_S = 60
DEFAULT_TIMEOUT_S = 6 * 3600  # 1 カーネルあたりの最大待ち時間
RETRY_ATTEMPTS = 2  # error で終わったときの再 push 再試行（リトライ）回数（Kaggle の一時的な入力マウント失敗対策）


def _kernel_id(out_dir: Path) -> str:
    return json.loads((out_dir / "kernel-metadata.json").read_text())["id"]


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    print(f"[run-eval] $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def _push(out_dir: Path) -> None:
    res = _run(["kaggle", "kernels", "push", "-p", str(out_dir)])
    sys.stdout.write(res.stdout)
    if res.returncode != 0:
        sys.stderr.write(res.stderr)
        raise RuntimeError(f"push に失敗（exit {res.returncode}）: {out_dir}")


def _poll_status(kernel_id: str) -> str:
    """status の文字列を返す: 'complete' | 'error' | 'running'（それ以外は running 扱い）。"""
    res = _run(["kaggle", "kernels", "status", kernel_id])
    text = (res.stdout + res.stderr).lower()
    if "complete" in text:
        return "complete"
    if "error" in text or "cancel" in text:
        return "error"
    return "running"


def _wait_for(kernel_id: str, *, timeout_s: int, interval_s: int) -> str:
    """complete/error になるまで待つ。時間切れなら 'timeout' を返す。"""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status = _poll_status(kernel_id)
        print(f"[run-eval] {kernel_id}: {status}")
        if status in ("complete", "error"):
            return status
        time.sleep(interval_s)
    return "timeout"


def _wait_fetch_with_retry(
    model: str, out_dir: Path, *, timeout_s: int, interval_s: int, max_attempts: int
) -> dict | None:
    """1 モデルについて待機→取得（回収）する。error で終わったら再 push して再試行（リトライ）する。

    Kaggle 側の一時的な入力マウント失敗（競技データが添付されず assert で落ちる等）は、
    再実行で直ることが多いので、error のときだけ再 push して待ち直す。timeout は
    コストが大きいので再試行しない。complete になって scores を取得（回収）できたら返す。
    """
    kid = _kernel_id(out_dir)
    for attempt in range(1, max_attempts + 1):
        status = _wait_for(kid, timeout_s=timeout_s, interval_s=interval_s)
        if status == "complete":
            scores = _fetch_scores(kid, out_dir)
            if scores is not None:
                return scores
            sys.stderr.write(f"[run-eval] {model}: complete だが scores.json を回収できず。\n")
            return None
        sys.stderr.write(f"[run-eval] {model}: 完了せず（{status}, 試行 {attempt}/{max_attempts}）。\n")
        if status == "error" and attempt < max_attempts:
            sys.stderr.write(f"[run-eval] {model}: 一時失敗の可能性。再 push してリトライします。\n")
            _push(out_dir)
    return None


def _fetch_scores(kernel_id: str, out_dir: Path) -> dict | None:
    """kernels output で scores.json を取得（回収）して dict を返す。"""
    output_dir = out_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    res = _run(["kaggle", "kernels", "output", kernel_id, "-p", str(output_dir)])
    sys.stdout.write(res.stdout)
    scores_path = output_dir / "scores.json"
    if not scores_path.is_file():
        sys.stderr.write(f"[run-eval] scores.json が見つかりません: {scores_path}\n")
        return None
    return json.loads(scores_path.read_text())


def _merge_and_save(exp: str, per_model: dict[str, dict]) -> Path:
    """今回採点したモデルの scores を experiments/<exp>/scores.json にマージして保存する。

    既存 scores.json のモデル結果は残したまま、今回採点したモデルだけを上書きする。
    こうすると 1 モデルだけ再 eval しても他モデルの結果が消えない（例: gpt_oss だけ
    再 eval しても既存の gemma_4 結果が残る）。
    """
    out_path = EXPERIMENTS_DIR / exp / "scores.json"
    existing: dict[str, dict] = {}
    if out_path.is_file():
        try:
            existing = json.loads(out_path.read_text()).get("models", {})
        except (json.JSONDecodeError, OSError):
            existing = {}
    merged = {**existing, **per_model}
    payload = {"exp": exp, "models": merged}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"[run-eval] マージ保存: {out_path}（models: {', '.join(merged)}）")
    return out_path


def _print_table(exp: str, per_model: dict[str, dict]) -> None:
    print("\n" + "=" * 64)
    print(f"eval サマリ — {exp}")
    print("=" * 64)
    header = f"{'model':10} {'guardrail':12} {'score':>8} {'raw':>10} {'findings':>9} {'cells':>6}"
    print(header)
    print("-" * len(header))
    for model, data in per_model.items():
        for gname, g in data.get("guardrails", {}).items():
            print(
                f"{model:10} {gname:12} {g['score']:>8.3f} {g['score_raw']:>10.1f} "
                f"{g['findings_count']:>9} {g['unique_cells']:>6}"
            )
    print("=" * 64)
    print("public=公開 LB 相関 / private=非公開汎化の代理。")
    print("public で出て private で消える攻撃は overfit の疑い。")


def main() -> None:
    parser = argparse.ArgumentParser(description="Kaggle API で attack.py を評価（build→push→wait→fetch）")
    parser.add_argument("exp", help="実験名 (例: exp001)")
    parser.add_argument("--models", default=",".join(MODELS), help=f"カンマ区切り（既定: {','.join(MODELS)}）")
    parser.add_argument("--candidates", type=int, default=None, help="候補数の上限（smoke 用）")
    parser.add_argument("--budget-s", type=float, default=8000.0, help="生成フェーズの時間予算（秒）")
    parser.add_argument("--guardrails", default="public,private", help="採点ガードレール")
    parser.add_argument(
        "--dump-events", type=int, default=0, help="先頭 N 候補のツールイベント要約を出す（probe 診断用・既定 0）"
    )
    parser.add_argument("--poll-interval", type=int, default=POLL_INTERVAL_S, help="status ポーリング間隔（秒）")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S, help="1 カーネルの最大待ち時間（秒）")
    parser.add_argument("--dry-run", action="store_true", help="build のみ（push しない）")
    parser.add_argument("--no-wait", action="store_true", help="push のみ（ポーリング/回収しない）")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    for m in models:
        if m not in MODELS:
            parser.error(f"未知の model '{m}'。選択肢: {', '.join(MODELS)}")

    # --- 1) build（全モデル） ---
    out_dirs: dict[str, Path] = {}
    for model in models:
        out_dirs[model] = build(
            args.exp,
            model,
            candidates=args.candidates,
            budget_s=args.budget_s,
            guardrails=args.guardrails,
            dump_events=args.dump_events,
        )

    if args.dry_run:
        print("\n[run-eval] --dry-run: push をスキップ。生成物:")
        for model, d in out_dirs.items():
            print(f"  {model}: {d} (id={_kernel_id(d)})")
        return

    # --- 2) push（全モデル先に push して Kaggle 側で並走させる） ---
    for d in out_dirs.values():
        _push(d)

    if args.no_wait:
        print("\n[run-eval] --no-wait: ポーリングをスキップ。状態は次で確認:")
        for d in out_dirs.values():
            print(f"  kaggle kernels status {_kernel_id(d)}")
        return

    # --- 3) wait + 4) fetch（モデルごと、error は再 push リトライ） ---
    per_model: dict[str, dict] = {}
    for model, d in out_dirs.items():
        scores = _wait_fetch_with_retry(
            model, d, timeout_s=args.timeout, interval_s=args.poll_interval, max_attempts=RETRY_ATTEMPTS
        )
        if scores is not None:
            per_model[model] = scores

    if not per_model:
        sys.stderr.write("[run-eval] 回収できた scores がありません。\n")
        sys.exit(1)

    _merge_and_save(args.exp, per_model)
    _print_table(args.exp, per_model)
    print(f"\n[run-eval] 完了。experiments/{args.exp}/scores.json を docs/SCORE.md の local 列へ反映してください。")


if __name__ == "__main__":
    main()
