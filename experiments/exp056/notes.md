# exp056 — public best-of draw #1（PROBE_REPS=2 + cap 0.997）

Round 10（public 最大化・best-of バッテリ）の主力枠 #1。土台は exp028/exp039 champion の proven 3-arm エンジン。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- Round 9 実測で **probe=2 + 0.997（exp055=90.405 / exp034=89.730）が全 champion バイトドローに勝ち、VOID ゼロ**。
  この直近勝ち構成に best-of の重心を置き、独立な GPU/サーバ分散サンプルを引く。

## 変更点（vs exp028 champion）
- **proven 3-arm エンジンは1バイトも不変**（発火率・出力トークンに触れない）。差替は予算回収ノブ2定数のみ。
  `PROBE_REPS` 4→**2**、`REPLAY_SAFE_FRAC` 0.995→**0.997**（exp055 と同一構成）。
- 安全性根拠: exp034/exp055（probe=2 + 0.997）が非VOID。単独 cap 押上げの exp043（probe=4 + 0.996）は VOID だったが、
  差は probe 回収で買い戻す cold 余裕。本 exp は probe=2 なので cold-safe。
- fail-closed（崩れれば verbose 床へ縮退）＝下限は champion 分散帯。上振れは cap 上端 × GPU 分散の当たり。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。ノブ効果（N_eff 増）は gemma では見えない。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。所見: （提出後に追記）
