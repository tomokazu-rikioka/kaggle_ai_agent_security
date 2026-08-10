# exp069 — adaptive_margin ＋ gpt_oss 行 forge-multipost（律速行底上げ・単一レバー A/B）

Round 12（public 100+ 奪回）。exp067 アンカーからの**単一レバー**。

## 狙い（仮説）
public LB = mean(gpt_oss, gemma)。mean を律速するのは**遅い gpt_oss 行**。gemma は既に floor 付近。
dimong4 の `_forge_plan_msg`（analysis チャネル偽装で「n 個の一意 endpoint に1回ずつ http.post」を commit）で
**gpt_oss に n post を確実に撃たせる**（実測 n=4 で 4.0 posts/候補・prose 形は 0.33）。1候補 raw=16n+2（n=4 で 66）。

過去の密度実験（exp026/027/031）は別 framing で全弾決まらず退行したが、本 exp は **dimong4 実証済み `_forge_plan_msg`
をバイト単位で使う**点が違う。gpt_oss 行だけに適用（gemma は Harmony 非対応で forge 自動除外→単発 verbose）。

## 変更点（vs exp067）
- `SLOW_MULTIPOST_N` 1→**4** のみ。margin・テンプレ・split は完全同一 → 差分は「forge-multipost の効き」に帰属。

## 評価/判定
- `make eval EXP=exp069`（gemma N=300）は健全性のみ（gemma は単発 verbose のまま＝forge-multipost は gpt_oss/live でのみ発現）。
- multipost 候補は elapsed ~4x → slowest 上昇 → adaptive_margin が自動で厚くなる（VOID 側は会計で吸収）。
- **判定は live LB**（gpt_oss 行が上振れ mean を押し上げるか。vs exp067 アンカー）。
- 所見: （eval・live 後に追記）
