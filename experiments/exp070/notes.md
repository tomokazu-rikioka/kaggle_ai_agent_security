# exp070 — 統合 reach（margin 詰め × forge-multipost・最大出力の一撃）

Round 12（public 100+ 奪回）の**統合 reach**。exp068 × exp069 の両取り。

## 狙い（仮説）
frontier の勝ちレバーを全部載せた最大出力構成（dimong4 の aggressive submission_variant 相当）:
- `MARGIN_S` 47→**37**・`FILL_BUDGET_FRAC` 0.95→**0.97**（exp068 の margin 詰め）。
- `SLOW_MULTIPOST_N` 1→**4**（exp069 の forge-multipost）。

過去の統合退行（exp013/030）は「未検証レバーの盲目重畳」だったが、本 exp は exp068/069 で**個別検証する2レバー**の
重畳＝frontier が実際に併用している構成なので筋が違う。best-of の上端狙い。

## 変更点（vs exp067）
- `MARGIN_S`・`FILL_BUDGET_FRAC`・`SLOW_MULTIPOST_N` の3定数（exp068＋exp069 のレバー合成）。

## 評価/判定
- `make eval EXP=exp070`（gemma N=300）は健全性のみ。**判定は live LB**（exp068/069 と合わせて帰属）。
- VOID risk が最大（FBF=0.97・MARGIN=37・multipost=4）。fail-closed（forge 崩れれば verbose 床）＋FBF クッションで下限は守る。
  exp068 が VOID するなら本 exp も VOID しうる。
- 所見: （eval・live 後に追記）
