"""Remove macOS AppleDouble metadata from the temporary Colab repo copy."""

from __future__ import annotations

from pathlib import Path

repo_root = Path("/content/aas")
removed = []
for path in repo_root.rglob("._*"):
    if path.is_file():
        path.unlink()
        removed.append(str(path))

print({"removed": len(removed), "sample": removed[:10]})
