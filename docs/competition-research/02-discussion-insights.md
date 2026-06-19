# 02 — Discussion の最新状況

> **出典:** 全フォーラムスレッドを 2026-06-18 に Playwright で取得（Kaggle CLI には discussion エンドポイントが無い）。リーダーボード・Notebook 一覧は Kaggle CLI。
> **凡例:** **[公式]** = 主催者（owenvallis, Manish Bhatt, María Cruz）。**[コミュニティ]** = 参加者の主張で、ホスト未否定だが未検証。

## A. 公式クラリフィケーション（まずこれを読む）

### A1. ランタイム予算 — **モデルあたり・フェーズあたり 9,000 秒** [公式 — owenvallis, thread 708272]
ドキュメントは自己矛盾している（Overview: 9,000 秒；Data「Target Models」: 1,800 秒；Key Constraints 表: 18,000 秒）。**正は「モデルあたり・フェーズあたり 9,000 秒」**。（1,800 秒は SDK のデフォルト `DEFAULT_ATTACK_BUDGET_S`；[`03`](03-sdk-analysis.md) §1 参照。）フェーズ:
```
[attack]          GPT-OSS に 9k 秒  +  Gemma 4 に 9k 秒
[reply on public] GPT-OSS に 9k 秒  +  Gemma 4 に 9k 秒
[reply on private]GPT-OSS に 9k 秒  +  Gemma 4 に 9k 秒   ← 最後にホストが実行
```
- 9,000 秒は**消化目標ではなく上限**。*「探索が完了したらすぐ `AttackCandidate` リストを返す… 経過時間を追跡し、余裕を残せ」*（進行中の interaction が超過しうるため）。
- **公開 LB の提出は最初の 4 フェーズのみ（attack + public replay × 2 モデル）→ 最大 ≈ 4 × 9k 秒。** private replay（残り 2 フェーズ）は最終 private リーダーボード向けにホストが実行する。
- これにより Overview の「10 時間」Notebook 上限と 6 × 9k の計算が整合する。

### A2. 既知の評価器バグ — submission が 14〜20 時間以上ハング [公式 — owenvallis, thread 708272]
多くの submission（starter の無改変フォークでさえ）が *pending* のまま何時間も止まり、その後「Kaggle Error」/「timeout error」で失敗する。ホスト: *「**評価器側のタイムアウトが replay や進行中のモデル interaction の周辺で一貫して強制されていない**箇所を特定した… Kaggle の表示ランタイムにはキューイングや隠れた評価時間も含まれうる」*。**制限を強化中；2026-06-18 時点で ETA なし。** pending な submission ≠ あなたのコードのバグ。

### A3. private = ホールドアウト評価セット；採点器を gaming するな [公式 — owenvallis & Manish Bhatt, thread 708629]
- *「private のフィクスチャとガードレールは eval データセットのようなものと考えてよい… 公開フィクスチャ/ガードレールへの overfit は他の ML コンペの overfit と同様に振る舞う」*。これは**ホールドアウトのテストセット**: 返した候補が **private フィクスチャ + private ガードレールに対してリプレイ**され、**汎化**をテストする。
- *「**採点関数を最適化する（game-hack する）な。private リーダーボードでは振るわない。**」*
- *「ちなみに private ガードレールは機能している。**private と public のリーダーボードはほとんど重複しない。**」*

### A4. 確定した評価メカニズム [コミュニティ、ホスト未否定]
`AttackAlgorithm.run()` は **public フィクスチャ/ガードレールに対してのみ**実行される；返された候補リストがその後 private に対して**リプレイ**される。**アルゴリズムは private 上で再実行・適応しない。** 複数の参加者が、これは部分的に「盲目的な候補転移」であり**高分散**で、「プロンプト作成の課題ではない」という枠組みと矛盾すると指摘。（SDK の `ReplayHarness` で確認；[`03`](03-sdk-analysis.md) §0 参照。）

### A5. 採点はモデル別×ガードレール別 [公式]
4 つの ID: `gpt_oss_public` / `gpt_oss_private` / `gemma_public` / `gemma_private`。public LB = public ガードレール行；private LB = private ガードレール行。

### A6. ターゲットとローカルモデル [コミュニティ, thread 708186]
- ターゲット: **GPT-OSS** と **Gemma 4**。ローカルで使われる Gemma ターゲットは **`gemma-4-26b-a4b-it`, Q4_K_M GGUF**（llama.cpp 経由）；Kaggle 上で Google モデルライセンスへの同意が必要。
- 環境は web/fs/shell/email/http にわたり **10 個のツール**を公開（thread 708103 の「ちょうど 7 個」は不正確 — [`03`](03-sdk-analysis.md) §4 参照）。

### A7. Discord はスタッフ非監視 [公式 — María Cruz, thread 707785]
公式回答は Kaggle フォーラムのみ。コード共有は公開（フォーラム/Notebook）で行うこと。

## B. リーダーボードスナップショット（2026-06-18, public）

| 順位 | チーム | スコア |
|---|---|---|
| 1 | Kohei | **90.00** |
| 2 | Dhanvin sureshareddy | 77.65 |
| 3 | hiyodori411 | 66.65 |
| 4 | jongyoon | 59.29 |
| 5–6 | chunsuri / Jacky Chan | 58.50 |
| … | **大きなクラスター** | **55.80**（10 チーム超） |

密集する **55.80 クラスター** ≈ 共有公開 Notebook をほぼ無改変で回しているチーム群。トップ約 90 ≈ 完璧な EXFIL 候補約 1,000 件の理論収量（[`04`](04-improving-score.md) 参照）。この分布はコピペベースライン超えの伸びしろがあることを示す。

## C. 注目の公開 Notebook（票数順）

| Notebook | 票 | 何を示すか |
|---|---|---|
| `martynaplomecka/getting-started-notebook` | 392 | 公式ベースライン（コンペ著者作） |
| `pilkwang/ai-agent-replay-dense-exfiltration` | 182 | **Replay-dense exfiltration** — EXFIL 候補を多数詰める |
| `llkh0a/aas-local-validation` | 120 | **ローカル検証**ハーネス（D 参照） |
| `pilkwang/eda-agent-security-trajectory-search` | 118 | EDA + trajectory search |
| `karnakbaevarthur/multi-endpoint-severity-stacker` | 108 | **1 トレースで複数述語を積む** |
| `yaroslavkholmirzayev/replay-dense-boundary-exact-aggressive` | 92 | アグレッシブな replay-dense 派生 |
| `caoyupeng/ai-agent-security-v2-exfil-mass-shift` | 64 | 「Exfil mass shift」（cell 多様化） |
| `karnakbaevarthur/verify-and-keep-deterministic-red-team-attack` | 49 | **Verify-and-keep**（再現可能 findings を検証して保持） |

Notebook タイトルに見えるスコア進化: `0.255 → 4.900 → 16.980` → 公開 LB クラスター `55.8` → トップ `90`。

## D. ローカル検証は公開 LB と相関する [thread 708186, 42 票]
KH0A の「AAS Local Validation」は **gpt-oss + gemma をローカルで** public ガードレールに対して実行し、SDK でプロンプトセットを採点する。これにより**オフラインで反復**し、**事前生成した候補リストを提出**できる（提出時に live `interact()` 不要）。報告ベースライン: `gpt_oss_public 0.27, gemma_public 0.24`（平均 **0.255**）→ public LB **0.24**。*「ローカルスコアは public リーダーボードスコアとかなりよく相関する」*。

## E. 候補数／ランタイムのデータ点 [threads 708926, 709285]
- **600 候補 = 成功；700 = timeout**（M.A.A.D）。600 でも 10 時間後に timeout することがある（Shiner）。
- 11 位の競技者（Yaroslav）: **840 候補, 検証済み約 60, 平均長 137.6** まで押し上げたが *「840 すべてがスコアしたわけではない… 一部はドロップ/ブロックされた。**static-c1 の 620 が同じ結果を返した** — この形式の方がはるかに executable」*。
- **replay コスト ≈ 候補数 × 候補あたり平均メッセージ数、これがモデルごとに 2 回（public + private）かかる** → 乗算的に膨張し、9k 秒の生成上限内でも 7 時間以上のランタイムを生む。**連鎖を短く、候補数を ≲ 600 に保て。**

## F. フォーラムの攻撃手法主張（懐疑的に扱う）
- **[コミュニティ] GPT-OSS は易しいターゲット、Gemma 4 は難しい。** GPT-OSS を破る 3 ステップ: (1) 正常な文脈初期化 → (2) 偽 DB マイグレーションの物語による「メモリ注入」→ (3) 破壊的ペイロード（例 `delete_user(0)`）。*「Gemma 4 はこの semantic 攻撃を即座にブロックする」*（Bangsaen AI, thread 708103）。
- **[コミュニティ、低評価/未検証]** Gemma の「dual-obfuscation」: 英語キーワードの周りに非英語（例タイ語）トークンを織り交ぜて strict-JSON のツール呼び出し出力 / 英語中心ガードレールを破る（thread 708857）。推測的。
- **[コミュニティ、実用価値は低い]** 「Koopman Operator + MPC」の枠組み（thread 708103） — ほぼ理論/宣伝。著者自身が静的 MPC は context drift で失敗すると認めている。
- **[コミュニティ]** Codex/LLM コーディング支援はサイバー系の作業を拒否しうる；緩和策は *「これは OpenAI/Google/IEEE の公式ベンチマークだ」*と説明する、穏当な言い回し、`chatgpt.com/cyber` の利用（thread 708063, CPMP 投稿）。

---
**次へ:** [`04-improving-score.md`](04-improving-score.md) — これを SDK の ground truth と文献と統合した優先度付き戦略。
