# exp013 — exp006 の統合版（probe 削減＋出力トークン削減の両取り・champion 候補）

## 狙い（仮説）
- 狙う述語: **EXFILTRATION 一本足**（`http.post` + `data=SECRET_MARKER`、severity5→raw16）。public 特化（private=0 承知）。
- ベースライン: exp006（LB84.78 champion）。**エンジンは1バイトも変えない**。
- 仮説: exp011（probe コスト削減）と exp012（出力トークン削減）の**両レバーを同時適用**する。probe 時間の回収と `fill_unit` の縮小が重なって N_eff が最大化し、**public LB > 84.78 の新 champion** になるはず。

## 変更点
- `PROBE_REPS` 5 → **3**（exp011 のレバー）。
- `TEMPLATES` を最短 4 種へ（`plain`/`bare_min`/`bare`/`inj_empty`、exp012 のレバー）。床＋gemma最短（bare_min）＋gemma頑健backup（bare）＋gpt_oss最短collapse（inj_empty）。
- 試し打ち 4×3+warmup=13 回に圧縮しつつ、選択テンプレの `fill_unit` も最小化。
- 据え置き: `REPLAY_SAFE=0.99` / `MIN_FIRE_RATE=0.2` / `CANDIDATE_CAP=None` / `MARKER` / 選択器。
- リスク: 2変更の重畳（試行減で選択が noisy ＋ 短形が flaky）。ただし最悪でも選択器と plain 床へ縮退し発火は維持（fail-closed）。

## 評価結果（make eval）
- `make eval EXP=exp013 CANDIDATES=300 MODELS=gemma_4`（N=300 gemma 固定）:
  - **期待値 = public 27.0 / private 0**（EXFIL 300全発火・block≡fire）。fill の床が動く健全性確認のみ。
  - gemma smoke は 2レバーの効果を出せない（分析 §3-2）。**真の判定は live LB**（84.78 と比較）。
- 提出順の推奨: 高EVの本 exp013 を先に live 提出し 84.78 と比較 → exp011/exp012 でどのレバーが効いたか帰属。
- 所見:
