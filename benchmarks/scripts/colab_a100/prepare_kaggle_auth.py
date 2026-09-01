"""アップロード済み Kaggle 認証ファイルの権限だけを整える。"""

from __future__ import annotations

import shutil
from pathlib import Path

auth_dir = Path("/root/.kaggle")
auth_dir.mkdir(parents=True, exist_ok=True)
for name in ("access_token", "kaggle.json"):
    path = auth_dir / name
    staged = Path("/content") / name
    if staged.is_file():
        shutil.copy2(staged, path)
    if path.is_file():
        path.chmod(0o600)
        print(f"[auth] ready: {path} ({path.stat().st_size} bytes, mode={oct(path.stat().st_mode & 0o777)})")
