# exp075 — cap 0.985 ＋ probe=2（完走床・全滅回避の保険）

Round13（public best-of バッテリ／cap リスク曲線に散らす5枚）。土台は champion(exp028=LB90.99) の proven 3-arm エンジンを exp062 からバイト継承。

## この枠の設計
cap 0.985（exp063=86.940 で完走実証）。速い round で他が刈り取り、遅い round でも確実に得点を残す下限保証。

## バッテリ全体（exp071-075）
| exp | cap | probe | 役割 |
|---|---|---|---|
| exp071 | 0.995 | 4 | exp028 champion-byte（90.99 実績）— 上端ギャンブル |
| exp072 | 0.995 | 2 | exp055 系（90.405 実績）+probe2 で N 上乗せ |
| exp073 | 0.993 | 2 | 0.99 と VOID 境界の中間 — ~90 狙い |
| exp074 | 0.99 | 2 | exp062 系（Round11 best 89.37）— 完走コア |
| exp075 | 0.985 | 2 | 完走床（~87）— 全滅回避の保険 |

## 変更点（vs exp062）
- `REPLAY_SAFE_FRAC` = 0.985・`PROBE_REPS` = 2 の2定数のみ（エンジンは1バイトも触らない）。差分は「cap/probe の best-of ドロー」に帰属。

## 評価/判定
- 判定は live LB（best-of の上端を拾えたか）。local gemma smoke は 27 天井で cap 効果を出せないので健全性のみ。
- VOID risk: cap 0.995 の 071/072 は VOID 境界（Round10 全滅の帯）。074/075 が完走を確保する設計。
- 所見: （LB 回収後に追記）
