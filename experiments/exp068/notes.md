# exp068 — adaptive_margin ＋ margin 詰め（yusuke 主ノブ・単一レバー A/B）

Round 12（public 100+ 奪回）。exp067 アンカーからの**単一レバー**。

## 狙い（仮説）
dimong4 明言＝「LB の差は FILL 戦略。`MARGIN_S` が主ノブ。yusuke が 50→45→44→42→37 と刻むたびに加点」。
exp067 のエンジンを1バイトも変えず、会計クッションだけ詰める:
- `MARGIN_S` 47→**37**（yusuke ラダー末端）・`FILL_BUDGET_FRAC` 0.95→**0.97**。
- クッション ~450s→~270s に縮み N_eff 純増（→ score↑）。

## 変更点（vs exp067）
- `MARGIN_S` と `FILL_BUDGET_FRAC` の2定数のみ。テンプレ・split・その他は完全同一 → 差分は「margin 詰めの効き」に帰属。

## 評価/判定
- `make eval EXP=exp068`（gemma N=300）で健全性のみ。**判定は live LB**（vs exp067 アンカー）。
- VOID risk: cold ドリフト >3% なら時間切れ。もし exp068 が VOID し exp067 が完走したら「cold ドリフトが 3–5% 帯」の実測。
- 所見: （eval・live 後に追記）
