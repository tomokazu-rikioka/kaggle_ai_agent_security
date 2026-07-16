# 実験スコア一覧

> 用語は [用語集](../用語集.md) を参照。

> このファイルは直接編集して運用する（スコアの単一ソース）。
> - `local_*` 列: `/update-score <exp>` スキルが `make eval` で取得（回収）した `experiments/<exp>/scores.json` から記入する（`gpt_oss > gemma_4` 優先）。`local_agent` は採用したモデル名。
> - `lb_public` 列・`changes` 列: 直接記入する（または Claude に依頼）。
> - `local_public` が公開 LB と相関し、`local_private` は非公開への汎化の代理。
> - local 列は 2026-07-16 の gemma_4・N=300 eval（public/private）で記入した。`lb_public` は再提出済み（rerun 採点待ち）。

## 実験一覧

| exp | local_agent | local_public | local_private | lb_public | changes |
|-----|------------|------|------|------|---------|
| exp001 | gemma_4 | 17.820 | 4.320 | - | EXFIL(marker)+DEPUTY 混合（命令形）・`EXFIL_FRACTION=0.5`・N=300/K=1/M=1。EXFIL=public の主柱＋DEPUTY=public/private の保険という中立な組み合わせ。public=EXFIL150+DEPUTY144 / private=DEPUTY144 |
| exp002 | gemma_4 | 8.730 | 8.730 | - | 純DEPUTY（疑問形）・`EXFIL_FRACTION=0.0`・N=300/K=1/M=1。"Could you notify…?"。public/private の両ガードレールで残る CONFUSED_DEPUTY に全振り。発火率97.0%（291/300）で public=private=8.73 |
| exp003 | gemma_4 | 27.000 | 0.000 | - | 純EXFIL(marker)・`EXFIL_FRACTION=1.0`・N=300/K=1/M=1。http.post の public の穴に全振りする public 特化の保険（private は block≡fire〔遮断条件と発火条件が同一〕で寄与なし）。300/300発火で public=27.0・private=0 |
| exp004 | gemma_4 | 27.000 | 0.000 | - | **fire-validated fill**（＝発火検証してから予算まで詰める。上位カーネル pengwang91 v26 を移植）。reasoning-collapse（＝推論の途中打ち切りで高速化。harmony注入でgpt_ossのCoTを打ち切り→~2倍速）＋per-model fire-rate selector（＝モデル別にテンプレを選ぶ）＋replay-safe sizing（＝リプレイの合計時間が予算を超えないよう候補数を決める。`REPLAY_SAFE=0.90`）。EXFIL一本足・K=1・N=自己較正の詰め込み（fill）。public特化（private=0）。exp001-003の静的N=300から探索型へ転換。smoke（簡易確認）=`CANDIDATES=300`、提出=`CANDIDATE_CAP=None`のfull fill。**local はN=300上限のsmoke（CANDIDATE_CAP=300）で 27.0（EXFIL300全発火）＝exp003と同値。gemmaではcollapseの効果が出ず、真価はfull-fillのgpt_ossで候補数を伸ばす点。提出はfull-fill** |
| exp005 | gemma_4 | 26.000 | 0.000 | - | **fire-validated fill**（上位カーネル pilkwang を移植）。multi-message amortization（＝固定費の分割償却。1候補=M(8→16)メッセージ連鎖で固定費Fを分割、候補あたりraw=16f+2）＋per-message collapse＋per-model routing（＝モデル別に振り分け）＋self-heal（＝失敗時に安全な既定へ戻す）＋measured-cost cap（＝測定した費用で上限管理。`REPLAY_SAFE=0.80`・固定N不使用）。EXFIL一本足・上限（ceiling）が高い。まずM=8のsmokeで compliance（＝モデルが従う率）の減衰とリプレイ費用を実測してからMを引き上げる。**local はM=8・N=40候補のsmoke（CANDIDATE_CAP=40、8×40=320メッセージ）で public=26.0：EXFIL320全発火・raw/候補=130（単発exp003の18の7.2倍）でmulti-message amortizationを実証。提出はfull-fill（live INVALIDのリスクを承知の上で submit）** |
