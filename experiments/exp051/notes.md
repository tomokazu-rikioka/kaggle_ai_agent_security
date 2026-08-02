# exp051 — champion(exp028) best-of draw #1

Round 9（public 最大化・best-of バッテリ）の1本。土台は現 champion **exp028（LB 90.99）**。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- Round4-8 で「新レバーは全滅・champion が再現可能天井・同一コードでも GPU 分散で ±1.4〜4 振れる」が確定。
  → **best-of（複数 live 提出の最良採用）が最も確実な公開レバー**。本 exp はその draw #1。

## 変更点（vs exp028）
- **採点候補の生成ロジックはバイト単位で不変**（TEMPLATES・_url・エンジン・`PROBE_REPS=4`・
  `REPLAY_SAFE_FRAC=0.995`・3-arm）。差分は docstring と stderr ラベルのみ＝**live の得点分布は exp028 と同一**。
- 役割: GPU/サーバ分散の独立サンプルを1つ引く（下限＝champion 分散帯）。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。local は N_eff を予測しない（27 天井）。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。所見: （提出後に追記）
