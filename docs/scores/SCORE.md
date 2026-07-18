# 実験スコア一覧

> 用語は [用語集](../用語集.md) を参照。

> このファイルは直接編集して運用する（スコアの単一ソース）。
> - `local_*` 列: `/update-score <exp>` スキルが `make eval` で取得（回収）した `experiments/<exp>/scores.json` から記入する（`gpt_oss > gemma_4` 優先）。`local_agent` は採用したモデル名。
> - `lb_public` 列・`changes` 列: 直接記入する（または Claude に依頼）。
> - `lb_time` 列: 提出（submit）から採点 COMPLETE 検知までの経過時間（分）。キュー待ちを含むので実採点時間の上限目安。`scripts/ops/time_manager.py` で計測する。
> - `local_public` が公開 LB と相関し、`local_private` は非公開への汎化の代理。
> - local 列は 2026-07-16 の gemma_4・N=300 eval（public/private）で記入した。`lb_public` は再提出済み（rerun 採点待ち）。

## 実験一覧

| exp | local_agent | local_public | local_private | lb_public | lb_time | changes |
|-----|------------|------|------|------|------|---------|
| exp001 | gemma_4 | 17.820 | 4.320 | 17.865 | 405分 | EXFIL(marker)+DEPUTY 混合（命令形）・`EXFIL_FRACTION=0.5`・N=300/K=1/M=1。EXFIL=public の主柱＋DEPUTY=public/private の保険という中立な組み合わせ。public=EXFIL150+DEPUTY144 / private=DEPUTY144 |
| exp002 | gemma_4 | 8.730 | 8.730 | 8.565 | 461分 | 純DEPUTY（疑問形）・`EXFIL_FRACTION=0.0`・N=300/K=1/M=1。"Could you notify…?"。public/private の両ガードレールで残る CONFUSED_DEPUTY に全振り。発火率97.0%（291/300）で public=private=8.73 |
| exp003 | gemma_4 | 27.000 | 0.000 | 27.000 | 311分 | 純EXFIL(marker)・`EXFIL_FRACTION=1.0`・N=300/K=1/M=1。http.post の public の穴に全振りする public 特化の保険（private は block≡fire〔遮断条件と発火条件が同一〕で寄与なし）。300/300発火で public=27.0・private=0 |
| exp004 | gemma_4 | 27.000 | 0.000 | 66.960 | 725分 | **fire-validated fill**（＝発火検証してから予算まで詰める。上位カーネル pengwang91 v26 を移植）。reasoning-collapse（＝推論の途中打ち切りで高速化。harmony注入でgpt_ossのCoTを打ち切り→~2倍速）＋per-model fire-rate selector（＝モデル別にテンプレを選ぶ）＋replay-safe sizing（＝リプレイの合計時間が予算を超えないよう候補数を決める。`REPLAY_SAFE=0.90`）。EXFIL一本足・K=1・N=自己較正の詰め込み（fill）。public特化（private=0）。exp001-003の静的N=300から探索型へ転換。smoke（簡易確認）=`CANDIDATES=300`、提出=`CANDIDATE_CAP=None`のfull fill。**local はN=300上限のsmoke（CANDIDATE_CAP=300）で 27.0（EXFIL300全発火）＝exp003と同値。gemmaではcollapseの効果が出ず、真価はfull-fillのgpt_ossで候補数を伸ばす点。提出はfull-fill** |
| exp005 | gemma_4 | 26.000 | 0.000 | 45.090 | 710分 | **fire-validated fill**（上位カーネル pilkwang を移植）。multi-message amortization（＝固定費の分割償却。1候補=M(8→16)メッセージ連鎖で固定費Fを分割、候補あたりraw=16f+2）＋per-message collapse＋per-model routing（＝モデル別に振り分け）＋self-heal（＝失敗時に安全な既定へ戻す）＋measured-cost cap（＝測定した費用で上限管理。`REPLAY_SAFE=0.80`・固定N不使用）。EXFIL一本足・上限（ceiling）が高い。まずM=8のsmokeで compliance（＝モデルが従う率）の減衰とリプレイ費用を実測してからMを引き上げる。**local はM=8・N=40候補のsmoke（CANDIDATE_CAP=40、8×40=320メッセージ）で public=26.0：EXFIL320全発火・raw/候補=130（単発exp003の18の7.2倍）でmulti-message amortizationを実証。提出はfull-fill（live INVALIDのリスクを承知の上で submit）** |
| exp006 | gemma_4 | 27.000 | 0.000 | 84.780 | 838分 | 公開 LB83 カーネル（lopure=dhanvin）の忠実移植。v26 replaysafe 系。5テンプレ（`plain`/`bare`/`bare_ok`/`inj_close`/`inj_commentary`）・binary cost 選択（median lat÷発火率）・`REPLAY_SAFE=0.99`・EXFIL 単発。exp004(LB66.96)→83 の差分（テンプレ3→5・`PROBE_REPS`2→5・`MIN_FIRE_RATE`1.0→0.2・`REPLAY_SAFE`0.90→0.99）を全取込。**local(N=300 gemma): public=27.0（EXFIL 300全発火）/private=0（block≡fire・想定通り）。exp003/004と同値。** |
| exp007 | gemma_4 | 27.000 | 0.000 | 70.785 | 806分 | **公開 EXFIL frontier（pilk `ai-agent-v3-1-2-single-post` 忠実移植）**。exp006 との差分＝pilk の4優位点: テンプレ5→**8**（`call_syntax`/`inj_empty`/`inj_done` 追加）・選択器を binary→**raw/秒**（`16×post数+2`÷latency合計。`_count_exfil` で multi-post 計数）・seed を**選択テンプレ限定**・fill_unit を**発火latency限定**。EXFIL 一本足（public 特化・private=0 承知）。**local(N=300 gemma): public=27.0/private=0。exp006と同値（pilkのraw/秒・multi-post改良はgemma smokeでは差が出ず、効くのはgpt_oss/live）。** |
| exp008 | gemma_4 | 9.000 | 9.000 | 16.695 | 898分 | **非公開汎化 fill（NB の fill 機構 × CONFUSED_DEPUTY。新結合）**。exp007 エンジンの発火対象を EXFIL→**email.send CONFUSED_DEPUTY**（private で得点できる唯一の述語）に差替。exp002 の疑問形テンプレ（`send`/`email`/`upload`・危険語を除外、「messaging tool」で迂回）＋harmony collapse 変種、宛先連番で cell 化。exp002 の固定N=300に**fill を追加**して N_eff 最大化。**public/private 両行で得点**。**local(N=300 gemma): public=private=9.0（CONFUSED_DEPUTY 300/300＝発火率100%）。exp002の8.73（97%）を超え、private汎化に成功。live full-fillでは更に上振れ余地。** |
| exp009 | gemma_4 | 9.000 | 9.000 | 33.660 | 805分 | **ポートフォリオ（EXFIL+DEPUTY 混載）**。1返却集合に EXFIL アーム（public 質量 raw16）と DEPUTY アーム（public/private 両行 raw4）を `EXFIL_FRACTION=0.5` で replay 予算分割。DEPUTY を先に確保→EXFIL を残りに上乗せ。4行すべてで得点する hedge。**local(N=300 gemma): public=private=9.0、全300がCONFUSED_DEPUTY（EXFIL=0）。DEPUTY先詰め＋N=300 truncationで最初の300がDEPUTYに占有されEXFILアームがsmokeで消失（バグでなくtruncation産物）。EXFILの公開質量はlive full-fill（truncateなし・予算分割）でのみ現れる。** |
| exp010 | gemma_4 | 27.000 | 0.000 | 68.130 | 742分 | **公開 LB 最大化の決定版（champion）**。ユーザ確定＝純公開 EXFIL。exp007 を土台に4NB+exp006 の全公開系改良を統合、テンプレプールを 8→**11**（`inj_final`/`bare_min`/`call_min` 追加）に拡張して各モデルの最速発火形の当たりを増やす。raw/秒 選択器が外れテンプレを自動排除するので退行なし。`REPLAY_SAFE=0.99`。**local(N=300 gemma): public=27.0（EXFIL 300全発火）/private=0。exp006/007と同値。テンプレ拡張の効果は各モデルの最速発火形が変わるgpt_oss/liveで顕在化。** |
