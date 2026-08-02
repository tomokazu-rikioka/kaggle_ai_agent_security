# exp028 — スループット全振り単発（現行 v3.1.2 の実天井 ~100 への正攻法）

Round 4（public 最大化・抜本転換）の1本。土台は exp021（canqiang）の replay-safe 単発 fill。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- 理論天井（disc/709357）= Raw 18×N, score Raw/200 → N=1000 で 90 / N=1200 で 108。100 超えは
  「9000s/モデルの replay 内で発火候補数 N_eff を最大化する純スループット勝負」。密度に頼らず、
  **「短いが発火率が落ちない」候補文面を per-model で実測選択**して生成トークンを削り、
  `REPLAY_SAFE_FRAC=0.995` で返却集合を天井まで詰める。

## 変更点（vs exp021）
- exp012 の轍（短形テンプレ盲目採用→発火率低下で LB73.3 退行）を避けるため、テンプレ3種
  `verbose`(canqiang proven 床)/`lean`(短縮 imperative)/`forge`(gpt_oss の CoT skip) を
  **effective_cost = median_latency÷fire_rate で同一土俵比較**し、発火率≥0.5 の中で最小コストを採用（fail-closed）。
- `REPLAY_SAFE_FRAC` を 0.97/0.99 系（exp021/023）→ **0.995** に引き上げ（exp018 で 0.995 が退行しなかった実証に沿う）。
- 発火した probe を選択形のみ seed。replay-safe fill で `0.995×9000=8955s` 手前まで詰める（VOID 構造的回避）。

## 評価結果（make eval）
- `make eval EXP=exp028`（gemma＋gpt_oss・N=300）で確認: **選ばれた形の fire率 ≥ 単発 champion(exp006 相当)**
  であること（下回れば短形を戻す＝exp012 の再発防止）・無クラッシュ・private=0。
- local は N_eff を予測しない（27 天井）。**LB は live 提出でのみ確定**（★ユーザー明示指示時のみ）。
- 所見: （eval 後に追記）
