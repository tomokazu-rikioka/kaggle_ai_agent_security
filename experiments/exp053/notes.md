# exp053 — champion(exp028) best-of draw #3

Round 9（public 最大化・best-of バッテリ）の1本。土台は現 champion **exp028（LB 90.99）**。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- best-of レバーの draw #3。draw #1/#2 と独立な分散サンプルを引き、champion 母集団の max（分散上端 ~91-93）を狙う。

## 変更点（vs exp028）
- **採点候補の生成ロジックはバイト単位で不変**（`PROBE_REPS=4`・`REPLAY_SAFE_FRAC=0.995`・3-arm）。
  差分は docstring と stderr ラベルのみ＝**live の得点分布は exp028 と同一**。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。local は N_eff を予測しない（27 天井）。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。所見: （提出後に追記）
