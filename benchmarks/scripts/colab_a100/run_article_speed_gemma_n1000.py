"""Colab A100: 記事用Gemma累積ベンチを各段階N=1,000で1回測定する。"""

import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")

from article_speed_runner import run

run(
    "gemma_4",
    "benchmarks/scripts/article_speed/gemma_cumulative_variants.py",
    "article_speed_gemma_n1000.json",
    candidates=1000,
)
