# exp011 — exp006 の probe コスト削減版（単一レバー A/B）

## 狙い（仮説）
- 狙う述語: **EXFILTRATION 一本足**（`http.post` + `data=SECRET_MARKER`、severity5→raw16）。public 特化（private=0 承知）。
- ベースライン: exp006（LB84.78 champion）。**エンジン（probe→select→replay-safe fill）は1バイトも変えない**。
- 仮説: exp010 の退行（テンプレ 11 で LB68）が **probe コスト**（テンプレ数×`PROBE_REPS` の試し打ちが生成予算を食う）由来なら、exp006 より probe を**減らせば** fill 候補（N_eff）が増えて **public LB > 84.78** になるはず。退行の逆方向で検証する。

## 変更点
- `PROBE_REPS` 5 → **3**。
- `TEMPLATES` 5 種 → **3 種**（`plain`/`bare`/`inj_close`）。backup の `bare_ok`/`inj_commentary` を除去。床＋gemma最速＋gpt_oss collapse の機能的最小集合を残す。
- 試し打ち回数 5×5+warmup=26 → 3×3+warmup=10。gpt_oss ~10–24s/回で ~160–380s を fill に回収。
- 据え置き: `REPLAY_SAFE=0.99` / `MIN_FIRE_RATE=0.2` / `CANDIDATE_CAP=None` / `MARKER` / 選択器（`median lat / 発火率`）。
- リスク: 試行減で選択が noisy。ただし選択器と plain 床（FALLBACK_INDEX=0）が保険（fail-closed）。

## 評価結果（make eval）
- `make eval EXP=exp011 CANDIDATES=300 MODELS=gemma_4`（N=300 gemma 固定）:
  - **期待値 = public 27.0 / private 0**（EXFIL 300全発火・block≡fire）。fill の床が動く健全性確認のみ。
  - gemma smoke は collapse を出せず fill 系を区別できない（分析 §3-2）。**真の判定は live LB**（84.78 と比較）。
- 所見:
