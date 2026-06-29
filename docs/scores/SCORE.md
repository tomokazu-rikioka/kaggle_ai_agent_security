# 実験スコア一覧

> このファイルは直接編集して運用する（スコアの単一ソース）。
> - `local_*` 列: `/update-score <exp>` スキルが `validation/runs/<exp>/summary_*.json` から記入。
> - `lb_*` 列・`changes` 列: 直接記入する（または Claude に依頼）。
> - `local_public` が公開 LB と相関、`local_provenance`/`local_strict` は非公開汎化の代理。

| exp | local_agent | local_public | local_provenance | local_strict | lb_gpt_oss_public | lb_gpt_oss_private | lb_gemma_public | lb_gemma_private | changes |
|-----|------------|------|------|------|------|------|------|------|---------|
| exp001 | deterministic | 0.000 | 0.000 | 0.000 | - | - | - | - | EXFIL リプレイ密度 + CONFUSED_DEPUTY ブレンド（EXFIL_FRACTION=0.5, N=620）。実モデルは Kaggle 検証待ち |
