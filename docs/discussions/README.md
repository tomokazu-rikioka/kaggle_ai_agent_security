# Discussion 要約索引

このディレクトリは、`Bookmarks.json`（本コンペの Kaggle Discussion URL **24 件**の原本リスト）の中身を
Playwright で本文＋コメントまで取得し、**テーマ別 6 ファイル**に日本語要約したもの。
各 Discussion は「**要旨** → **注目コメント**（運営回答・重要知見・反論）→ **攻略への示唆**（`attack.py` / `validation/` / `SCORE.md` への含意）」で整理している。

- 役割分担: `docs/competition-research/` が**公式仕様・SDK 解析**、本ディレクトリが**参加者・運営の Discussion で得た発見・質問・回答**。
- 取得日: 2026-06-29。当時の評価器バージョンは `v3.1.2`。
- 各行の記法: `**原文タイトル**（ID, 著者）— 1 行要旨`。

## 評価・採点と公式アップデート — [01-評価・採点と公式アップデート.md](01-評価・採点と公式アップデート.md)
運営の評価器更新・FAQ、採点ロジックへのフィードバック、採点関数の変更提案、secret 採点バグ、凍結 LB 問題。

- **Evaluator update and FAQ**（712642, owenvallis）— v3.1.2 展開・9000秒維持/15時間化・EXFIL採点修正・非再採点
- **Evaluator update planned for Monday**（710234, owenvallis）— アップデート予告・時間強制と可逆エンコード認識の2本柱
- **Feedback on Scoring Logic, Evaluation Flow, and Environment**（711457, hiyodori411）— ループ誘発採点・public/private弱相関・サイドチャネル・GPU乖離
- **Feedback: Structural impossibility of predicates + attack.py never sees private env**（712371, Anh Lam）— 2述語が成立不能・private盲目transferでonline適応無し
- **Proposal to modify the scoring function used for the public leaderboard**（709875, MAJ0RT0M）— public採点を多様性報酬へ・URL別cell量産を抑制する提案
- **Could we apply a score multiplier to post-update submissions?**（714765, Pilkwang Kim）— 旧評価器の0点提出がLB上位固定・日付キー倍率で救済提案
- **The Secrets being checked are hardcoded to wrong values**（709539, Renee）— EXFIL判定が誤ったハードコード値照合・構文一致でエンコード回避可

## 攻撃設計と述語 — [02-攻撃設計と述語.md](02-攻撃設計と述語.md)
述語の発火条件・到達可能性（公開ガードレールでの reachability）、探索 対 物量の設計論、ツール名 parser の罠。

- **Working Note : A White-Box, Diversity-Aware Search for Multi-Step Tool Attacks**（712535, たかゆき）— SDK 精読で到達可能述語を導出、単発 post ファームが最良
- **Mental model check: v0.14 search → v0.15 static fill → v0.16 EXF+CD**（712542, Mark Susol）— 探索→物量→EXF+CD の変遷、運営が v3.1.2 訂正
- **Confused about CONFUSED_DEPUTY**（714216, xz）— CD が last_user 部分文字列のみ判定で意図を測れない疑問
- **Gemma4Agent native parser rejects dotted SDK tool names like http.post?**（714306, ys1997）— Gemma4 native parser がドット名 http.post を拒否、GemmaAgent は JSON で可

## 実行時間と候補数バジェット — [03-実行時間と候補数バジェット.md](03-実行時間と候補数バジェット.md)
9000 秒/フェーズの時間バジェット、候補数とスコアの関係、公式文書の時間記述の食い違い。

- **Update on long-running submissions and runtime budgets**（708272, owenvallis）— attack と replay は別フェーズ各9000秒の公式更新
- **Clarification on Replay Runtime vs Published Time Budgets**（709581, Suman Sharma）— replay 支配項は生成トークン量だと運営確認
- **Clarification needed: Errors in Overview vs Data sections on Time Budgets**（708034, g john rao）— 公式の時間バジェット表記矛盾、正は9000秒
- **What is the maximum number of candidates you were able to use without timing out?**（708926, Mando）— 候補600成功/700タイムアウトの実測共有
- **I plotted a table showing the theoretical maximum scores for different candidate counts (200 to 1,200)**（709357, Mando）— 候補数別の理論最大スコア表（18×N、Raw/200）

## 公開/非公開（public/private）汎化 — [04-公開・非公開汎化.md](04-公開・非公開汎化.md)
public/private env の差、候補転送（candidate-transfer）設計。**勝利条件＝private 汎化**の核心。

- **Difference between public/private env**（708629, bruce_was_too_short）— public/private env の差と汎化に関する運営 Q&A
- **On the public-private candidate-transfer setup: a concern + concrete proposals**（711152, Mohammad Shadab Alam）— 候補転送設計への懸念と3つの具体修正提案
- 関連: **Structural impossibility of predicates...**（712371）の「`attack.py` は private env を見られない」論点は[評価・採点](01-評価・採点と公式アップデート.md)に主収録。

## 検証とツール・モデル実行 — [05-検証とツール・モデル実行.md](05-検証とツール・モデル実行.md)
提出前のローカル検証、private 環境の代理実装、GPU 無しでの実モデル実行、運用 Tips。

- **Validate Your Attack Locally to Save Submission Time**（708186, Kh0a）— SDK でローカル採点し提出前に攻撃を検証
- **Private env proxy - validate 1000 candidates in 5m**（714273, MAJ0RT0M）— private 環境を代理実装し 1000 候補を数分検証
- **Run Gemma 4 and Other LLMs in the Competition SDK Without Local/Kaggle GPUs**（713010, Aryan Yadav）— AI Studio 無料枠で GPU 無しに実モデル実行
- **How to not get nerfed when using codex?**（708063, CPMP）— codex の cyber フラグ回避は中立表現が有効

## 提出エラーとプラットフォーム問題 — [06-提出エラーとプラットフォーム問題.md](06-提出エラーとプラットフォーム問題.md)
評価器更新期に多発した提出エラー・format error と、その復旧事例。

- **Persistent "Kaggle Error" on all submissions — platform/scoring issue?**（713764, Gregory L.）— 全提出が約4分でKaggle Error、プラットフォーム障害疑い
- **Finally got a clean score (27.0) under v3.1.2 — format errors aren't the end**（713946, Pilkwang Kim）— format errorの真因は候補過多のタイムアウト、半減で解消

## 横断トピック（相互参照）

- **private 汎化の核心**: 712371（`attack.py` は private env を見ない盲目 transfer）＋ 708629 / 711152。online 適応は前提にできない。
- **候補数 sizing**: 9000 秒/フェーズ律速で replay 総時間が支配（708272, 709581）。実測で候補 ~600 が安全圏（708926, 709357, 712542）。
- **EXFIL の version 依存**: v3.1.2 は `fs.read(secret.txt)` 前提・可逆エンコード（URL/base64/hex/reversal）を認識（709539, 712542, 712642）。ハードコード payload は 0 点。
- **公開 LB の信頼度**: 旧評価器の 0 点提出が LB 上位に固定（714765）。公開 notebook は採点バージョンを疑い、`validation/` のローカル採点を一次シグナルに。
