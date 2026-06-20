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
├── .claude/skills/update-score/                 # スコア表更新スキル（/update-score）
├── experiments/                                 # 攻撃アルゴリズムの実験単位
│   ├── _template/                               #   new-exp のコピー元（動くベースライン）
│   │   ├── attack.py                            #     自己完結 AttackAlgorithm
│   │   ├── kernel-metadata.json                 #     提出 Notebook メタ
│   │   └── notes.md                             #     実験メモ
│   └── expNNN/                                  #   各実験（_template から生成）
├── scripts/ops/                                 # 運用スクリプト
│   ├── new_experiment.py                        #   実験ディレクトリ生成
│   ├── build_notebook.py                        #   attack.py → submission.ipynb
│   └── submit.py                                #   build → kaggle kernels push
├── validation/                                  # ローカル検証パイプライン（公式採点を再現）
├── docs/                                        # ドキュメント
│   ├── scores/SCORE.md                          #   スコア表（直接編集 / update-score スキル）
│   └── competition-research/                    #   調査・戦略ノート
└── vendor/aicomp_sdk_pkg/                      # 公式 SDK（MIT・git 管理・展開済み）
```

## セットアップ

```bash
uv python pin 3.12
uv sync                       # 依存をインストール（.venv 作成）

# 公式 SDK（MIT・git 管理）。vendor/aicomp_sdk_pkg/ に展開済みで clone に同梱される。
#   validation/paths.py が sys.path に追加してロードする（pip install しない）。

# 実モデル検証や提出に必要:
#   ~/.kaggle/kaggle.json（Kaggle API トークン）
#   GGUF モデル: uv run python -m validation.download_models gpt_oss
```

## 典型ワークフロー

```bash
# 1. 実験を作成（_template を複製）
make new-exp NAME=exp001

# 2. ロジック層で検証（deterministic・GPU 不要・数秒）— 配線と採点の確認
make validate EXP=exp001

# 3. 実モデルで検証（gpt_oss・GPU/Metal・要 GGUF）— 公開 LB と相関する本物スコア
make validate-real EXP=exp001 CANDIDATES=30

# 4. 提出 Notebook を生成して push
make build EXP=exp001          # experiments/exp001/submission.ipynb を生成
make submit EXP=exp001         # kaggle kernels push
make status EXP=exp001         # カーネル実行状態を確認
```

attack.py を編集 → `make validate` → `make validate-real` → `make build`/`make submit` を回す。
**同じ `experiments/exp001/attack.py` がローカル検証でも提出でも使われる**（単一の真実源）ため、
手元で検証した実体がそのまま提出される。

## スコア管理

スコアは [`docs/scores/SCORE.md`](docs/scores/SCORE.md) を**直接編集**して管理する（単一ソース）。

- **ローカル列** (`local_public` 等): `make validate*` が `validation/runs/<exp>/summary_*.json` を
  書き出し、`/update-score <exp>` スキルがその exp の行へ反映（実モデルのサマリを優先採用）。
  `public` が公開 LB 相関、`provenance`/`strict` は非公開汎化の代理。
- **LB 列** (`lb_gpt_oss_public` 等) / **changes 列**: `docs/scores/SCORE.md` に直接記入する
  （または Claude に依頼）。1 提出で 4 スコアが返るので、確認して転記する。

## ローカル検証

`validation/` が公式採点（`eval_predicates` / `score_attack`）をオフライン再現する。
3 ティア（ロジック層 / 実モデル層 / 汎化代理）。詳細は
[`validation/README.md`](validation/README.md)。

## ドキュメント

| ファイル | 内容 |
|---|---|
| [`docs/competition-research/01-competition-overview.md`](docs/competition-research/01-competition-overview.md) | 公式仕様（述語・採点式・提出形式・制約） |
| [`docs/competition-research/02-sdk-analysis.md`](docs/competition-research/02-sdk-analysis.md) | SDK ソース解析（ground truth） |
