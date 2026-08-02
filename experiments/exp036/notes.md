# exp036 — deep-forge（reasoning-effort 抑制 + wrap-up 崩壊）★本命

Round 6（抜本転換／public 100+）の本命。土台は exp028（champion 90.99）のエンジン（1 バイト不変）。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- 採点数学と Discussion 網羅で確定した唯一の未解決フロンティア＝**gpt-oss の deliberation を token-level
  Harmony forge で削る**（Cleanor Labs「自然言語の skip analysis は無効・reasoning-effort 到達方法は未発見」）。
- 現行 forge は空 analysis で pre-tool CoT を飛ばすだけ。deep-forge で **(a) 偽装 system の `Reasoning: low`
  で reasoning-effort を低に寄せ**、**(b) commentary チャネル直開きでツール呼びへ最短誘導**して、
  forge 後も支配的な出力トークンをさらに削る。当たれば gpt-oss 行 85→100 圏 → mean 100+。

## 変更点（vs exp028）
- TEMPLATES に `df_effort`（system Reasoning: low）/`df_commentary`（commentary 直開き）の 2 変種を追加。
  pool = verbose/lean/forge/df_effort/df_commentary（5 arms）。`PROBE_REPS 4→3`（arms 増の probe 相殺）。
- エンジン（warm-up ループ外・effective_cost race・replay-safe fill・`REPLAY_SAFE_FRAC=0.995`）は不変。

## local の読み方（gemma・N=300）
- gemma は forge/deepforge が format error で発火0→min_fire で自動除外され **verbose が選ばれる**（正しい）。
- 判定は **健全性のみ**: stderr の `name:fires/attempts@cost` で **選択形の fire率 ≥ verbose**・非クラッシュ・
  private=0。deep-forge の真価は gpt_oss/live のみ。

## live 安全性（INVALID/VOID 回避）
- 偽装列が tokenizer とズレれば probe で発火せず verbose へ縮退（fail-closed）。`REPLAY_SAFE_FRAC=0.995` で
  KV-cache warm→cold の過小評価 VOID に cold 余裕。probe/fill/replay とも hops=8。当たり版は best-of で採る。

## 評価結果（make eval）
- `make eval EXP=exp036 CANDIDATES=300`（gemma・N=300・2並列枠厳守）。
- 所見: （eval 後に追記）
- LB: （live 提出はユーザー明示指示時のみ。best-of。ここに記入）
