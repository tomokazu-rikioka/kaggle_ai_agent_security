# exp067 — frontier adaptive_margin エンジン移植・安全既定（アンカー）

Round 12（public 100+ 奪回）の**アンカー**。dimong4/jed-v25/yusuke（JED系）の fill エンジンを移植。

## 位置づけ
frontier 主流は **我々の exp028 と同一テンプレ（verbose/forge）＋優れた fill 会計（MARGIN_S / adaptive_margin）**。
本 exp はその会計を安全既定（MARGIN_S=47・FBF=0.95・単発）で移植＝frontier 公開既定相当（~88-90 で完走）。
exp068（margin 詰め）/ exp069（forge-multipost）/ exp070（統合）の**帰属基準・完走保証の床**。

## 狙い（仮説）
- 我々の exp028（0.995 の薄い 45s クッション）は高 N で VOID（Round10 全滅・cold リプレイ過小評価）。
- adaptive_margin は `budget×FBF - margin` で wall-clock を止める。FBF=0.95 の ~450s クッションが cold ドリフト
  （~5%）を吸収して**完走する**。速いモデル（gemma）は margin を削って fill 容量を回収、遅い gpt_oss は満額保護。
- split_by_latency で per-model routing（遅い→forge / 速い→verbose）。

## 変更点（vs exp028）
- 会計を replay-safe fill（0.995 フラクション）→ **adaptive_margin（MARGIN_S=47・FBF=0.95）**に差替。
- テンプレ選択を effective_cost race → **latency-split 分類**に差替（機能は同じ per-model routing）。

## 評価/判定
- `make eval EXP=exp067`（gemma N=300）で健全性: fire率・無クラッシュ・private=0。local は N_eff を予測しない。
- **判定は live LB**。まず本アンカーが完走することを確認（VOID しなければ会計移植が成功）。exp028=90.99 と比較。
- 所見: （eval・live 後に追記）
