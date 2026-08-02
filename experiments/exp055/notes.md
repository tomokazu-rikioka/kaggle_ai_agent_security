# exp055 — 近 champion draw B（PROBE_REPS=2 + cap 0.997）

Round 9（public 最大化・best-of バッテリ）の1本。土台は exp028/exp039 champion の proven 3-arm エンジン。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- best-of の近 champion 枠のうち **cap をもう一段攻めた reach draw**。exp054（0.996）より `REPLAY_SAFE_FRAC` を
  0.997 まで押し、返却集合の replay 予算を最大化して N_eff を上端まで詰める。

## 変更点（vs exp054）
- **proven 3-arm エンジンは1バイトも不変**。`PROBE_REPS`=2 は据置、`REPLAY_SAFE_FRAC` 0.996→**0.997**。
- 安全性根拠: exp034（probe=2+0.997）が **非VOID（LB 89.730）** を実証。単独 cap 押上げの exp043（probe=4+0.996）は
  VOID だったが、差は probe 回収で買い戻す cold 余裕。本 exp は probe=2 なので cold-safe。
- fail-closed（崩れれば verbose 床へ縮退）＝下限は champion 分散帯。上振れは cap 上端 × GPU 分散の当たり。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。ノブ効果（N_eff 増）は gemma では見えない。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。所見: （提出後に追記）
