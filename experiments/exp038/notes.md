# exp038 — 両モデル最小トークン単発（出力トークン削減・二次レバー）

Round 6 の 1 本。土台は exp028 エンジン。**TEMPLATES を最短形へ**差し替える純単一レバー A/B。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**。public の通貨は 1候補あたり出力トークン（Ya Xu/owenvallis/souldrive）。
  http.post 自体を最短化して両モデルの出力トークンを削り、9000s の replay に多く詰めて N_eff↑。
- exp033（最短化 + `PROBE_REPS 4→1` の交絡・LB89.05）と違い、**テンプレ最短化のみ**の純単一レバー
  （PROBE_REPS 据え置き）。exp012（短形の盲目採用で退行）を `effective_cost` で回避。

## 変更点（vs exp028）
- pool = verbose(床)/`bare`(positional 最短 `http.post {url} {payload}`)/`lean_ok`(keyed + 一語終端)/forge。
  発火率が落ちる短形は selector が自動排除（fail-closed で verbose 床）。エンジン・0.995 は不変。
- ※支配コストは gpt-oss の deliberation なので効きは exp036/037（deep-forge）に劣る二次枠。

## local の読み方（gemma・N=300）
- **選択形の fire率 ≥ verbose** を stderr の `name:fires/attempts@cost` で確認（下回れば verbose へ縮退＝安全）。
  非クラッシュ・private=0。トークン削減の N_eff 増は live 判定。

## live 安全性
- `REPLAY_SAFE_FRAC=0.995`・probe/fill/replay とも hops=8。best-of で提出。

## 評価結果（make eval）
- `make eval EXP=exp038 CANDIDATES=300`（gemma・N=300・2並列枠厳守）。
- 所見: （eval 後に追記）
- LB: （live 提出はユーザー明示指示時のみ。ここに記入）
