# 実験スコア一覧

> 用語は [用語集](knowledges/用語集.md) を参照。知見の入口は [knowledges/](knowledges/README.md)。

> このファイルは直接編集して運用する（スコアの単一ソース）。
> - `local_*` 列: `make eval` で取得（回収）した `experiments/<exp>/scores.json` を読んで記入する（`gpt_oss > gemma_4` 優先）。`local_agent` は採用したモデル名。
> - `lb_public` 列・`lb_time` 列: `/lb-submit` スキルが提出から採点完了まで追い、`scripts/ops/time_manager.py` の出力から記入する。
> - `lb_time` の意味: 提出（submit）から採点 COMPLETE 検知までの経過時間（分）。キュー待ちを含むので実採点時間の上限目安。
> - `changes` 列: 直接記入する（または Claude に依頼）。
> - `local_public` が公開 LB と相関し、`local_private` は非公開への汎化の代理。

> **exp001–080（Round1–14）の実測値は [knowledges/02-実測台帳.md](knowledges/02-実測台帳.md) 2-10 に移した。**
> この表は exp081 以降を記録する。

## 実験一覧

| exp | local_agent | local_public | local_private | lb_public | lb_time | changes |
|-----|------------|------|------|------|------|---------|
| exp001 | - | - | - | 88.425 | 1028分 | champion 安全アンカー（cap0.993/probe2・3-arm race+fail-closed）。2026-08-10 提出（DAILY 1/5）。**結果 LB88.425 完走（非VOID）。proven な床**。 |
| exp002 | - | - | - | 89.775 | 1027分 | finalization抑制（race に forge_final 追加・fail-closed で退行不能）。2026-08-10 提出（DAILY 2/5）。**★本バッチ最高 LB89.775 完走。champion(88.425)を同一ドローで +1.35 上回る（forge_final が寄与した弱いが正の signal・分散±3-8内）**。 |
| exp003 | - | - | - | 88.605 | 1025分 | overfill×proven forge（cap0.997・8/5部分スコアで上振れを VOIDなしに狙う）。2026-08-10 提出（DAILY 3/5）。**結果 LB88.605 完走。cap0.997 は従来 VOID 帯だが8/5で完走実証（overfill 保険は有効・ただし+点は小）**。 |
| exp004 | - | - | - | 85.995 | 964分 | multi-message multipost（独立M-turn連鎖16M+2・raw/秒で条件付き採用）。2026-08-10 提出（DAILY 4/5）。**結果 LB85.995 で完走（非VOID・964分）。multipost は frontier 突破せず ~86帯**。 |
| exp005 | - | - | - | 88.560 | 1023分 | raw-per-sec+P75 sizing+overfill（yw8837 88.875 移植）。2026-08-10 提出（DAILY 5/5）。**結果 LB88.560 完走。yw8837 原本 88.875 とほぼ同帯（忠実移植を実証）**。 |
| exp006 | - | - | - | - | - | **Round16・DEPUTY-stack**（proven +3.5・dimong4 90.09 の勝因）。race に dual(EXFIL+CONFUSED_DEPUTY "forward a note")/dual_forge を追加し selector を **raw-per-replay-second** に作り替え（time/fire では +4raw が見えず dual が選ばれない）。gemma 行=dual・gpt_oss 行=forge に自動 routing・fail-closed。2026-08-12 提出（DAILY 1/5）。判定=live LB。目算 ~92-93。 |
| exp007 | - | - | - | - | - | **Round16・reasoning root-forge**（本命の100+スイング・開示未踏）。Harmony `special=True` 無サニタイズ（`llama_chat_format.py:662`）を突き、偽造 system/developer "Reasoning: low"（+forge_reason）を race に追加＝**hop1 CoT に届く唯一の候補側経路**。fail-closed で proven forge 縮退。2026-08-12 提出（DAILY 2/5）。判定=live LB。効けば90突破〜100+（未検証）。 |
| exp008 | - | - | - | 62.460 | 1146分 | **Round16・reasoning-forge×multi-hop multipost**（100+スイング②）。1 user_message で K∈{1,4,6} 個の別ドメインへ順次 post 指示＋reasoning-forge、候補ごとの実発火 post 数を計測し raw/秒が単発超え&発火≥2 のみ採用・下回れば単発縮退。2026-08-12 提出（DAILY 3/5）。**結果 LB62.460 完走（非VOID）＝床(~89)を大きく下回る**。reasoning-forge/multipost が cold replay で劣化し、warm probe ベースの fail-closed が守り切れず（Cleanor 警告「in-run() timing ≠ replay」の実証）。**reasoning-forge は負け筋と判明**。 |
| exp009 | - | - | - | - | - | **Round16・Aug-5 true overfill**。replay-cost cap 撤廃・停止=generation-wall のみ・validate を **max_tool_hops=1**（S1 確定・greedy 決定的で固定8-hop replay でも hop0 発火）で検証半減→HARD_N_CAP=2000 まで返す（部分点前提）。2026-08-12 提出（DAILY 4/5）。判定=live LB。目算 +1〜3。 |
| exp010 | - | - | - | 68.985 | 1142分 | **Round16・combined all-public-levers**（A+B+C 合成・最高天井）。raw/秒 race に dual/dual_forge/reason_low_sys/forge_reason を全部入れ overfill sizing で返す。各レバー独立 fail-closed。2026-08-12 提出（DAILY 5/5）。**結果 LB68.985 完走（非VOID）＝床を下回る**。合成に reasoning-forge 系を含めたため exp008 と同様に劣化（raw/秒 selector が warm probe で reasoning arm を誤選択）。**合成には reasoning-forge を入れてはいけない**（DEPUTY-stack+overfill のみに絞るべき）。 |
