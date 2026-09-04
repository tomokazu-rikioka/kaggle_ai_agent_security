"""Colab A100: 記事用GPT-OSS累積ベンチを各段階N=1,000で1回測定する。"""

import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")

from article_speed_runner import run

run(
    "gpt_oss",
    "benchmarks/scripts/article_speed/gpt_cumulative_variants.py",
    "article_speed_gpt_n1000.json",
    candidates=1000,
)
