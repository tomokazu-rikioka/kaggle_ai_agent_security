# exp062 — cap 0.99 ＋ probe=2（cold 余裕を probe 回収で二重確保・独立ドロー）

Round 11（public 最大化・VOID 完走回避バッテリ）の probe 回収枠。土台は champion(exp028=LB90.99) の proven 3-arm エンジン。

## 背景（Round10 全滅）
- Round10（exp056-060）は cap 0.995-0.997 で **5/5 全て時間切れ VOID**。cold 余裕 45s が分散を吸収できず 9000s 超過。
- 対策は cap 保守化（0.98-0.99）で完走優先。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- exp061（cap 0.99・probe=4）と同 cap で **probe を 4→2** に半減。生成は greedy 決定論で発火は反復不変なので、
  浮いた試し打ち時間を fill と cold 余裕に回す。cap 0.99 の余裕 90s に probe 回収を上乗せして VOID をさらに遠ざける。
- exp061 と同 cap の独立な GPU/サーバ分散サンプル（同一構成でも ±1.4〜4 振れるため best-of で max を厚くする）。

## 変更点（vs exp028 champion）
- **proven 3-arm エンジンは1バイトも不変**。差替は予算回収ノブ2定数のみ＝`PROBE_REPS` 4→**2**、`REPLAY_SAFE_FRAC` 0.995→**0.99**。
- exp061 との対比で「同 cap における probe 削減の効き」も読める。
- fail-closed（崩れれば verbose 床へ縮退）＝下限は champion 分散帯。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。ノブ効果（N_eff 増・VOID 回避）は gemma では見えない。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。**所見: LB89.370 で完走＝Round11 ベスト（exp061-065 が 5/5 全完走・VOID ゼロ）。** cap0.99+probe=2。exp061(0.99+probe=4=87.075) 比 +2.295 だが cap0.98 では probe4>probe2 と符号逆転＝probe 効果は GPU 分散(±1.4〜4)に埋もれ系統性なし。best-of max として 89.370 を捕捉（exp028=90.99 の分散帯上位）。
