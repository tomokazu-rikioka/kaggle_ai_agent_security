# exp025 — canqiang(exp021) 派生: `PROBE_HOPS=1` ＋ `REPLAY_BUDGET_MULT=1.35`（強気の throughput 賭け）

## 位置づけ
土台は exp021（canqiang EA-B 忠実移植・Public 88.560）。exp024 と同じ hops=1 throughput 賭けを**より強く**押す
（`REPLAY_BUDGET_MULT` 1.15→1.35）。他（テンプレ・split・validation-fill・`REPLAY_SAFE_FRAC=0.97`・
`PROBE_HOPS=1`）は exp024 と同一。exp023-025 の中で最もアグレッシブ。

## 機構
`REPLAY_BUDGET_MULT=1.35`＝「判定器のリプレイ壁が fill 予算より ~35% 広い」への強めの賭け。当たれば hops=1 の
速さで N_eff が更に増える。外れると hops=8 リプレイが 9000s を超え VOID（提出丸ごと失格）。機構の詳細は exp024
notes を参照（本 exp はその上限側 A/B）。

## 提出順
**exp024(=1.15) → exp025(=1.35)**。exp024 が VOID せず 88.56 超で得点した場合に、リプレイ壁の余裕をどこまで
取れるかを探る上限側。exp024 が VOID したら壁に余裕が無い証拠なので exp025 は出さない（LB 枠の無駄を避ける）。

## 検証（手元）
ruff clean / py_compile OK。env=None → fallback 300。mock live env で fill が正常終了。
`PROBE_HOPS=1` / `REPLAY_BUDGET_MULT=1.35` を確認。VOID 判定は live のみ。

## eval / 提出
health eval で発火・無クラッシュを確認（local ~27.0 正常）。LB 提出はユーザ明示指示時のみ。

## 結果
- **eval 実施（2026-07-23・gemma・N=2000 uncapped fill・health check）**: public=180.0（EXFIL 2000/2000 全発火・raw36000）・private=0.0（http.post EXFIL の仕様どおり）・**非INVALID・クラッシュ無し＝health OK**。
- fill が local 締切なしで `MAX_REPLAY_FINDINGS=2000` まで到達。100%発火＋線形採点なので **N=300 等価=27.0**（他 fill 行 exp003/006/019/020 と同値）。local 絶対値はランキング信号にならず、public LB 優劣は LB 提出でのみ判定。
- SCORE.md へ反映済み（local_public=27.000 / local_private=0.000、changes 列に uncapped 実測を注記）。
