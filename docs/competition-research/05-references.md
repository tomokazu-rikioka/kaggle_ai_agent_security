# 05 — 参考リンク

> 2026-06-18 取得。Kaggle の discussion/notebook リンクは閲覧にログインが必要。

## A. 公式コンペページ
- コンペトップ / Overview — https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks
- Data — …/data · Code — …/code · Discussion — …/discussion · Leaderboard — …/leaderboard · Rules — …/rules
- SDK（取得済み）: `kaggle competitions download -c ai-agent-security-multi-step-tool-attacks` → `aicomp_sdk` **v3.1.0**（`downloads/aicomp_sdk_pkg/` に展開、git 管理外）

## B. 主要フォーラムスレッド（host = OpenAI/Google/Kaggle スタッフ）
| ID | タイトル | 重要点 |
|---|---|---|
| 708272 | Update on long-running submissions and runtime budgets *(pinned, host)* | **9k 秒/モデル/フェーズ**；評価器タイムアウトのバグ |
| 708034 | Errors in Overview vs Data on Time Budgets *(host 返信)* | ドキュメント矛盾の整理 |
| 708629 | Difference between public/private env *(host 返信)* | **private = ホールドアウト；game-hack 禁止** |
| 708600 | Clarification on private scoring and hidden fixtures *(host 返信)* | private 採点の仕組み |
| 708186 | Validate Your Attack Locally to Save Submission Time | **ローカル検証**；Gemma モデルリンク |
| 708926 | Max candidates without timing out | 600 OK / 700 timeout / 840（11 位） |
| 709285 | Submission runtime far exceeding expectations | replay コスト ≈ N × 平均メッセージ数 |
| 709357 | 理論最大スコア表（候補 200〜1,200） | スコアは候補数にほぼ線形 |
| 708103 | Koopman Operator & MPC; GPT-OSS 3-step *(コミュニティ)* | GPT-OSS は易・Gemma 4 は難 *(未検証)* |
| 708857 | Gemma "dual-obfuscation" *(コミュニティ, 低評価)* | 多言語難読化 *(未検証)* |
| 708063 | How to not get nerfed when using codex (CPMP) | 支援 AI の拒否回避策 |
| 707785 / 707811 | How to get started / Welcome *(pinned, host)* | starter notebook, Discord（非監視） |

## C. エージェント攻撃の文献（背景；コンペ固有ではなく手法を読むため）
- **STAC: Sequential Tool Attack Chaining** — arXiv [2509.25624](https://arxiv.org/abs/2509.25624)。クローズドループ Generator→Verifier→Prompt-Writer→Planner→Judge；個々には無害なツール呼び出しを連鎖させ、意図は最後の呼び出しでのみ露出；失敗ステップを env グラウンディングで修復。ASR > 90%。
- **Indirect Prompt Injection — 大規模公開コンペ** — arXiv [2603.15714](https://arxiv.org/abs/2603.15714)。第三者データ経由の indirect injection；隠蔽（最終応答をクリーンに）が第一級の目標；universal な攻撃が behavior を跨いで転移。
- **Security Challenges in AI Agent Deployment (Gray Swan / ART benchmark)** — arXiv [2507.20526](https://arxiv.org/abs/2507.20526)。**Indirect ASR 27.1% 対 direct 5.7%**；10〜100 試行で ASR ほぼ 100%；堅牢なモデルでチューニングした攻撃は弱いモデルへ転移；堅牢性はサイズと無相関。著名ペイロード: system-prompt-override タグ、faux-reasoning、fake session reset。
- **Measuring AI Agents on Multi-Step Cyber Attack Scenarios** — arXiv [2603.11214](https://arxiv.org/html/2603.11214v1)。長期連鎖；状態維持が支配的な失敗要因；ボトルネックのステップに計算を投下；エージェントは想定外の近道で勝つ。

## D. 注目の公開 Notebook
- `martynaplomecka/getting-started-notebook`（公式ベースライン）
- `pilkwang/ai-agent-replay-dense-exfiltration` · `pilkwang/eda-agent-security-trajectory-search`
- `llkh0a/aas-local-validation`（ローカル検証ハーネス）
- `karnakbaevarthur/multi-endpoint-severity-stacker` · `…/verify-and-keep-deterministic-red-team-attack`
- `yaroslavkholmirzayev/replay-dense-boundary-exact-aggressive` · `caoyupeng/ai-agent-security-v2-exfil-mass-shift`

## E. モデル / ツール
- Gemma ターゲット（ローカル）: `kaggle.com/models/llkh0a/gemma-4-26b-a4b-it-ud-q4-k-m-gguf`（Google ライセンス同意が必要）
- 公式 Discord: `discord.gg/kaggle` — **スタッフ非監視**；公式回答はフォーラムのみ。

## F. この調査の収集方法
- **Kaggle CLI**（`competitions list/files/leaderboard`・`kernels list`・`competitions download`）— メタデータ・リーダーボード・Notebook 一覧・SDK。*CLI に discussion エンドポイントは存在しない。*
- **Playwright MCP**（未ログインブラウザ）— コンペ Overview 本文と全 discussion スレッド内容（Kaggle ページは JS 描画で、`WebFetch` はページタイトルしか返さない）。
- **WebFetch / WebSearch** — arXiv 文献と外部記事。
- **SDK ソース** — `aicomp_sdk` v3.1.0 を取得パッケージから直接読解。
