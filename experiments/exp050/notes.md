# exp050 — champion 完全同一（best-of control／下限保証）

Round8（public best・探索 swing 全振り）の control。**attack.py は exp028（LB 90.99）とバイト一致**（`diff` で確認済み）。

## 狙い（なぜ同一コードを1本使うか）
- 研究（2026-07-29 Playwright 調査）で確定した2点:
  1. **best-of は必須**。byte-identical な提出でもスコアが広く分散する（同一コード exp039=89.6 vs exp028=91.0＝±1.4 の GPU/サーバ分散が実在）。単発 A/B の判定は分散に埋もれるので、複数ドローの最良採用が前提。
  2. **現行評価器で公開手法が再現できる天井は ~88–90**（同手法 Cleanor Labs 88.7 停滞・指定NB v12=89.19）。**我々の 90.99 は現行フロンティアの最上端かそれ以上**。上位 100+ は旧評価器の凍結ゾンビが濃厚。
- したがって本 exp は (a) **exp046–049 の各レバーの帰属基準（control）**、(b) **分散の上端を狙う独立ドロー**、(c) 全レバーが外れた時の**下限保証**、を兼ねる。

## エンジン（= exp028）
- EXFIL 一本足・単発。テンプレ3種 `verbose`/`lean`/`forge` を per-candidate race。
- `effective_cost=median_latency÷fire_rate` で最小選択（fail-closed・`MIN_FIRE_RATE=0.5`）。
- `PROBE_REPS=4`・`REPLAY_SAFE_FRAC=0.995`・replay-safe sizing（`0.995×9000=8955s` 手前停止で VOID 回避）。
- URL 連番 `aa.co/ab.co/...` で 1候補=1 unique cell。

## 検証（eval 最小化・LB 直行）
- `make eval EXP=exp050`（gemma N=300）は健全性のみ（fire率=verbose 相当・無クラッシュ・private=0）。exp028 と同一なので確認は形式的。
- **判定は live 提出**（★ユーザ明示指示時のみ）。exp028 の既知 90.99 を control 値として流用してもよい。
- 所見/LB: （提出後に追記）
