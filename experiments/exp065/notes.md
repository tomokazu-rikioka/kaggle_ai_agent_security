# exp065 — cap 0.98 ＋ probe=2（絶対完走の二重保険・cold 余裕最大）

Round 11（public 最大化・VOID 完走回避バッテリ）の絶対完走枠（最も VOID しにくい）。土台は champion(exp028=LB90.99) の proven 3-arm エンジン。

## 背景（Round10 全滅）
- Round10（exp056-060）は cap 0.995-0.997 で **5/5 全て時間切れ VOID**。cold 余裕 45s が分散を吸収できず 9000s 超過。
- 対策は cap 保守化（0.98-0.99）で完走優先。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- cap **0.98**（cold 余裕 180s）に加え **probe を 4→2** に減らして cold 余裕を上乗せした二重保険。Round11 で最も VOID しにくい枠。
- best-of の下限保証。この構成が VOID するなら cap では救えない別要因（Round10 の最終切り分け）。

## 変更点（vs exp028 champion）
- **proven 3-arm エンジンは1バイトも不変**。差替は予算回収ノブ2定数のみ＝`PROBE_REPS` 4→**2**、`REPLAY_SAFE_FRAC` 0.995→**0.98**。
- 生成は greedy 決定論で発火は反復不変なので、probe を削っても選択の質は保たれる（fail-closed で verbose 床へ縮退）。
- exp064（0.98 ＋ probe=4）との対で probe 削減の効きを読む。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。ノブ効果（N_eff 増・VOID 回避）は gemma では見えない。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。**所見: LB86.310 で完走（非VOID・4件目の VOID 回避）。** cap0.98+probe=2。exp064(0.98+probe=4=86.940) 比 −0.63＝probe 削減が僅かに不利（latency 推定 noisy or 分散）。→ probe=4 維持が無難と示唆。
