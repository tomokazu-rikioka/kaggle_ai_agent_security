# Colab A100 検証

## 目的

Kaggle T4 の GPU 枠を使わず、Colab CLI の A100 で候補を比較する。A100 と T4 の絶対時間は混ぜず、同じA100実行内の ABBA 比で判断する。

## 分析ファイル

- GPT-OSS: [GPT_ANALSYS.md](GPT_ANALSYS.md)
- Gemma: [GEMMA_ANALSYS.md](GEMMA_ANALSYS.md)
- 危険操作語を含まないGPT候補: [SAFETY.md](SAFETY.md)
- 要約: [SUMMARY.md](SUMMARY.md)

## 記録ルール

`SUMMARY.md`は常に冒頭を「GPT有力候補」「Gemma有力候補」の順にし、各案のbaseline比、速度、完全性、採否を先に示す。
新しい結果が出たら詳細節より先に冒頭表を更新し、進行中・採用候補・棄却を明示する。
個々の実験はモデル別分析ファイルへ「検証内容 → 詳細 → 判定」の順で記録する。

## 共通実行条件

- GPU: `NVIDIA A100-SXM4-40GB`
- 実測VRAM: 42,405,855,232 bytes（約39.5 GiB、製品表記40 GB）
- `n_ctx=8192`, `n_gpu_layers=-1`, `max_new_tokens=1024`
- public ガードレールのみ、variant ごとに warmup=1
- Kaggle T4評価で添付したGGUFとサイズ・SHA-256が一致する実ファイルを使用
- モデルmanifest: `benchmarks/scripts/colab_a100/results/model_manifest.json`

## 運用方針

N=10で動作確認し、正常な軸だけN=100、N=2,000へ増やす。Gemmaは動作確認を完了したため、以後はGPTに専念する。Colab A100は2枠を常用し、取得できる場合は3枠を並列利用する。
