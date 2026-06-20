# ローカル検証パイプライン — AI Agent Security

`attack.py` を Kaggle に出して LB を待つ（1 提出 7〜十数時間 + 評価器バグ）代わりに、
**手元で同じ採点を再現**する。公式評価器 `kaggle_evaluation/jed_attack_134815/jed_attack_gateway.py`
と同じ SDK 部品（`eval_attack` / `_replay_candidate_trace` / `eval_predicates` / `score_attack`）を
再利用しているので、採点ロジックは ground-truth と一致する。

## 3 行で

```bash
# 0) セットアップ（リポジトリ直下で。依存の正は pyproject.toml）
uv sync                              # 依存をインストール（.venv 作成）
# 以降 `uv run python -m validation...`（または source .venv/bin/activate）

# 1) ロジック層（GPU 不要・数秒）: 自分の attack.py を回帰チェック
python -m validation.run_validation --attack path/to/attack.py --agent deterministic \
    --gen-guardrail allow --guardrails allow,public,strict,provenance

# 2) 実モデル層（GPU/Metal 必須）: 公開 LB と相関するスコア
python -m validation.run_validation --attack path/to/attack.py --agent gpt_oss \
    --guardrails public --candidates 20 --env gym
```

---

## 3 つの検証 tier

| tier | agent | GPU | 速度 | 何がわかるか |
|---|---|---|---|---|
| **ロジック層** | `deterministic` | 不要 | 数秒〜2分 | パイプライン疎通・採点/cell/dedup の正しさ・ガードレール差分。**attack.py の回帰テスト**向け |
| **実モデル層** | `gpt_oss` / `gemma_4` | 必須 | 分〜時間 | **公開 LB と相関する本物のスコア**（実ターゲットを OptimalGuardrail でリプレイ） |
| **汎化代理** | 上記 + `--guardrails strict,provenance` | tier 依存 | 同上 | 非公開 LB へ**転移するか**の代理シグナル（厳格ガードレールで生き残るか） |

> **重要:** `deterministic` はモデル不要の簡易スタブで、`data='demo'` 固定・自前秘密を流出しない。
> taint 系の危険 op は public ガードレールで必ず弾かれるため **`deterministic_public` は構造上ほぼ 0**。
> ロジック層は「**配線と採点の正しさ**」を見るもので、**公開スコアの本物の信号は実モデルが必要**。

---

## Q&A（ユーザーの 3 質問）

### GPU は必要？
- **ロジック層: 不要**（`deterministic`、CPU 数秒）。
- **実モデル層: 必須**だが NVIDIA でなくてよい。コンペは GGUF を llama.cpp で回すので、
  **Mac の Apple Silicon GPU（Metal）でそのまま動く**（本機 M4 Pro で `llama_supports_gpu_offload=True`、
  Metal working set 実測 **≈19GB**）。`gpt-oss-20b Q4_K_M`（約12GB）は **19GB に快適**。
  `gemma-4-26B-A4B Q4_K_M`（約16GB）は 19GB working set だと**余裕僅少**（文脈長を絞る/他アプリ終了）→ Colab/Kaggle 推奨。

### どのくらい時間？（概算・誤差大）
| 構成 | 目安 | HW |
|---|---|---|
| ロジック層 600 候補 | 数秒〜2分 | Mac CPU |
| gpt-oss 10〜20 候補 | 約10〜20分 | Mac Metal |
| 100 候補・public・1〜2モデル | 約1.5〜4時間 | Mac / Colab |
| 約600 候補・両モデル・public | 約8〜16時間（夜間） | Kaggle T4×2 / Colab L4-A100 |

支配項は `候補数 × メッセージ数 × tool hop` の LLM 呼び出し。リプレイはモデルを再実行するので
**ガードレールを増やすほど比例して重い**（既定は public のみ）。連鎖を短く・候補 ≲600 に。

### LB と相関した検証はできる？
- **公開 LB: できる。** 実ターゲットを `public`（OptimalGuardrail = 公開 LB の実体）でリプレイ →
  決定論的（seed 123）なので高相関（KH0A の検証 Notebook が実証）。
- **非公開 LB: 厳密再現は不可**（隠しガードレール+隠しフィクスチャのホールドアウト）。
  `strict` / `provenance` を**代理**にして「**public で出て厳格版で消える攻撃 = overfit**」を選別する。
  数値の予測ではなく**攻撃ファミリの選別**に使う。

---

## ガードレール（`--guardrails`）

| 名前 | 実体 | 用途 |
|---|---|---|
| `public` | `aicomp_sdk/guardrails/optimal.py`（OptimalGuardrail） | **公開 LB の本命。** taint 窓(直近5)で危険 op を遮断 |
| `strict` | `aicomp_sdk/attacks/baselines/guardrail_rules.py` | http.post の data 走査・private-net 遮断。形状が public と違う代理 |
| `provenance` | `validation/provenance_guardrail.py`（自作） | **永続来歴**で全トレースの汚染を追跡し file-wash を無効化。非公開の `persistent_provenance` 代理 |
| `allow` | `aicomp_sdk/attacks/baselines/guardrail_allow.py` | 全許可。疎通確認・探索上限の把握用（LB 無関係） |

---

## 実モデルの GGUF（公式採点と同一）

| ターゲット | repo / file（既定値） | env 上書き |
|---|---|---|
| `gpt_oss` | `unsloth/gpt-oss-20b-GGUF` / `gpt-oss-20b-Q4_K_M.gguf` | `GPT_OSS_GGUF_REPO` `GPT_OSS_GGUF_FILE` `GPT_OSS_MODEL_PATH` |
| `gemma_4`（=`gemma`） | `unsloth/gemma-4-26B-A4B-it-GGUF` / `gemma-4-26B-A4B-it-UD-Q4_K_M.gguf` | `GEMMA_GGUF_REPO` `GEMMA_GGUF_FILE` `GEMMA_MODEL_PATH` |

> ⚠️ 公式「gemma」ターゲットの実体は **Gemma4Agent + 26B**。`aicomp --agent gemma`（gemma-3-4b）は別物なので
> LB 相関には使わない。本パイプラインの `--agent gemma` は自動で 26B（`gemma_4`）にエイリアスされる。

ダウンロード（初回のみ・約12〜16GB）:
```bash
python -m validation.download_models gpt_oss     # gpt-oss-20b Q4_K_M
python -m validation.download_models gemma_4     # gemma-4-26B Q4_K_M（Colab/Kaggle 推奨）
# 取得済みファイルを直接指定する場合:
export GPT_OSS_MODEL_PATH=~/models/gpt-oss-20b-Q4_K_M.gguf
```
RAM が厳しい時は `LLAMA_N_GPU_LAYERS`（GPU に載せる層数）/ `LLAMA_N_CTX`（文脈長, 既定 8192）で調整。

### Mac(Metal)
```bash
uv pip install llama-cpp-python huggingface_hub     # Metal 対応で入る
python -m validation.run_validation --agent gpt_oss --guardrails public --candidates 10 --env gym
```

### Google Colab（ハイブリッド推奨）
`validation/colab_validation.ipynb` を開くだけ。要点:
- ランタイム → GPU（`gemma_4` を回すなら **L4(24GB) か A100**。無料 T4(16GB) は gpt_oss のみ快適）。
- llama.cpp は CUDA ビルド: `CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python`。
- このリポジトリと `downloads/aicomp_sdk_pkg/` を Drive かアップロードで配置 → 同じ CLI を実行。

### Kaggle 無料 GPU（最終相関チェック）
T4×2 = **採点と同一 HW**。新規 GPU Notebook で本リポジトリ + SDK を配置し同じ CLI を実行。
最も忠実だが commit/run 待ちで反復は遅い。提出前の最終確認に使う。

---

## 典型ワークフロー

1. **開発中**: `--agent deterministic --gen-guardrail allow` で attack.py の疎通・採点を即チェック（`python -m validation.selftest` が回帰ガード）。
2. **候補を固定**: `--candidates-out runs/cand.json` で生成候補を保存。
3. **実モデルで採点**: `--candidates-in runs/cand.json --agent gpt_oss --guardrails public,provenance` を Mac/Colab で。生成を再実行せず採点だけ回せる。
4. **汎化チェック**: public で高く provenance/strict で消える候補を捨て、転移する攻撃ファミリを残す。
5. **最終**: Kaggle T4×2 で full 600 候補・両モデルを夜間実行 → 4 行（`gpt_oss_*` / `gemma_4_*`）の表を確定。

## ファイル
- `run_validation.py` — CLI 本体（生成1回 → ガードレール別リプレイ → 採点）
- `agents_local.py` — agent_factory（deterministic / GGUF+llama.cpp 共有ロード）
- `guardrails_local.py` / `provenance_guardrail.py` — ガードレール
- `report.py` — `{agent}_{guardrail}` スコア表 + 述語内訳
- `seed_attacks.py` — 既知発火の種攻撃（疎通確認・出発点）
- `selftest.py` — ロジック層回帰テスト
- `download_models.py` — GGUF 取得ヘルパー
- `paths.py` — SDK の sys.path / fixtures 解決
