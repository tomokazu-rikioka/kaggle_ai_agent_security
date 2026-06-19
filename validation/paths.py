"""SDK の import パス解決。

`downloads/aicomp_sdk_pkg/`（git 管理外）に展開された aicomp_sdk / kaggle_evaluation
を import 可能にする。validation 配下のどのモジュールも、最初にこれを import すれば
`import aicomp_sdk...` がそのまま通る。
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SDK_PKG_DIR = REPO_ROOT / "downloads" / "aicomp_sdk_pkg"


def ensure_sdk_on_path() -> Path:
    """aicomp_sdk が import できるよう sys.path を整える。SDK パッケージのパスを返す。"""
    if not (SDK_PKG_DIR / "aicomp_sdk").is_dir():
        raise RuntimeError(
            f"aicomp_sdk が見つかりません: {SDK_PKG_DIR}\n"
            "Kaggle からコンペ zip を取得し downloads/aicomp_sdk_pkg/ に展開してください。"
        )
    if str(SDK_PKG_DIR) not in sys.path:
        sys.path.insert(0, str(SDK_PKG_DIR))
    return SDK_PKG_DIR


ensure_sdk_on_path()

# パス確定後にのみ import 可能（SDK 同梱の fixtures 解決ロジックをそのまま使う）
from aicomp_sdk.evaluation.ops import resolve_fixtures_dir  # noqa: E402

__all__ = ["REPO_ROOT", "SDK_PKG_DIR", "ensure_sdk_on_path", "resolve_fixtures_dir"]
