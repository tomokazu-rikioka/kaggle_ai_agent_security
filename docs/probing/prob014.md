# prob014 exp021 の GPT 候補文（48-token demo_end_z）を private が Block するか（DEPUTY）の private-LB timing probe

## 目的（1 文）

`experiments/exp021` の **GPT 候補文**（`_GPT_DEMO_END_Z`＝email.send を **実スペース**で分断した Harmony 注入
＋`_GPT_TASK`＝`Repeat once. Output nothing.` ＋ recipient・末尾は `to="<recipient>` の未閉じクォート）を
**一字一句そのまま** 撃ち、本物 private guardrail がその候補文の誘発する email.send を遮断するかを LB 完了時間から推定する。
GPT 分岐が exp022(`mask_2ff`) / rick-use-allcaps(reordered inner-share) とは別文面なので独立に確認する。

## 設計（prob010/012 rev と同一構造・gate だけ差し替え）

- 単一 kernel・GPT のみ・`N_CANDIDATES=20`・`TAIL_REPEATS=5`・rev=**LONG-on-ALLOW**。
- 各候補 = message[0]=gate（exp021 `_message_gpt(i)`＝`_GPT_DEMO_END_Z`＋`_GPT_TASK`＋recipient・宛先 a..（"ht"除外）先頭20）＋ message[1..5]=tail。
- gate は `_GPT_DEMO_END_Z`／`_GPT_TASK` を exp021 とバイト等価に移植（`e mail.se nd` は実スペース分断・zero-width なし）。
- 手元 eval は public/private とも clean args 走査で常に ALLOW → 本物 private の block 可否は **LB timing 専用**。

校正（prob007 正式 run・同 GPT・同 email.send gate）: `B≈129`, `C≈111`, `B+C≈240`, `B+2C≈352`。既知 ALLOW 参照＝prob010_rev 310 / prob012_rev 325。
- ALLOW（block しない）→ `B+2C`（重い ~352 / 既知 310-325）→ **ALLOW示唆**
- BLOCK（DENY/CONFIRM）→ `B+C`（軽い ~240）→ **BLOCK示唆**

## 提出結果（2026-09-01 CPU 版で Kaggle Version 1 commit・COMPLETE）

| kernel | commit | 状態 | run duration | public LB | メモ |
|---|---|---|---|---|---|
| `prob014_rev` | 2026-09-01 | COMPLETE（CPU push） | （LB 提出後に記入） | （LB 提出後） | CPU 設定（`enable_gpu=false`・GPU machine 指定なし）。sanity: roundtrip/ serve/ compile/ ruff PASS。LB 未提出。 |

## 判定

- **LB 未提出**（本ラウンドは CPU commit まで）。timing 計測には GPU での競技 rerun が必要。
- 提出時の読み方: `T≈B+2C(≈310-352)`→ALLOW示唆 / `T≈B+C(≈240)`→BLOCK示唆。既知 ALLOW（prob010/012_rev）との比較で判定。
- 単一アーム rev のみ（companion fwd なし＝ユーザ指示）。
