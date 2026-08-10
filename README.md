# kaggle_ai_agent_security

Kaggle コンペ
[**AI Agent Security – Multi-Step Tool Attacks**](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks)
のソリューション開発リポジトリ。`Python 3.12` / `uv` / `llama.cpp`。

## 概要

ツール使用型 LLM エージェント（gpt-oss / gemma）に対する **再現可能なマルチステップ攻撃**を
発見する探索アルゴリズムを実装するコンペ。学習（training）は無い。

- **提出物**: `AttackAlgorithm` クラス（`run(env, config) -> list[AttackCandidate]`）を実装した
  `attack.py` と、それを `/kaggle/working/attack.py` へ書き出す Kaggle Notebook。
  評価基盤が `attack.py` をロードして攻撃候補を採点する。
- **スコア**: `gpt_oss_public` / `gpt_oss_private` / `gemma_public` / `gemma_private` の 4 値。
- **制約**: インターネット無効・`seed=123`・9000 秒/モデル/フェーズ・候補 ≤2000（実用 ~600）・
  メッセージ連鎖 ≤32・各 ≤2000 文字・ツールホップ ≤8。
- **採点する述語**: EXFILTRATION / UNTRUSTED_TO_ACTION / DESTRUCTIVE_WRITE / CONFUSED_DEPUTY。

詳細は [`docs/competition-research/`](docs/competition-research/01-competition-overview.md)（コンペ仕様・SDK 解析）。

## プロジェクト構成

```
kaggle_ai_agent_security/
├── pyproject.toml / uv.lock / .python-version   # uv パッケージ管理（Python 3.12）
├── Makefile                                     # ワークフロー集約（make help）
├── .claude/skills/lb-submit/                    # LB 提出＋採点結果の記録スキル（/lb-submit）
├── experiments/                                 # 攻撃アルゴリズムの実験単位
│   ├── _template/                               #   new-exp のコピー元（champion エンジン = 歴代最高 LB 90.99）
│   │   ├── attack.py                            #     自己完結 AttackAlgorithm（EXFIL 単発 throughput fill）
│   │   └── kernel-metadata.json                 #     提出 Notebook メタ
│   └── expNNN/                                  #   各実験（_template から生成）
├── scripts/                                     # 運用スクリプト
│   ├── ops/new_experiment.py                    #   実験ディレクトリ生成
│   ├── ops/build_notebook.py                    #   attack.py → submission.ipynb（提出）
│   ├── ops/submit.py                            #   build → kaggle kernels push（提出）
│   ├── ops/build_eval_notebook.py               #   attack.py + eval_driver → eval.ipynb（評価）
│   ├── ops/run_eval.py                          #   build→push→wait→fetch（make eval）
│   ├── ops/build_sdk_dataset.py                 #   評価用 SDK dataset を生成
│   └── eval/eval_driver.py                      #   自己完結の採点ドライバ（Kaggle GPU で実行）
├── docs/                                        # ドキュメント
│   ├── knowledges/                              #   ★知見集（観点別・まずここを読む）
│   │   └── reference/                           #     実績のある attack.py（exp028/073/040）
│   ├── SCORE.md                                 #   スコア表（直接編集。LB 列は /lb-submit が記入）
│   ├── 用語集.md                                #   語彙の統一先
│   └── competition-research/                    #   コンペ仕様と SDK の一次解析
└── vendor/aicomp_sdk_pkg/                      # 公式 SDK（MIT・git 管理・展開済み）
```

## セットアップ

```bash
uv python pin 3.12
uv sync                       # 依存をインストール（.venv 作成）

# 公式 SDK（MIT・git 管理）。vendor/aicomp_sdk_pkg/ に展開済みで clone に同梱される。
#   評価では SDK dataset として Kaggle に添付し eval_driver が sys.path 解決する（pip install しない）。

# 提出・評価に必要:
#   ~/.kaggle/kaggle.json（Kaggle API トークン。Internet 有効化に電話番号認証も必要）
# 評価（make eval）は Kaggle GPU 上で実モデル採点する。初回は SDK dataset を 1 度アップロードする:
#   make sdk-dataset && kaggle datasets create -p build/sdk_dataset
```

## 典型ワークフロー

```bash
# 0. 初回のみ: 評価 Notebook 用の SDK dataset を Kaggle へアップロード
make sdk-dataset
kaggle datasets create -p build/sdk_dataset      # 2 回目以降は kaggle datasets version

# 1. 実験を作成（_template を複製）
make new-exp NAME=exp001

# 2. Kaggle GPU で採点（build→push→wait→fetch）— 実モデル gpt_oss/gemma_4 × public/private
make eval EXP=exp001 CANDIDATES=30     # smoke。本番は CANDIDATES を外す
                                       # experiments/exp001/scores.json を見て SCORE.md の local 列へ記入

# 3. 提出 Notebook を生成して push
make build EXP=exp001          # experiments/exp001/submission.ipynb を生成
make submit EXP=exp001         # kaggle kernels push（LB へは提出しない）

# 4. LB へ提出して結果を記録（★ユーザ明示指示時のみ・日次上限 5/日を消費）
/lb-submit exp001              # push → Edit 画面から Submit → 採点監視 → SCORE.md 記録
```

attack.py を編集 → `make eval`（Kaggle で採点）→ `make build`/`make submit` を回す。
**同じ `experiments/exp001/attack.py` が評価でも提出でも使われる**（単一の真実源）ため、
評価した実体がそのまま提出される。

## スコア管理

スコアは [`docs/SCORE.md`](docs/SCORE.md) を**直接編集**して管理する（単一ソース）。

- **ローカル列** (`local_public` 等): `make eval` が Kaggle から回収する
  `experiments/<exp>/scores.json` を読んで、その exp の行へ手で記入する
  （`gpt_oss > gemma_4` の優先順で採用）。`public` が公開 LB 相関、`private` は非公開汎化の代理。
- **LB 列** (`lb_public` / `lb_time`): `/lb-submit` スキルが提出から採点完了までを追い、
  `scripts/ops/time_manager.py` の出力を元に記入する。
- **changes 列**: `docs/SCORE.md` に直接記入する（または Claude に依頼）。

## 評価（Kaggle GPU でローカル採点）

`make eval` がローカルから Kaggle API で攻撃を採点する一本道。`scripts/eval/eval_driver.py` が公式採点
（`eval_predicates` / `summarize_attack_findings`）を **生成1回・ガードレール別リプレイ多**で再現し、
`public`（公開 LB 相関）/ `private`（非公開汎化の代理）の 2 ガードレールで採点する。
実モデル（gpt_oss 20b / gemma_4 26B）は GPU 必須のため **Kaggle 上で実行**（Mac/Metal 非対応）。
`make eval` が eval.ipynb の build → `kaggle kernels push` → status ポーリング → `kaggle kernels output`
までを 1 コマンドで回し、`experiments/<exp>/scores.json` を回収する。

## ドキュメント

| ファイル | 内容 |
|---|---|
| [`docs/competition-research/01-competition-overview.md`](docs/competition-research/01-competition-overview.md) | 公式仕様（述語・採点式・提出形式・制約） |
| [`docs/competition-research/02-sdk-analysis.md`](docs/competition-research/02-sdk-analysis.md) | SDK ソース解析（ground truth） |
| [`docs/competition-research/03-agent-behavior-and-scoring-flow.md`](docs/competition-research/03-agent-behavior-and-scoring-flow.md) | エージェント挙動と採点フロー（動的解説） |
