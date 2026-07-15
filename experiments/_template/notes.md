# expNNN — 実験メモ

> `make new-exp NAME=expNNN` でこのテンプレートを複製したら、本ファイルを書き換える。

## 狙い（仮説）
- どの述語を狙うか（EXFILTRATION / UNTRUSTED_TO_ACTION / DESTRUCTIVE_WRITE / CONFUSED_DEPUTY）:
- ベースラインから何を変えるか:

## 変更点
- `attack.py` の `run()` でやったこと:

## 評価結果（make eval）
- `make eval EXP=expNNN`（gpt_oss / gemma_4 × public/private）:
- 所見（public で出て private で消える＝overfit 疑い など）:
