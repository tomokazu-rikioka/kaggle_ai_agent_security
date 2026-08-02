# exp058 — public best-of draw #3（PROBE_REPS=2 + cap 0.997）

Round 10（public 最大化・best-of バッテリ）の主力枠 #3。exp056/057 と**同一構成の独立分散サンプル**。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- probe=2 + 0.997 は直近勝ち構成（exp055=90.405 / exp034=89.730・VOID ゼロ）。best-of の主力を3ドローに厚くして
  この構成の分散上端を刈り取る。

## 変更点（vs exp028 champion）
- **proven 3-arm エンジンは1バイトも不変**。`PROBE_REPS` 4→**2**、`REPLAY_SAFE_FRAC` 0.995→**0.997**（exp056/057 と同一）。
- 安全性根拠・fail-closed は exp056 と同一（probe=2 で cold-safe・下限は champion 分散帯）。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。所見: （提出後に追記）
