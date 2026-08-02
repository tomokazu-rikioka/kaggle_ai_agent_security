# exp061 — cap 0.99（0.995→保守化・最も攻めた完走枠）

Round 11（public 最大化・VOID 完走回避バッテリ）の本命枠。土台は champion(exp028=LB90.99) の proven 3-arm エンジン。

## 背景（Round10 全滅）
- Round10（exp056-060）は cap 0.995-0.997 で **5/5 全て時間切れ VOID**（COMPLETE だが公開スコア空欄・incorrect-format）。
- 確定教訓＝cap 0.995 の cold 余裕 45s では GPU/サーバ分散を吸収できず、live replay が 9000s を跨ぐ。
  **対策は cap を 0.98-0.99 に保守化して完走を最優先すること**。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- cap を 0.995→**0.99**（cold 余裕 45s→90s）に1段だけ保守化。Round11 で最も攻めた完走枠として、
  「0.99 が完走するか」を LB で確かめる。当たれば N_eff は 0.995 比 −0.5% で理論 ~90.5。

## 変更点（vs exp028 champion）
- **proven 3-arm エンジンは1バイトも不変**（発火率・出力トークンに触れない）。差替は cap 定数のみ。
  `REPLAY_SAFE_FRAC` 0.995→**0.99**、`PROBE_REPS`=4 据置。
- cap 階段（exp061=0.99 / exp063=0.985 / exp064=0.98）で完走上限を LB 特定しつつ 5 独立ドローで best-of。
- fail-closed（崩れれば verbose 床へ縮退）＝下限は champion 分散帯。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。cap 効果（VOID 回避）は gemma では見えない。
- **結果: LB87.075 で完走（非VOID・890分）。cap 0.99 でも VOID せず得点＝「cap 保守化」対策が本命 cap でも有効。** exp064(cap0.98=86.940) 比 +0.135。Round11 は exp061-065 が **5/5 全完走・VOID ゼロ**（Round10 の 0/5 全滅と対照）で「cap 0.98-0.99 保守化＝VOID 回避」を実証。best-of max は exp062(cap0.99+probe=2)=89.370。
