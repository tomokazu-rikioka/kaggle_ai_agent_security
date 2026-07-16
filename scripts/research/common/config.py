"""収集ツール全体で共有する定数（コンペ slug・パス・HTTP 設定）。

パスはすべてリポジトリ root からの相対で定義する。CLI は必ず
`uv run python scripts/research/...`（cwd=リポジトリ root）で実行する前提。
"""

from __future__ import annotations

from pathlib import Path

# 対象コンペ（experiments/*/kernel-metadata.json の competition_sources と一致）
COMPETITION_SLUG: str = "ai-agent-security-multi-step-tool-attacks"
# 内部 API のフリーテキスト検索に使う表示名（ListEntities の filters.query）
COMPETITION_TITLE: str = "AI Agent Security"

# 収集キャッシュ（再生成可能。.gitignore 対象）
DATA_DIR: Path = Path("data")
KERNELS_DB: Path = DATA_DIR / "kernels.db"
DISCUSSIONS_DB: Path = DATA_DIR / "discussions.db"
NOTEBOOKS_DIR: Path = DATA_DIR / "notebooks"  # <comp>/<owner>__<slug>/ に .ipynb をキャッシュ
DISCUSSIONS_RAW_DIR: Path = DATA_DIR / "discussions_raw"  # 案B: 事前取得 JSON（<topic_id>.json）

# 人間可読サマリの出力先（既存の要約 md 6本・Bookmarks.json と同居。コミット対象）
DISCUSSIONS_DOCS_DIR: Path = Path("docs/discussions")
BOOKMARKS_JSON: Path = DISCUSSIONS_DOCS_DIR / "Bookmarks.json"

# 内部 API（案A）用エンドポイント
KAGGLE_WEB: str = "https://www.kaggle.com"
KAGGLE_API: str = "https://api.kaggle.com"
HTTP_TIMEOUT_S: int = 30
# 環境変数名（KGAT ベアラートークン）
TOKEN_ENV: str = "KAGGLE_API_TOKEN"
