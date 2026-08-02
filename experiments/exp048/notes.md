# exp048 — forge-continuation stacking（Round8・最も大胆な swing）

Round8（public best・探索 swing 全振り）の非線形上振れ枠。土台 exp028（LB 90.99）。

## 狙い（T-MAN の continuation economy を白黒付ける）
- 研究（2026-07-29）: T-MAN/Xander（disc 727895）が「cross-turn stacking は strictly loses」を**撤回**し、
  「gpt_oss continuation は fresh candidate に経済的に勝てる／解析オーバーヘッド無しで即ツール実行を強制
  する最適化 continuation ＋圧縮 URL」と主張。exp029（continuation を plain で試し LB54.7 で棄却）を
  **per-turn forge ＋圧縮 url ＋実測採否**で再挑戦する。

## 機構（採点 replay の continuation 挙動）
- 採点 replay は候補を `env.reset()` 1回＋各メッセージを順に interact（同一 env・KV 継続）で流す（`ops.py:530-534`）。
- K メッセージ continuation = **1トレースに K post 蓄積**（raw=16K+2・cell は1個）。fresh 単発 K 個=raw18K（cell +2K）。
- continuation は cell −2(K−1) を失うが system/tools prompt の prefill を K→1 に償却。gpt_oss は forge で gen が
  小さい分 prefill 比が大きく、continuation の raw/秒 が単発を上回りうる。break-even は continuation post が
  単発比 ≥11% 安いこと（16/18）。

## 実測採否（fail-closed・exp029/密度退行の回避）
- fill 中に単発 raw/秒 と K∈{4,8} の continuation raw/秒 を実測。continuation が単発を `CONT_MARGIN`=1.05 倍
  超えた時だけ K 連鎖で fill、さもなくば単発 fill（exp028 相当）。
- **部分 compliance（K 未満の発火）は raw/秒 が自動的に下がり単発に負ける**ので、密度が黒字化しない場合は
  自動で単発へ縮退する。continuation ターンは forge 崩壊＋圧縮 url（`aa.co`）でトークン最小化。

## live 安全性
- replay-safe sizing（keep 集合の実測コスト積算・`0.995×9000` 手前停止）。continuation 候補の実測 elapsed=
  採点 replay コスト（同一手順）。K≤8（`MAX_REPLAY_MESSAGES_PER_FINDING=32` 内）。単発 slowest を chain で
  膨らませない（単発 fill の stop 推定を汚さない）。

## 検証（eval 最小化・LB 直行）
- `make eval EXP=exp048`（gemma N=300）: 健全性のみ。**stderr の `unit=` と `cont_rps/single_rps` が
  一次信号**（continuation が chain して黒字化するか）。gemma で forge は format error で壊れるので、gemma では
  continuation ターンが発火しない可能性大→単発へ縮退（想定挙動）。真価は gpt_oss/live。
- 提出前に health check 厳格化（無クラッシュ・per-turn 発火・単発縮退の確認）。
- 所見/LB: （提出後に追記）
