---
name: exp-loop
description: AI Agent Security コンペの攻撃探索を、実験No(expNNN)を増やしながら再帰的に反復して最良スコアを目指す自律実験ループ。仮説→2並列eval(N=300 gemma)→docs/analysis記録→改善、を繰り返す。実装・調査は opus サブエージェントに委譲しオーケストレーションに徹する。トリガー: "実験ループ", "再帰的に実験", "expを増やして試行錯誤", "/exp-loop"
---

# exp-loop — 再帰的・自律実験ループ

`experiments/expNNN` を増やしながら、仮説→検証→改善を**止めずに反復**して最良スコアを探索する。
学習は無く `attack.py` の `run()` がコア。詳細な採点構造は CLAUDE.md「このコンペの要点」と
`docs/analysis/` を参照。

## 大原則（過去の失敗から確定）

1. **実験制約は勝手に変えない**。eval は **N=300 固定・gemma のみ**で回す（手法比較の公平性のため）。
   N や制約を変えたくなったら**必ずユーザに確認**してから。安価に絞るなら `CANDIDATES=30` smoke →
   有望なら N=300 full。※ N を勝手に上げると比較が無効化する（CLAUDE.md 教訓参照）。
2. **実装・調査は opus サブエージェントに委譲**。オーケストレータ（このループの主体）は
   attack.py を自分で書かず、コード解析・論文/Discussion 調査・EDA・文書化も委譲する。
   主体の仕事は「仮説選定・2並列割当・eval 駆動と結果回収・ラウンド間の意思決定と反復」。
3. **常に 2 並列**（Kaggle 同時 GPU 枠=2）。3 本以上同時に push しない。
4. **local≠live**。ローカルは replay 締切が無く高 N/高 K で高スコアが出るが提出非再現。
   提出可否は「N×K×t_cand<9000秒/モデル、遅い gpt_oss 律速」で判断（CLAUDE.md 教訓）。
5. **やったこと全てを `docs/analysis/` に集約**（時系列の単一の物語として維持。負の結果も残す）。

## 1 ラウンドの流れ

1. **仮説選定**：現ベストと未探索の穴から、次に試す 2 案を決める（1案=public方向、1案=provenance/strict
   方向、等）。アイデア源は Kaggle 公開 Notebook/Discussion・AI Security/レッドチーム論文・EDA。
2. **委譲（実装）**：各案につき opus サブエージェントを spawn し、`experiments/expNNN/attack.py` を執筆させ
   `make build EXP=expNNN` で単一ファイル自己完結・構文を確認させる（クラス名 `AttackAlgorithm` 固定・
   兄弟 import 禁止・N_CANDIDATES=300）。
3. **eval（2並列）**：`make eval EXP=expNNN MODELS=gemma_4` を 2 本並列で実行し、完了を監視。
   `scores.json` の per-guardrail 値・発火述語数・所要時間を回収し、1 候補あたり raw を逆算して理論値と照合。
4. **記録**：opus に `docs/analysis/2026-07-attack-strategy-evolution.md` へ追記させ、`/update-score expNNN`
   で `docs/scores/SCORE.md` を更新。
5. **意思決定**：結果を踏まえ次ラウンドの 2 案を決める。overfit（public で出て strict/provenance で消える）
   に注意。**止めずに次ラウンドへ**（ユーザが止めるまで反復）。

## 並行調査（ブロッキングしない）

ラウンドと並行して opus に投げてよい非同期タスク：
- provenance で発火する未利用述語の穴ハント（`vendor/aicomp_sdk_pkg/` の predicates/scoring/guardrail 再精読）。
- Kaggle Discussion 最新・AI Security/レッドチーム論文からの fire率/N/新手法アイデア抽出。
- 完了したサブエージェントは解放（知見は docs に永続化してから）。

## eval 運用の注意（詰まったら CLAUDE.md「Kaggle eval 運用の落とし穴」）

- 同時 GPU 枠=2。テスト/提出カーネルの実行も枠を数える。連続 push を避ける。
- 枠オーバーで壊れた kernel id は "Notebook not found" 恒久化 → `EVAL_ID_SUFFIX=-rN` で新 id に切替
  （id・title 両方に付く。title 不一致だと 409 Conflict）。
- CLI キャンセルは走行中 GPU を殺さないことがある。確実な解放は Kaggle UI の Stop Session。

## 提出フェーズへの移行

比較表（provenance/public/strict の各列が N=300 で揃う）が埋まり最良手法が定まったら、
`docs/analysis/2026-07-submission-design-risks.md` の提出設計チェックリストを起点に、
INVALID 安全（両モデル）な構成で `make submit EXP=<best>` する。提出 Notebook は `serve()` セル必須。

## 状態の起点
- 現在の到達点は `docs/scores/SCORE.md` と `docs/analysis/` の最新セクションを読んで把握する。
- 実験制約・方針でユーザ指示があればそれを最優先（本スキルの既定より上位）。
