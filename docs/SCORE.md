# 実験スコア一覧

> 用語は [用語集](用語集.md) を参照。知見の入口は [knowledges/](knowledges/README.md)。

> このファイルは直接編集して運用する（スコアの単一ソース）。
> - `local_*` 列: `make eval` で取得（回収）した `experiments/<exp>/scores.json` を読んで記入する（`gpt_oss > gemma_4` 優先）。`local_agent` は採用したモデル名。
> - `lb_public` 列・`lb_time` 列: `/lb-submit` スキルが提出から採点完了まで追い、`scripts/ops/time_manager.py` の出力から記入する。
> - `lb_time` の意味: 提出（submit）から採点 COMPLETE 検知までの経過時間（分）。キュー待ちを含むので実採点時間の上限目安。
> - `changes` 列: 直接記入する（または Claude に依頼）。
> - `local_public` が公開 LB と相関し、`local_private` は非公開への汎化の代理。

> **exp001–080（Round1–14）の実測値は [knowledges/08-実験アーカイブ.md](knowledges/08-実験アーカイブ.md) に移した。**
> この表は exp081 以降を記録する。

## 実験一覧

| exp | local_agent | local_public | local_private | lb_public | lb_time | changes |
|-----|------------|------|------|------|------|---------|
