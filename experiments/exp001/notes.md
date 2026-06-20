# expNNN — 実験メモ

> `make new-exp NAME=expNNN` でこのテンプレートを複製したら、本ファイルを書き換える。

## 狙い（仮説）
- どの述語を狙うか（EXFILTRATION / UNTRUSTED_TO_ACTION / DESTRUCTIVE_WRITE / CONFUSED_DEPUTY）:
- ベースラインから何を変えるか:

## 変更点
- `attack.py` の `run()` でやったこと:

## ローカル検証結果
- `make validate EXP=expNNN`（deterministic・ロジック層）:
- `make validate-real EXP=expNNN`（gpt_oss / gemma_4・実モデル）:
- 所見（public で出て strict/provenance で消える＝overfit 疑い など）:

## LB 結果
- 提出日 / Version:
- gpt_oss_public / gpt_oss_private / gemma_public / gemma_private:

## 次にやること
-
