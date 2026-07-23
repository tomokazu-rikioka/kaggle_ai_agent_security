# exp024 — canqiang(exp021) 派生: `PROBE_HOPS=1` ＋ `REPLAY_BUDGET_MULT=1.15`（穏当な throughput 賭け）

## 位置づけ
土台は exp021（canqiang EA-B 忠実移植・Public 88.560）。**hops=1 fill throughput レバー**を穏当に効かせる。
他（テンプレ・split・validation-fill・`REPLAY_SAFE_FRAC=0.97`・`REPLAY_COST_COEF=1.0`）は exp021 と同一。

## 機構（なぜ効くか／なぜ賭けか）
- `PROBE_HOPS=1` で probe を 1 hop で回すと wrap-up 生成を飛ばし fill が ~1.5-2x 速くなる。fill の wall-clock は
  `REPLAY_SAFE_FRAC × budget` に縛られるので、速い分だけ probe 回数＝発火候補が増える。
- ただし hops=1 単独では N_eff は増えない: replay 会計 `replay_cap = REPLAY_SAFE_FRAC × (budget × REPLAY_BUDGET_MULT)`
  が頭打ちにする。`REPLAY_BUDGET_MULT>1` が「判定器のリプレイ壁が fill 予算より広い」方への賭けで、これがある時だけ
  hops=1 の速さが N_eff 増に変換される（canqiang docstring: hops<8 は MULT>1 と併用してのみ有効）。
- `REPLAY_BUDGET_MULT=1.15`＝壁に ~15% の余裕への穏当な賭け。canqiang: exfil は hop-0 で記録され hops=1/8 で
  発火同一（12/12 実測）なので 1-hop 実測を replay コストに計上（`REPLAY_COST_COEF=1.0` 据置）。
- **当たれば** N_eff が ~1.15-2x に増え 88.56 を上回る余地。**外れる（壁に余裕が無い）と** hops=8 リプレイが
  9000s/モデルを超え `ModelEvaluationTimedOut` → 提出丸ごと VOID。攻める方針で承知の賭け。

## 検証（手元）
ruff clean / py_compile OK。env=None → fallback 300。mock live env で `PROBE_HOPS=1` 経路の fill が正常終了。
`PROBE_HOPS=1` / `REPLAY_BUDGET_MULT=1.15` を確認。
> 注: hops=1 vs hops=8 の**発火同一性・リプレイコスト**は live gpt_oss/gemma でしか実測できない（手元は模擬）。
> これが本 exp の賭けの核心リスク。

## eval / 提出
health eval で発火・無クラッシュを確認（local ~27.0 正常。VOID 判定は live のみ）。LB 提出はユーザ明示指示時のみ。
**提出順は exp024→exp025**（穏当が VOID せず得点したら壁の余裕が実証され、exp025 で更に押す）。

## 結果
- **eval 実施（2026-07-23・gemma・N=2000 uncapped fill・health check）**: public=180.0（EXFIL 2000/2000 全発火・raw36000）・private=0.0（http.post EXFIL の仕様どおり）・**非INVALID・クラッシュ無し＝health OK**。
- fill が local 締切なしで `MAX_REPLAY_FINDINGS=2000` まで到達。100%発火＋線形採点なので **N=300 等価=27.0**（他 fill 行 exp003/006/019/020 と同値）。local 絶対値はランキング信号にならず、public LB 優劣は LB 提出でのみ判定。
- SCORE.md へ反映済み（local_public=27.000 / local_private=0.000、changes 列に uncapped 実測を注記）。
