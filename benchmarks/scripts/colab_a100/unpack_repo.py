"""アップロードした評価用 repo bundle を Colab に展開する。"""

from __future__ import annotations

import shutil
import tarfile
from pathlib import Path

archive = Path("/content/aas-colab-code.tgz")
destination = Path("/content/aas")
if destination.exists():
    shutil.rmtree(destination)
destination.mkdir(parents=True)
with tarfile.open(archive, "r:gz") as tar:
    tar.extractall(destination, filter="data")
print(f"[unpack] {archive} -> {destination}")

