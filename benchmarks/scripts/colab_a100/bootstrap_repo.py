"""Uploaded archiveをColabの/content/aasへ展開する。"""

import shutil
import tarfile
from pathlib import Path

archive = Path("/content/aas-colab-code-clean.tgz")
target = Path("/content/aas")
if target.exists():
    shutil.rmtree(target)
target.mkdir(parents=True)
with tarfile.open(archive, "r:gz") as bundle:
    bundle.extractall(target, filter="data")
print(f"[bootstrap] extracted {archive} to {target}")
