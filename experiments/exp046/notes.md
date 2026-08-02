# exp046 — per-model forge-routing single-commit（Round8）

Round8（public best・探索 swing 全振り）の1本。土台 exp028（LB 90.99）。

## 狙い（単一レバー＝lean 除去で 2-arm 化）
- 研究（2026-07-29）で Cleanor Labs（disc 728174）が開示した現行フロンティア: 「gpt_oss 行のみ
  harmony analysis-channel forge で latency ~3倍（1.16s vs 4s）・低分散。**gemma では format error で
  壊れるのでモデル別ルーティング必須**。自然言語の skip analysis は無効」。
- champion(exp028) の `effective_cost=median_lat÷fire_rate` 選択器は、テンプレを **{verbose, forge}
  の 2-arm** にすると自然に per-model ルーティングする（gpt_oss→forge・gemma→verbose）。lean を落とす
  ことで probe を 3×PROBE_REPS → 2×PROBE_REPS に減らし fill 時間を回収する。

## 変更点（vs exp028・単一差分）
- `TEMPLATES` を `(verbose, forge)` の 2-arm に（`lean` 除去）。**他の定数・selector・fill・
  replay-safe sizing は exp028 とバイト一致**。
- 期待: lean が gemma で実質速度優位を出していなければ probe 回収で N_eff 純増→ LB > 90.99。
  出していれば verbose 床へ縮退（fail-closed・下限は champion 分散帯）。

## landmine 回避（確認済み）
- URL/payload は英字のみ（`aa.co`/`SECRET_MARKER`）で gemma int 化 TypeError 無し。1生成1 tool call。
  probe も hops=8。replay-safe hard 停止で VOID 回避。

## 検証（eval 最小化・LB 直行）
- `make eval EXP=exp046`（gemma N=300）: 健全性のみ（gemma では forge 除外→verbose 選択・fire率
  =verbose・無クラッシュ・private=0）。gpt_oss の forge 効果は local(gemma) では見えない→判定は live。
- 所見/LB: （提出後に追記）
