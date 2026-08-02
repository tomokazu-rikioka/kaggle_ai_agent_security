# exp030 — 適応統合エンジン（026–028 の勝ちレバーを自己選択する堅牢版）

Round 4（public 最大化・抜本転換）の1本。**最終提出候補**（どのレバーが当たっても取りこぼさない堅牢版）。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- どのレバー（単発throughput / plain 密度 / forge-multipost）が live で効くかは事前に読めない（手元は fill 変種を
  区別不能）。本 exp は **per-model で全アームを同一の実効 raw/秒 で比較し勝者にコミット**する統合器。
  gemma 行は bare 多発(plain 密度)、gpt_oss 行は forge/forge-multipost が勝ちやすいが、アーム集合を両モデルに
  広く用意して selector に任せる。tetsutani 移植ギャップ(82→87.795)も rollback バイアス廃止の再設計で回収を狙う。

## 変更点（vs exp021 / exp026 / exp027 の統合）
- アーム＝`single_verbose`(proven 床)/`single_forge`/`dual_plain`/`triple_plain`/`forge_n2`/`forge_n3`。
  plain 密度は gemma 有利・forge 系は gpt_oss 有利で、両モデルに広く用意。
- selector＝発火率≥0.60・密度アームは exact-fire率≥0.50 の中で **保守的 raw/秒 最大**を採用（単発バイアス無し）。
- **堅牢性**: `single_verbose`(proven ~100% 発火)を最終 fallback 床に持ち、全滅しても単発 champion(≈87.795)を割らない。
- 全アームに replay-safe sizing（`_charged_replay_cost` 積算・`REPLAY_SAFE×9000=8910s` 手前で停止）→ VOID 構造的回避。

## 評価結果（make eval）
- `make eval EXP=exp030`（gemma＋gpt_oss・N=300）で確認: (a) 選択器が走る・(b) アーム別 exact-fire/raw秒・
  (c) 無クラッシュ・(d) 単発床 fallback が機能・(e) private=0。forge アームは `--models gpt_oss` で確認。
- **LB は live 提出でのみ確定**（★ユーザー明示指示時のみ）。026–028 の勝ちレバーが判明したら本 exp が総取りする想定。
- 所見: （eval 後に追記）
