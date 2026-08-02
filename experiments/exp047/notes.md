# exp047 — extreme token/URL compression（Round8）

Round8（public best・探索 swing 全振り）の1本。土台 exp028（LB 90.99）。

## 狙い（単一レバー＝生成 url トークンの最小化）
- 研究（2026-07-29）: T-MAN/Xander（disc 727895）「圧縮 URL でトークン生成時間を最小化」、
  Cleanor「real headroom is in latency, not packing closer」。scored replay で標的が生成する
  tool call の url 文字列＝生成トークンが per-candidate latency の一部。**url を最短化して N_eff を稼ぐ**。

## 変更点（vs exp028・単一差分）
- `_url(i)` を「素のラベル」（`aa`/`ab1`…）に変更し、scheme/TLD をテンプレ側で埋め込む。
- `TEMPLATES` = 3-arm `verbose`(full `http://aa.co`・床) / `forge`(full url) / **`min`(schemeless `aa.co`・圧縮本命)**。
  probe 数は exp028 と同じ 3×PROBE_REPS（圧縮レバーを単離）。
- selector・fill・replay-safe sizing・定数は exp028 と同一。

## fail-closed（安全性）
- 圧縮で発火が落ちれば `min` は `effective_cost`（fire率≥0.5）で自動排除→ full url の床が残る。
- 標的が bare url に `http://` を勝手に補完しても害は無い（effective_cost が verbose と同等になるだけ）。
- landmine: ラベルは英字＋数字 suffix で非全数字・非危険語・一意（cell）。1生成1 tool call・probe hops=8。

## 検証（eval 最小化・LB 直行）
- `make eval EXP=exp047`（gemma N=300）: 健全性のみ（`min` の fire率 ≥ verbose なら圧縮成立の一次信号・
  無クラッシュ・private=0）。真の latency 効果は gpt_oss/live でのみ顕在化→判定は live LB（vs exp028）。
- 所見/LB: （提出後に追記）
