# exp049 — forge-routing ＋ URL 圧縮の統合（Round8）

Round8（public best・探索 swing 全振り）の統合枠。土台 exp028（LB 90.99）。

## 狙い（exp046 ＋ exp047 の両取り＝現行評価器で再現可能な最良 recipe）
- **forge routing**（exp046）: gpt_oss 行のみ harmony forge（Cleanor 開示・latency ~3倍・低分散）。
- **URL 圧縮**（exp047）: 勝ちアーム（forge/min）を schemeless 圧縮 url（`aa.co`）にして生成トークン最小化。
- 46/47 が個別に効くなら統合で最上端を狙う。強い best-of ドローも兼ねる。

## 変更点（vs exp028）
- `_url(i)` = 素のラベル、scheme/TLD はテンプレ側（exp047 の圧縮基盤）。
- `TEMPLATES` = 3-arm `verbose`(full url 床) / `forge_min`(圧縮 forge・本命) / `min`(圧縮最短)。
  gpt_oss→forge_min / gemma→min（落ちれば verbose 床）を effective_cost が自動ルーティング。
- selector・fill・replay-safe sizing・定数は exp028 と同一。

## fail-closed
- 圧縮/forge が全滅しても full url の `verbose` 床が残る（fire≥0.5 の中で最小 effective_cost を選択）。
- landmine: ラベル英字＋数字 suffix（非全数字・非危険語・一意 cell）／1生成1 tool call／probe hops=8／replay-safe hard 停止。

## 検証（eval 最小化・LB 直行）
- `make eval EXP=exp049`（gemma N=300）: 健全性のみ（gemma で `min` 発火・fire率≥verbose・無クラッシュ・private=0）。
  forge 効果は gpt_oss/live でのみ→判定は live LB（vs exp028・exp046・exp047）。
- 所見/LB: （提出後に追記）
