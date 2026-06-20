"""攻撃アルゴリズム — 自己完結ベースライン（experiments/_template）。

評価器は提出された `/kaggle/working/attack.py` を
`importlib.util.spec_from_file_location` で **単一ファイル** としてロードし、
`AttackAlgorithm` クラスの `run(env, config)` を 1 回実行する
（vendor/.../kaggle_evaluation/.../jed_attack_inference_server.py）。

そのため本ファイルは以下を守ること:
  * クラス名は `AttackAlgorithm` 固定（評価器が名前で探す）。
  * 兄弟ファイル（config.py 等）への相対 import を持たない（単一ファイルのため解決不能）。
  * `import aicomp_sdk...` は評価環境に SDK が入っているので利用可。

本テンプレートは SDK 同梱の Go-Explore ベースラインをそのまま継承した出発点。
新しい実験では `make new-exp NAME=expNNN` でこれを複製し、`run()` を改造して
探索戦略を進化させる（述語 stacking / cell 多様化 / 公開ガードレールの穴を突く 等）。
"""

from __future__ import annotations

from aicomp_sdk.attacks.baselines.attacker_goexplore import AttackAlgorithm as _GoExploreBaseline


class AttackAlgorithm(_GoExploreBaseline):
    """SDK の Go-Explore ベースラインを継承した出発点。

    まずはベースラインのまま `make validate` / `make build` / `make submit` が
    通ることを確認し、その後 `run()` をオーバーライドして攻撃候補の質を上げる。
    """

    pass
