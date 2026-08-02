# exp064 — cap 0.98（完走床・最保守・cold 余裕 180s）

Round 11（public 最大化・VOID 完走回避バッテリ）の完走床（下限保証）。土台は champion(exp028=LB90.99) の proven 3-arm エンジン。

## 背景（Round10 全滅）
- Round10（exp056-060）は cap 0.995-0.997 で **5/5 全て時間切れ VOID**。cold 余裕 45s が分散を吸収できず 9000s 超過。
- 対策は cap 保守化（0.98-0.99）で完走優先。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- cap を **0.98**（cold 余裕 180s＝0.995 の 4 倍）に置いた最保守の**完走床**。replay 目標 8820s、GPU 分散 +2% でも
  8820×1.02=8996<9000 でぎりぎり完走。**この床が VOID するなら cap 以外の別要因**（Round10 の切り分け基準）。
- N_eff は 0.995 比 −1.5%（理論 ~89.6）。best-of の下限保証。

## 変更点（vs exp028 champion）
- **proven 3-arm エンジンは1バイトも不変**。差替は cap 定数のみ＝`REPLAY_SAFE_FRAC` 0.995→**0.98**、`PROBE_REPS`=4 据置。
- exp065（0.98 ＋ probe=2）との対で「同 cap における probe 削減の効き」も読める。
- fail-closed（崩れれば verbose 床へ縮退）＝下限は champion 分散帯。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。cap 効果（VOID 回避）は gemma では見えない。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。**所見: LB86.940 で完走（非VOID）＝最保守 cap 0.98 の床が確実に得点。** Round10 全滅（cap0.995-0.997 で 5/5 VOID）への「cap 保守化」対策が奏功。exp028(90.99) 比 −4.05 は N_eff 減＋分散。exp065(0.98+probe=2=86.310) 比 +0.63＝probe=4 が僅かに有利。
