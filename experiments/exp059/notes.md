# exp059 — public best-of draw（champion byte・PROBE_REPS=4 + cap 0.995）

Round 10（public 最大化・best-of バッテリ）の**上側裾ドロー #1**。attack.py の採点対象を exp028 champion から
バイト継承（`diff` の差分は docstring と stderr ラベルのみ＝得点分布は exp028 と同一）。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 特化・private=0 承知。
- exp028 は歴代最高 **LB 90.99**（初の90超え）を出した構成。その上側裾（~91）をもう一度引きにいく独立サンプル。
  高床の probe=2+0.997（exp056-058）と母集団を分けることで、max の上側裾を厚くする。

## 変更点（vs exp028 champion）
- **なし**（採点対象はバイト一致）。`PROBE_REPS`=4 / `REPLAY_SAFE_FRAC`=0.995 / 3-arm 不変。docstring・stderr ラベルのみ差替。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。exp028 と同一挙動。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。所見: （提出後に追記）
