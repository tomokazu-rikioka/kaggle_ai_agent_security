.PHONY: new-exp sdk-dataset eval build submit status lint format help
.DEFAULT_GOAL := help

KAGGLE := kaggle
EXP ?= exp001

# === 実験管理 ===

## new-exp: 新しい実験を作成（Usage: make new-exp NAME=exp001 [BASE=_template]）
new-exp:
	@test -n "$(NAME)" || (echo "Usage: make new-exp NAME=exp001 [BASE=_template]" && exit 1)
	uv run python scripts/ops/new_experiment.py $(NAME) --base $(or $(BASE),_template)

# === 評価（Kaggle GPU でローカル採点） ===

## sdk-dataset: 評価 Notebook 用の SDK dataset(assets.zip) を生成（vendor 更新時のみ）
sdk-dataset:
	uv run python scripts/ops/build_sdk_dataset.py

# attack.py を Kaggle GPU 上で実モデル（gpt_oss / gemma_4）採点し scores.json を回収する。
# 採点は public+strict+provenance の 3 ガードレール（生成1回・リプレイ多）。MODELS / CANDIDATES で調整可。
## eval: Kaggle で採点（build→push→wait→fetch）。例: make eval EXP=exp001 CANDIDATES=30
eval:
	uv run python scripts/ops/run_eval.py $(EXP) \
	  $(if $(MODELS),--models $(MODELS),) $(if $(CANDIDATES),--candidates $(CANDIDATES),)

# === 提出 ===

## build: attack.py を提出用 submission.ipynb に焼く
build:
	uv run python scripts/ops/build_notebook.py $(EXP)

## submit: build して Kaggle へ push
submit:
	uv run python scripts/ops/submit.py $(EXP)

## status: カーネル実行状態を確認
status:
	$(KAGGLE) kernels status rikitomo0526/ai-agent-security-attack-$(EXP)

# === コード品質 ===

## lint: ruff チェック（新規コード）
lint:
	uv run ruff check experiments scripts
	uv run ruff format --check experiments scripts

## format: ruff フォーマット（新規コード）
format:
	uv run ruff format experiments scripts

# === ヘルプ ===

## help: ターゲット一覧
help:
	@echo "make new-exp NAME=exp001      — 新しい実験を作成"
	@echo "make sdk-dataset              — 評価用 SDK dataset を生成（vendor 更新時のみ・要 kaggle datasets create）"
	@echo "make eval EXP=exp001          — Kaggle で採点（build→push→wait→fetch）[MODELS=.. CANDIDATES=..]"
	@echo "make build EXP=exp001         — 提出用 submission.ipynb を生成"
	@echo "make submit EXP=exp001        — build して kaggle kernels push"
	@echo "make status EXP=exp001        — 提出カーネルの実行状態を確認"
	@echo "make lint / make format       — ruff チェック / フォーマット"
	@echo "（スコア表 docs/scores/SCORE.md の更新は /update-score スキル）"
