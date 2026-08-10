# AGENTS.md

このファイルは Agent への指示書。回答は日本語で、実施予定と実施内容を説明すること。

## プロジェクト概要

Kaggle「AI Agent Security – Multi-Step Tool Attacks」のソリューション開発リポジトリ。ツール使用型 LLM エージェントへの再現可能なマルチステップ攻撃を見つける探索アルゴリズムを実装する。学習（training）は無く、`attack.py` の `run()` がコア。

## 開発環境

- Python 3.12 / `uv` 管理。スクリプトは `uv run ...` で実行。
- ruff（`line-length=120`, `select=E,W,F,I,UP,B,SIM`）。`make lint` / `make format`。
- 公式 SDK は `vendor/aicomp_sdk_pkg/`（MIT・private repo なので git 管理）。Kaggle 評価では SDK をdataset として添付し `scripts/eval/eval_driver.py` が `--sdk-root` で sys.path 解決する（pip installしない）。`import aicomp_sdk...` はこれで解決。

## アーキテクチャ

### 提出の仕組み（最重要）

評価器（`vendor/.../kaggle_evaluation/.../jed_attack_inference_server.py`）は`/kaggle/working/attack.py` を `importlib.util.spec_from_file_location` で単一ファイルとしてロードし、`AttackAlgorithm.run(env, config)` を 1 回実行する。

そのため `attack.py` は次を守る:
- クラス名は **`AttackAlgorithm` 固定**。
- **兄弟ファイルへの相対 import を持たない**（単一ファイルのため解決不能）。設定値はファイル冒頭の定数か `AttackAlgorithm.__init__(self, config)` の `config` で持つ。
- `import aicomp_sdk...` は評価環境に SDK があるので利用可。

提出 Notebook の役割は「`attack.py` を `/kaggle/working/` へ書き出すだけ」。
`scripts/ops/build_notebook.py` が attack.py を **base64 で符号化して 1 セルに埋め込む**（`'''` の混入に強い）。Notebook 自体は採点に関与しない（学習コンペの推論 Notebook とは別物）。

#### LB 提出までの流れ（push → Edit 画面から Submit）

**手順の正典は `/lb-submit` スキル**（`.claude/skills/lb-submit/SKILL.md`）。提出から
`docs/SCORE.md` への記録までを一本で持つ。ここには背景と硬い制約だけ置く。

`make submit`（`kaggle kernels push`）は**カーネルをデプロイ・実行するだけ**で、
リーダーボード（LB）への提出は行わない。LB 提出は Kaggle の Edit（ノートブック編集）画面の
「Submit to competition」からのみ通る。おおまかにはpush → COMPLETE を待つ → Notebook の Edit 画面 → 右パネル「Submit to competition」→ Submit、でDAILY SUBMISSIONS が `n/5` に増えれば受理。採点はキュー込みで概ね ~800–1000 分。

**このデプロイ（LB 提出）のブラウザ操作は Claude in Chrome（`mcp__claude-in-chrome__*`）を使う**。

> ★**LB 提出は、ユーザから明示的に指示された場合のみ実行する。** エージェントが自分の判断で提出を始めてはいけない。
> **`/lb-submit` の起動がその「明示的な指示」にあたる**。起動後は都度確認を取らずに Submit まで> 進めてよいが、各 Submit の直前にスクリーンショットで対象 exp / Version / 残枠を目視し、食い違ったら押さずに止める。

### 実験構成

`experiments/expNNN/{attack.py, kernel-metadata.json}` のフラット構成。探索アルゴリズムの構造そのものを差し替えるため、child-exp（YAML 差分）は採用しない。**同じ attack.py が評価でも提出でも使われる**ので、評価した実体がそのまま提出される。
`_template/attack.py` は提出フォーマットの最小骨組み（`run()` を実装する雛形）で、`make new-exp` はこれを複製する。実績のある実装は `docs/knowledges/reference/` を参照。

### 評価（Kaggle GPU でローカル採点）

`make eval EXP=expNNN` が手元から Kaggle API で攻撃を採点する一本道。`scripts/ops/run_eval.py` がモデルごとに `eval.ipynb` を build（`scripts/eval/eval_driver.py` と attack.py を base64 で埋め込む）→`kaggle kernels push` → 実行状態を定期確認（ポーリング）→ `kaggle kernels output` で `scores.json` を取得し `experiments/<exp>/scores.json` にマージする。
- 採点ドライバ `scripts/eval/eval_driver.py` は公式採点（`eval_predicates` /
  `summarize_attack_findings`）を **生成は1回・ガードレール（防御機構）別に再実行（リプレイ）を多数**で再現する自己完結ファイル。
- モデルは `gpt_oss`（20b）/ `gemma_4`（26B）。GPU 必須なので Kaggle 上で実行。
- SDK は `make sdk-dataset` で作る Kaggle dataset（`rikitomo0526aiagent-security-sdk`）を Add Input で添付（vendor 更新時のみアップロード）。GGUF は Internet ON で HF hub から取得。

### スコア管理と知見

`docs/SCORE.md` が**スコアの単一ソース**（直接編集して運用、yaml 入力ファイルは使わない）。ローカル列（`local_*`）は `make eval` が回収する `experiments/<exp>/scores.json` を読んで手で記入する（`gpt_oss > gemma_4` 優先）。LB 列（`lb_public` / `lb_time`）は `/lb-submit` が`scripts/ops/time_manager.py` の出力から記入する。changes 列は直接記入する。
