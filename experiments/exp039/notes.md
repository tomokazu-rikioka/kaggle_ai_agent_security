# exp039 — champion 床（best-of の確実な下限＆分散回収）

Round 6 の 1 本。**exp028（proven 90.99）のエンジンを忠実に保った控え**。

## 狙い
- 狙う述語: **EXFILTRATION**。verbose/lean/forge の3テンプレ・`PROBE_REPS=4`・`REPLAY_SAFE_FRAC=0.995` を
  1 バイトも変えない。deep-forge(exp036/037)・最短化(exp038) が live で外れた（INVALID/VOID）ときの
  **退行しない下限**であり、同時に **best-of の中核**＝同一/近縁を複数回 live 提出して GPU 分散上振れ
  （chenahong 104位: 同一スクリプトで±10点）を拾う。

## なぜ 0.996 以上へ攻めないか
- 「identical-candidate KV-cache warm spam は VOID」＝run() 内の温かい cache 速度は cold replay に転移しない。
  warm 実測 latency で積む会計は過小評価で、cap を攻めると cold replay で 9000s 超過→VOID（exp024/025 の正体）。
  床の役割上 **cold 余裕を最優先し 0.995 を維持**する。

## 運用（best-of）
- 探索でなく **確実な 90 台を複数回引く**枠。deep-forge 系が当たれば champion を差し替え、外れても本 exp が下限を保証。

## local の読み方（gemma・N=300）
- 健全性のみ（fire率 verbose 基準・非クラッシュ・private=0）。fill 系は手元 27 天井。LB は live のみ確定。

## 評価結果（make eval）
- `make eval EXP=exp039 CANDIDATES=300`（gemma・N=300・2並列枠厳守）。
- 所見: （eval 後に追記）
- LB: （live 提出はユーザー明示指示時のみ。best-of。ここに記入）
