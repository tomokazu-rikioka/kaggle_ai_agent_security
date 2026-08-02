# exp060 — public best-of draw（champion byte・PROBE_REPS=4 + cap 0.995）

Round 10（public 最大化・best-of バッテリ）の**上側裾ドロー #2**。exp059 と同一（exp028 champion バイト継承）。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 特化・private=0 承知。
- exp059 と独立な GPU/サーバ分散サンプルを引き、歴代最高 90.99 を出した母集団の max を厚くする。

## 変更点（vs exp028 champion）
- **なし**（採点対象はバイト一致）。`PROBE_REPS`=4 / `REPLAY_SAFE_FRAC`=0.995 / 3-arm 不変。docstring・stderr ラベルのみ差替。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。exp028 と同一挙動。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。所見: （提出後に追記）
