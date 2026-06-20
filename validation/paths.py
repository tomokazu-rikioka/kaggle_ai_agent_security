"""SDK の import パス解決。

`vendor/aicomp_sdk_pkg/`（MIT・private repo なので git 管理）に展開された
aicomp_sdk / kaggle_evaluation を import 可能にする。validation 配下のどのモジュールも、
最初にこれを import すれば `import aicomp_sdk...` がそのまま通る。
旧 `downloads/aicomp_sdk_pkg/` 配置も後方互換でフォールバック解決する。
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# git 管理された vendored SDK を優先。後方互換で旧 downloads/ 配置もフォールバック。
_SDK_CANDIDATES = (
    REPO_ROOT / "vendor" / "aicomp_sdk_pkg",
    REPO_ROOT / "downloads" / "aicomp_sdk_pkg",
)
SDK_PKG_DIR = next((p for p in _SDK_CANDIDATES if (p / "aicomp_sdk").is_dir()), _SDK_CANDIDATES[0])


def ensure_sdk_on_path() -> Path:
    """aicomp_sdk が import できるよう sys.path を整える。SDK パッケージのパスを返す。"""
    if not (SDK_PKG_DIR / "aicomp_sdk").is_dir():
        searched = "\n".join(f"  - {p}" for p in _SDK_CANDIDATES)
        raise RuntimeError(
            "aicomp_sdk が見つかりません。次を探索しました:\n"
            f"{searched}\n"
            "通常は vendor/aicomp_sdk_pkg/ が git 管理されています。"
            "失われた場合は Kaggle からコンペ zip を取得し展開してください。"
        )
    if str(SDK_PKG_DIR) not in sys.path:
        sys.path.insert(0, str(SDK_PKG_DIR))
    return SDK_PKG_DIR


ensure_sdk_on_path()

# パス確定後にのみ import 可能（SDK 同梱の fixtures 解決ロジックをそのまま使う）
from aicomp_sdk.evaluation.ops import resolve_fixtures_dir  # noqa: E402

__all__ = ["REPO_ROOT", "SDK_PKG_DIR", "ensure_sdk_on_path", "resolve_fixtures_dir"]
