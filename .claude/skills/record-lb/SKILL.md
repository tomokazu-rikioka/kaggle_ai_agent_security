---
name: record-lb
description: LB 提出の採点完了を監視し、public スコアと所要時間（提出→COMPLETE 検知）を回収して docs/SCORE.md の lb_public 列・lb_time 列へ記録する。トリガー: "LB記録", "LBスコア記録", "採点時間の記録", "提出の時間とスコアを記載", "/record-lb"
---

# record-lb — LB スコアと採点時間の記録

Kaggle へ LB 提出（Edit 画面の Submit）した exp について、**採点完了（COMPLETE）を検知して
`lb_public`（公開スコア）と `lb_time`（提出→完了検知までの経過分）を回収し、`docs/SCORE.md`
に記入する**。SCORE.md はスコアの単一ソースで、スクリプトでは書かず Claude が Edit で反映する。

> このコンペは kernel 提出。採点はキュー込みで概ね **~800〜1000 分（13〜16 時間）** かかる。
> 提出直後は必ず PENDING で、スコアはその場では取れない。時間に余裕を持って回収する。

## 対象 exp の特定
- 引数で対象を受ける。範囲指定 `exp021-exp025`、カンマ列挙 `exp021,exp023`、単体 `exp021` に対応。
- 省略時は文脈上の対象 exp を使い、判らなければユーザに確認。

## 手順

### 1. 状態を取得
取得スクリプト `scripts/ops/record_lb.py` が `kaggle competitions submissions` をポーリングし、
対象 exp ごとに最新提出の `status` / `public` / `time_min`（提出→検知の経過分）を JSON へ書き出す。

- **現状を1回だけ確認（待たない）**。全て COMPLETE なら即記録へ進める:
  ```bash
  uv run scripts/ops/record_lb.py --exps exp021-exp025 --once
  ```
- **まだ PENDING が残る場合**（提出直後など）。完了まで待って確定値を取るなら:
  ```bash
  uv run scripts/ops/record_lb.py --exps exp021-exp025 --wait
  ```
  `--wait` はキュー込みで長時間かかる。この環境では**バックグラウンド bash は kill されがち**なので、
  数時間放置後に改めて `--once` を回して回収する運用が確実。判断は状況に応じて。

出力 JSON（既定 `build/lb_results.json`）の各 exp:
```json
{"exp021": {"status": "COMPLETE", "public": 88.560, "time_min": 812,
            "submit_utc": "2026-07-22 14:43:13", "version": "Version 2"}}
```
- `status` が `PENDING`/`RUNNING` の間は `public=null`・`time_min=経過分`（確定していない）。
- `status=COMPLETE` になって初めて `public` と確定 `time_min` が入る。
- `NOT_FOUND` は該当 exp の提出が submissions 一覧に無い（未提出／description 不一致）。

### 2. docs/SCORE.md を更新
- `docs/SCORE.md` を Read し、対象 exp の行を確認する。
- `status=COMPLETE` の exp について、`lb_public` 列に `public`（小数3桁、例 `88.560`）、
  `lb_time` 列に `time_min` に「分」を付けた値（例 `812分`）を Edit で記入する。
- **`local_*` 列・`changes` 列は既存値を保持する**（この skill は LB 列のみ触る）。
  local スコアの反映は `/update-score` の担当。
- 列数・区切り（`|`）がズレないよう Markdown テーブルの整合を保つ。
- `PENDING`/`RUNNING` のままの exp は**まだ記入しない**（`-` のまま残す）。完了後に再回収する。
- スコアが空欄で COMPLETE のケース（過去 exp017/019 V2 等）は INVALID / 出力なしの疑い。
  `lb_public` は空欄のままにし、`changes` 列にその旨を追記するかユーザに確認する。

### 3. 報告
- どの exp をどう記入したか（before → 記入値）を簡潔に伝える。
- まだ PENDING の exp があれば、その旨と経過分・目安（~800〜1000 分で完了）を伝え、
  後で再実行（`--once`）して回収する段取りを示す。

## 注意
- スコアの単一ソースは `docs/SCORE.md`。yaml 入力ファイルは作らない。SCORE.md はスクリプトで書かない。
- `lb_time` は「提出→COMPLETE **検知**までの経過分」。`--wait` で完了を検知した瞬間の分数が確定値。
  後追いの `--once` で拾う場合は「現在時刻−提出時刻」になり検知遅れ分だけ上振れする（上限目安として扱う）。
- Kaggle の日次提出上限（5/日）や提出操作自体はこの skill の対象外。提出は Edit 画面から手動・
  ユーザ明示指示時のみ（CLAUDE.md 参照）。この skill は**記録のみ**で提出はしない。
- description のマッチは `script exp\d{3}` 正規表現。タイトル命名を変えた場合は
  `scripts/ops/record_lb.py` の `EXP_RE` を合わせる。
