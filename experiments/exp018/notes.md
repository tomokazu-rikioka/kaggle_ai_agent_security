# exp018 — REPLAY_SAFE 0.99→0.995（予算上限を攻めて N_eff 増）

Round 3 の単一レバー A/B（3本）の1本。頂点 exp006（LB84.78）を種に、**`REPLAY_SAFE` 定数1つだけ**を
0.99→0.995 に上げる。TEMPLATES・エンジン・他定数はすべて exp006 と完全同一。

## 前提（public 飽和）
- `docs/スコア分析と改善方針.md` §1-c のとおり、public は `score ≈ 0.09 × N_eff` に張り付き、
  残る唯一の実レバーは N_eff を増やすこと。

## 狙い（予算上限の押し上げ）
- gateway は返却した全候補を、生成とは別枠の 9000s で hops=8 再実行（リプレイ）する。返却集合の累積
  再実行コストを `REPLAY_SAFE × 9000` で cap している。
- **exp006 の 0.99（cap まで詰めて余裕 ~900s）→ exp018 は 0.995（余裕 ~450s）**。発火率・レイテンシに
  一切触れず、cap を予算の 99.5% まで攻めて N_eff を直接 +~0.5% 増やす純増レバー。
- exp011（PROBE_REPS 削減で選択がノイジー化して退行）とは別機構。**選択の質を落とさず候補数だけ増やす**。

## 変更点（対 exp006）
- `REPLAY_SAFE: 0.99 → 0.995`（`attack.py` の定数1行のみ）。

## 期待値
- **利得は小さい**（+~0.5% N_eff ≈ LB +0.4 程度）。退行はしない代わりに大化けもしない、下限を少し押す一手。
- **gemma smoke（N=300）は ~27.0 に頭打ちが正常**（cap は full-fill でのみ効くため、§5）。優劣は live 提出でのみ確定。

## リスク（3本中で最も高い INVALID リスク）
- 0.995 は再実行の余裕が **~450s に半減**する。live で latency スパイクが起き、再実行が 9000s/モデルを
  超えると `ModelEvaluationTimedOut` → **提出が丸ごと VOID（失格）**。
- exp006 由来の late-fill ハードクランプ（`attack.py` 末尾の比例縮小 `keep = len × cap/実測cost`）は
  残しているので、探索中に実測 cap 超過を検知すれば返却集合を縮小する。だが余裕が薄い点は承知で提出すること。
- **提出前に time_manager で N×24s（gpt_oss 律速）が 9000s 以内かを確認**し、K=1・単発を厳守（K=2 は 14400s で確実に VOID）。

## 評価器との契約（不変条件）
- クラス名 `AttackAlgorithm` 固定。兄弟 import 禁止（単一ファイルロード）。`import aicomp_sdk…` 可。
- `run(env, config)` は `list[AttackCandidate]` を返す。env=None 時は fallback。

## 評価結果（make eval / 提出）
- 未実施。
