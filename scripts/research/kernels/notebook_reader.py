"""Kaggle カーネル（.ipynb）を nbformat で読み、code + markdown を可読テキストに整形する。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class NotebookCell:
    """ノートブックの 1 セル。"""

    cell_type: str
    source: str
    execution_count: int | None = None


def read_notebook(path: Path) -> list[NotebookCell]:
    """`.ipynb` を読み、セル列を返す。解析に失敗したら生テキスト 1 セルに切り替える（代替＝fallback）。"""
    try:
        import nbformat

        nb = nbformat.read(str(path), as_version=4)
        cells: list[NotebookCell] = []
        for cell in nb.cells:
            cells.append(
                NotebookCell(
                    cell_type=cell.get("cell_type", "raw"),
                    source=cell.get("source", "") or "",
                    execution_count=cell.get("execution_count"),
                )
            )
        return cells
    except Exception as exc:  # noqa: BLE001 - 破損 ipynb でも生テキストで返す
        print(f"[research] nbformat 解析失敗（生テキストで継続）: {path.name}: {exc}")
        text = path.read_text(encoding="utf-8", errors="replace")
        return [NotebookCell(cell_type="raw", source=text)]


def render_notebook(cells: list[NotebookCell], *, raw: bool = False) -> str:
    """セル列を Markdown 風テキストに整形する。

    Args:
        cells: read_notebook の出力。
        raw: True なら整形せず source を連結する。
    """
    if raw:
        return "\n\n".join(c.source for c in cells)
    parts: list[str] = []
    for i, cell in enumerate(cells, start=1):
        if cell.cell_type == "code":
            parts.append(f"# --- cell {i} (code) ---\n```python\n{cell.source}\n```")
        elif cell.cell_type == "markdown":
            parts.append(f"# --- cell {i} (markdown) ---\n{cell.source}")
        else:
            parts.append(f"# --- cell {i} ({cell.cell_type}) ---\n{cell.source}")
    return "\n\n".join(parts)
