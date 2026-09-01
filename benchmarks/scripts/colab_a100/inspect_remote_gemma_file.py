"""Colab VM上のGemma GGUF実体をサイズとSHA-256で確認する。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

paths = sorted(Path("/content/aas-a100").glob("**/*gemma*UD-Q4_K_M.gguf"))
rows = []
for path in paths:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(32 * 1024 * 1024):
            digest.update(block)
    rows.append({"path": str(path), "size": path.stat().st_size, "sha256": digest.hexdigest()})
print(json.dumps(rows, indent=2))
