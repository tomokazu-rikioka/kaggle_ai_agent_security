.PHONY: new-exp validate validate-real build submit status lint format help
.DEFAULT_GOAL := help

KAGGLE := kaggle
EXP ?= exp001
CANDIDATES ?= 30

# === 実験管理 ===

## new-exp: 新しい実験を作成（Usage: make new-exp NAME=exp001 [BASE=_template]）
new-exp:
	@test -n "$(NAME)" || (echo "Usage: make new-exp NAME=exp001 [BASE=_template]" && exit 1)
	uv run python scripts/ops/new_experiment.py $(NAME) --base $(or $(BASE),_template)

# === ローカル検証 ===

# deterministic は実モデルを使わないため、探索は allow ガードレールで回す（public 探索は
# 全ブロックされ候補 0 になる）。配線・採点の疎通確認が目的。実スコアは validate-real で。
## validate: ロジック層検証（deterministic・GPU 不要・数十秒）
validate:
	uv run python -m validation.run_validation \
	  --attack experiments/$(EXP)/attack.py --agent deterministic \
	  --guardrails public,strict,provenance,allow --gen-guardrail allow --budget-s 30 \
	  --summary-out validation/runs/$(EXP)/summary_deterministic.json \
	  --report-out validation/runs/$(EXP)/deterministic.txt

## validate-real: 実モデル検証（gpt_oss・GPU/Metal・要 GGUF）。CANDIDATES で候補数調整
validate-real:
	uv run python -m validation.run_validation \
	  --attack experiments/$(EXP)/attack.py --agent gpt_oss \
	  --guardrails public,provenance --candidates $(CANDIDATES) --budget-s 600 --env gym \
	  --summary-out validation/runs/$(EXP)/summary_gpt_oss.json \
	  --candidates-out validation/runs/$(EXP)/cand_gpt_oss.json \
	  --report-out validation/runs/$(EXP)/gpt_oss.txt

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

# validation/ は ruff 導入前からの既存コード（import の副作用順序に依存）のため lint 対象外。
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
	@echo "make validate EXP=exp001      — ロジック層検証（GPU 不要・数秒）"
	@echo "make validate-real EXP=exp001 — 実モデル検証（GPU/Metal・要 GGUF）"
	@echo "make build EXP=exp001         — 提出用 submission.ipynb を生成"
	@echo "make submit EXP=exp001        — build して kaggle kernels push"
	@echo "make status EXP=exp001        — カーネル実行状態を確認"
	@echo "make lint / make format       — ruff チェック / フォーマット"
	@echo "（スコア表 docs/SCORE.md の更新は /update-score スキル）"
