# exp063 — cap 0.985（中間保守・cold 余裕 135s）

Round 11（public 最大化・VOID 完走回避バッテリ）の中間保守枠。土台は champion(exp028=LB90.99) の proven 3-arm エンジン。

## 背景（Round10 全滅）
- Round10（exp056-060）は cap 0.995-0.997 で **5/5 全て時間切れ VOID**。cold 余裕 45s が分散を吸収できず 9000s 超過。
- 対策は cap 保守化（0.98-0.99）で完走優先。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- cap を **0.985**（cold 余裕 135s＝0.995 の 3 倍）に置く cap 階段の中段。exp061(0.99) が VOID した場合に得点を拾う保険。
- N_eff は 0.995 比 −1.0%（理論 ~90.1）。

## 変更点（vs exp028 champion）
- **proven 3-arm エンジンは1バイトも不変**。差替は cap 定数のみ＝`REPLAY_SAFE_FRAC` 0.995→**0.985**、`PROBE_REPS`=4 据置。
- exp061(0.99)/exp064(0.98) と合わせ、cap 階段で「完走する上限 cap」を LB で特定する中段サンプル。
- fail-closed（崩れれば verbose 床へ縮退）＝下限は champion 分散帯。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。cap 効果（VOID 回避）は gemma では見えない。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。**所見: LB86.940 で完走（非VOID）。** cap0.985 も VOID せず得点。exp064(0.98) と同値・exp061(0.99=87.075) 比 −0.135。cap 0.98-0.99 は全て完走圏で cap 差は分散に埋もれる。
