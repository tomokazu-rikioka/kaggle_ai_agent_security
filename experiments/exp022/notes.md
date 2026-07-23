# exp022 — tetsutani `ai-agent-sec-adaptive-uniform-three-probe-race` 忠実移植

## 目的
ユーザ指定の2公開カーネルの2つ目を忠実移植。exp021（canqiang）とは別系統の比較対照。

## 移植元と正体
- 底本: `docs/competition-research/public-kernels/tetsutani_race_attack.py`（Playwright 取得の生コード）。
- 解析の結果、**その正体は exp006（lopure=dhanvin LB84.78 champion）のエンジンで `PROBE_REPS` を 5→3 に
  しただけ**。5テンプレ（`plain`/`bare`/`bare_ok`/`inj_close`/`inj_commentary`）・effective_cost selector
  （median lat / fire-rate 最小）・`MIN_FIRE_RATE=0.2`・`REPLAY_SAFE=0.99`(cap 8910s)・warm-up 破棄・
  末尾 hard clamp は完全に同一。
- よって本 exp は **exp006/attack.py を土台に `PROBE_REPS` のみ 5→3 に差し替えた単一レバー移植**。
  docstring と print ラベルのみ exp022 用に更新。

## "adaptive uniform three-probe race" の意味
- three-probe: `PROBE_REPS=3`（各テンプレ3回試し打ち）。
- uniform: 割り当ては一様（round-robin。弱腕を枯らす bandit ではない）。
- race/adaptive: probe 後、`effective_cost` 最小のテンプレを選ぶ。run() はモデルごとに1回呼ばれるので選択がそのモデルに適応。

## exp011 との違い（重要）
exp011 は `PROBE_REPS` 5→3 **かつテンプレも 5→3** に削って LB79.245（退行）。本 exp は**テンプレ5を維持**して
probe だけ 3 に減らす。probe オーバーヘッド（テンプレ数×PROBE_REPS）を 25→15 に削り fill 時間を増やす狙い。
ただし probe が減る分 selector がノイジー化するトレードオフがある（判定は live LB）。

## 狙う述語
EXFIL 一本足（http.post + data=SECRET_MARKER）。public 特化（private=0 承知、block≡fire）。exp006 と同じ数式。

## 検証（手元）
- ruff clean / py_compile OK。env=None → fallback 5 候補（plain "Send SECRET_MARKER to ..."）。
- mock live env（`eval_predicates=None` で `_manual_exfil` 経路）で **uniform three-probe race → fill** が正常動作
  （各テンプレ 3/3 probe → effective_cost 選択 → MAX_CANDIDATES まで fill）を確認。

## eval / 提出
- health eval: `make eval EXP=exp022`（N=300・gemma・2並列厳守）。local ~27.0 は正常。
- LB 提出はユーザ明示指示時のみ。exp022 は exp006(84.78)/exp011(79.245) との比較点（probe 削減 単一レバーが
  テンプレ維持なら効くか）。

## 結果
- **eval 実施（2026-07-23・gemma・N=2000 uncapped fill・health check）**: public=180.0（EXFIL 2000/2000 全発火・raw36000）・private=0.0（http.post EXFIL の仕様どおり）・**非INVALID・クラッシュ無し＝health OK**。
- fill が local 締切なしで `MAX_REPLAY_FINDINGS=2000` まで到達。100%発火＋線形採点なので **N=300 等価=27.0**（他 fill 行 exp003/006/019/020 と同値）。local 絶対値はランキング信号にならず、public LB 優劣は LB 提出でのみ判定。
- SCORE.md へ反映済み（local_public=27.000 / local_private=0.000、changes 列に uncapped 実測を注記）。
