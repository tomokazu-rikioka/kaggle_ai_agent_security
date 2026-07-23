# exp023 — canqiang(exp021) 派生: `REPLAY_SAFE_FRAC` 0.97→0.99（cap 押し上げ）

## 位置づけ
土台は exp021（canqiang EA-B 忠実移植・Public 88.560）。**定数 `REPLAY_SAFE_FRAC` を1つだけ** 0.97→0.99 に
上げる単一レバー A/B。他（テンプレ・split・validation-fill・その他定数）は exp021 と完全同一。

## 狙い
`REPLAY_SAFE_SIZING=True`（canqiang 既定）の下で fill を律速するのは `REPLAY_SAFE_FRAC`。これは
`replay_cap = REPLAY_SAFE_FRAC × replay_budget` と `wall_deadline = run_start + REPLAY_SAFE_FRAC × budget` の
**両方**を決める。0.97→0.99 で返却集合の replay 予算を +~2% 押し上げ N_eff を純増させる。

> 注: 当初プランの `FILL_BUDGET_FRAC` レバーは `REPLAY_SAFE_SIZING=True` の下では**死にコード**（fill は
> `_replay_stop` が律速し `FILL_BUDGET_FRAC`/`MARGIN_S` は else 分岐でしか使われない）と実装中に判明。
> 実際に効くレバー `REPLAY_SAFE_FRAC` に差し替えた。

## 根拠
exp018 で exp006 の `REPLAY_SAFE` を 0.99→0.995 に上げても退行しなかった（84.78→84.96）実証があり、この方向は
比較的安全。INVALID リスクはクッションが薄くなる分だけ上がる（攻める方針で承知）。

## 検証（手元）
ruff clean / py_compile OK。env=None → fallback 300。mock live env で fill 経路が正常終了。`REPLAY_SAFE_FRAC=0.99` を確認。

## eval / 提出
health eval で発火・無クラッシュ・非INVALID を確認（local ~27.0 正常）。LB 提出はユーザ明示指示時のみ。

## 結果
- **eval 実施（2026-07-23・gemma・N=2000 uncapped fill・health check）**: public=180.0（EXFIL 2000/2000 全発火・raw36000）・private=0.0（http.post EXFIL の仕様どおり）・**非INVALID・クラッシュ無し＝health OK**。
- fill が local 締切なしで `MAX_REPLAY_FINDINGS=2000` まで到達。100%発火＋線形採点なので **N=300 等価=27.0**（他 fill 行 exp003/006/019/020 と同値）。local 絶対値はランキング信号にならず、public LB 優劣は LB 提出でのみ判定。
- SCORE.md へ反映済み（local_public=27.000 / local_private=0.000、changes 列に uncapped 実測を注記）。
