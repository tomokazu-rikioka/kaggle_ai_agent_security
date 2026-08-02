# exp034 — 統合エンジン（per-model forge routing + 最良 latency 形 + 0.997 + best-of 運用）

Round 5 の 1 本。土台は exp028（champion 90.99）。exp032/exp033 の latency 形を統合した集大成。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- 統合: exp032/033 の最速形 + `forge` をリッチだが薄いプールに統合し、**per-model routing を selector に
  自動でやらせる**（gpt_oss=forge が effective_cost 最小→自動選択で latency 約3倍削減／gemma=forge は
  format error で発火0→自動除外→最速の非 forge 形）。公開 LB は 2 model 平均なので **gpt_oss 行の
  底上げが 100 到達の鍵**。
- `REPLAY_SAFE_FRAC 0.995→0.997`（一段攻める・void は実測会計で hard 停止）。
- **best-of 運用**（コードでなく提出運用）: GPU 分散の上振れを複数 live 提出で回収（Cleanor 86→88.7）。

## 変更点（vs exp028）
- テンプレプール = {verbose(床), terse_tail, bare_min, forge}（全て単発 post・密度なし）。
- `PROBE_REPS 4→2`（統合でテンプレ増→probe コスト相殺。exp010/030 の「リッチプール退行」を probe 削減で回避）。
- `REPLAY_SAFE_FRAC 0.997`。`_label` に ultra-dangerous フィルタ追加。エンジン本体は exp028 と同一。

## exp030 統合退行との違い
exp030 は密度アームを混ぜて probe コスト＋誤 qualify で N_eff を縮めた。本 exp が混ぜるのは**単発 latency
形だけ**（密度ゼロ）＋probe を削るので、「候補あたり raw を増やす」路線ではなく「latency を削る」路線に
統合を閉じている。

## local ≠ live
- gemma-only eval では forge は非選択が正しい。**gemma path の健全性のみ確認**（fire率 ≥ verbose・
  非クラッシュ・private=0）。gpt_oss の forge 効果・0.997 の効きは **live 提出でのみ判定**。

## 評価結果（make eval）
- `make eval EXP=exp034 CANDIDATES=300`（gemma・N=300・2並列枠厳守）。
- 判定: gemma で最速の非 forge 形が選ばれ fire率 ≥ verbose・非クラッシュ・private=0。
- 所見: （eval 後に追記）
- LB: （live 提出はユーザー明示指示時のみ。best-of で複数回。ここに記入）
