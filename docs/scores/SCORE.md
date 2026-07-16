# 実験スコア一覧

> このファイルは直接編集して運用する（スコアの単一ソース）。
> - `local_*` 列: `/update-score <exp>` スキルが `make eval` 回収の `experiments/<exp>/scores.json` から記入（`gpt_oss > gemma_4` 優先）。`local_agent` は採用モデル名。
> - `lb_public` 列・`changes` 列: 直接記入する（または Claude に依頼）。
> - `local_public` が公開 LB と相関、`local_private` は非公開汎化の代理。
> - スコアは未評価（`make eval` 実施後に記入）。

## 実験一覧

| exp | local_agent | local_public | local_private | lb_public | changes |
|-----|------------|------|------|------|---------|
| exp001 | - | - | - | - | EXFIL(marker)+DEPUTY ブレンド（命令形）・`EXFIL_FRACTION=0.5`・N=300/K=1/M=1。EXFIL=public 主柱＋DEPUTY=public/private 保険の中立ヘッジ |
| exp002 | - | - | - | - | 純DEPUTY（疑問形）・`EXFIL_FRACTION=0.0`・N=300/K=1/M=1。"Could you notify…?"。public/private 両GRで残る CONFUSED_DEPUTY に全振り |
| exp003 | - | - | - | - | 純EXFIL(marker)・`EXFIL_FRACTION=1.0`・N=300/K=1/M=1。http.post の public 穴に全振りする public 特化ヘッジ（private=block≡fire で寄与なし） |
