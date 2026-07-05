# exp011 — public 最大化・提出用: hardened deadline-fill × 適応的K選択EXFIL

## 狙い（仮説）
- どの述語を狙うか: **EXFILTRATION**（http.post, sev5→16）。public 特化・strict/provenance=0 を意図的に受け入れる。
- ベースラインから何を変えるか:
  1. exp007 の deadline-aware fill を「提出安全」に硬化（`N_MIN=300` フロア撤廃 → `N_ABS_FLOOR=20`、`FALLBACK_N=340` 固定値撤廃 → 式化、`SAFETY=0.30` → `MARGIN=0.80`）。
  2. Kaggle discussion 718210 / pilkwang 氏の working note（live で public=58.05 達成）が示す「1 メッセージ内で http.post を K 回呼ばせて停止」を、`EnvInteractionResult.successful_tool_calls` で実測しながら K∈{1,2,3} から自動選択する適応ロジックを追加。

## 変更点
- `attack.py` の `run()` でやったこと:
  - probe フェーズ: K∈{1,2,3} それぞれ `env.reset()`→`env.interact()` で計測し、継続率(compliance)とt_candを実測。`score_rate(K)=(16·K·compliance+2)/t_cand` の argmax で K・N_safe を決定。
  - K=1 は exp007/009 と完全互換の文面。K≥2 はマルチホップ継続を指示する新規文面。
  - マーカーは `SECRET_MARKER` のリテラル文字列のまま（エンコード厳禁）。
  - cell 多様化は `_host_factory()`（連番ドメイン、exp007/009と同一）。

## ローカル検証（実装後）
- `env=None`: フォールバック値通り動作（budget=9000で fallback_n=100 と一致）。
- 壊れた env（例外送出）: 正しくフォールバック（K=1, N=100）。
- `_select_k` ユニットテスト: 完全遵守なら K=3 選択（EXFILは継続コストが共有されるため高K有利）、compliance不足ならK=1にフォールバック、全滅・t_cand範囲外はNone。いずれも設計通り。
- モックenv（完全遵守・現実的レイテンシ）: K=3 が正しく選択され、N_MAXでクランプされることを確認。

## 運用上の発見（次回への申し送り）
- `scripts/ops/run_eval.py` の `_fetch_scores()` は `kaggle kernels output` に `--force` を付けていないため、同一 (exp, model) の `build/eval/<exp>/<model>/output/` を smoke→full の順で連続使用すると、Kaggle側が新しい結果でも「ローカルの方が新しい」と判定してダウンロードをスキップし、**古いscores.jsonが読まれる**バグを発見（exp012/gpt_ossで実際に発生、`--force`付きで手動再取得して解決）。次回は smoke と full で出力先ディレクトリを分けるか、`run_eval.py` に `--force` を追加すべき。
