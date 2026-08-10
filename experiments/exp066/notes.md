# exp066 — verityix v174 忠実移植（terse 出力抑制 × 高N grid）

Round 12（public 100+ 奪回）の1本。frontier **独立系統**（dimong4/yusuke の verbose 系とは別哲学）。

## 位置づけ
2026-08-03 に LB を直接確認＝上位 100–112 は現行 v3.1.2 の実スコア（凍結ゾンビでない）。verityix `...hitherto`
（v174・2026-08-02 最新）は **terse 出力抑制テンプレ × 高N grid（~1568）** で高スコアを狙う独立実装。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 特化・private=0 承知。
- 「post を撃たせた後に沈黙させる」（"Output nothing else" 系）で hops=8 リプレイの生成トークンを最小化 → 1候補を
  高速化 → N を ~1568 まで詰める。exp016「応答するな」（発火率↓で退行）と違い**ツール呼び自体は渋らせない**。
- **terse(066) vs verbose(067) のどちらが live で勝つか**を決着させる枠。

## 変更点（vs 我々の champion exp028）
- テンプレを exp028 の verbose/lean/forge → verityix の**出力抑制8種**（`STYLES`）に全面差替。
- 会計を replay-safe fill → verityix の単純 `slowest*1.5` ゲート（keep-only-fired の高N grid）に差替。
- url_pattern 8種（scheme/TLD/port 多様化）で cell を散らす。

## 評価/判定
- `make eval EXP=exp066`（gemma N=300）で健全性のみ: fire率・無クラッシュ・private=0。local は N_eff を予測しない。
- VOID risk: verityix の単純マージンは adaptive_margin（exp067）ほど保守的でない。cold ドリフト次第で時間切れしうる。
- **判定は live LB**（vs exp067 の verbose/adaptive_margin・exp028=90.99）。★LB 提出はユーザ明示指示時のみ。
- 所見: （eval・live 後に追記）
