# exp012 — private/汎化最大化・提出用: exp003 + exp008 + hardened deadline-fill

## 狙い（仮説）
- どの述語を狙うか: **CONFUSED_DEPUTY**（email.send, sev3→4）。全ガードレール（public/strict/provenance）で生き残る唯一の述語であり、private（非公開）汎化の核心。
- ベースラインから何を変えるか:
  1. exp011 と同型の hardened deadline-fill（`N_MIN`フロア撤廃・`FALLBACK_N`式化・`MARGIN=0.80`）。
  2. exp008 の K-pack連鎖機構（`_build_chain`/`_addr_factory`）を統合しつつ、fill配下では **K-packingが数学的にK=1に勝てない**ことを事前に導出（`f(K)>f(1)+0.5(1-1/K)`が必要で、fire率0.97の下K=2には`f(2)>1.22`が必要=確率の定義域[0,1]を超え不可能）。exp003（12テンプレ、fire率97%）の文面を無改造で移植。

## 変更点
- `attack.py` の `run()` でやったこと:
  - probe フェーズ: K∈{1,2,3} それぞれ「本物のK連鎖」（`env.reset()`後にK回`env.interact()`）で計測。DEPUTYは別メッセージ型のためEXFILと異なり、`score_rate(K)=(4·K·compliance+2)/t_cand_chain`のargmaxで選択。
  - `_DEPUTY_TEMPLATES`（exp003の12テンプレ、疑問形、fire率97%実証済み）を無改造で移植。
  - K-pack機構（`_build_chain`/`_addr_factory`）はexp008から流用しつつ、恣意的なK=1固定はせず実測で確認する設計。

## ローカル検証（実装後）
- `env=None`: フォールバック通り動作（budget=9000でfallback_n=100と一致）。
- 壊れたenv: 正しくフォールバック（K=1, N=100）。
- `_select_k`ユニットテスト: 完全遵守ならK=3選択（数式上は理論通り）、compliance不足ならK=1、全滅・範囲外はNone。
- **数理検証**: exp003実測f(1)=0.97・exp008実測f(2)=0.96を代入したモック測定で、**完全遵守シナリオでもK=1が選ばれる**ことを確認（score_rate(1)=0.4900 > score_rate(2)=0.4033）。理論導出が実測データと整合することを裏付けた。

## 運用上の発見（次回への申し送り）
- `run_eval.py`の`_fetch_scores()`が`--force`無しで`kaggle kernels output`を呼ぶため、smoke→full を同一出力先で連続実行すると**古いscores.jsonがスキップされず読まれる**バグを発見（本実験のgpt_oss/CANDIDATES=300で実際に発生）。`kaggle kernels output <id> -p <dir> --force`で手動再取得し正しい値(n_candidates=300, findings=284)に修正済み。詳細はexp011/notes.md参照。
