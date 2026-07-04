"""experiments/<exp>/attack.py を提出用 submission.ipynb に焼き込む。

評価器は提出された Notebook を実行し、その結果 `/kaggle/working/attack.py` が存在することを
期待する（vendor/.../jed_attack_inference_server.py が同パスを単一ファイルロードする）。
そこで本スクリプトは attack.py の中身を **base64 で 1 セルに埋め込み**、実行時に
`/kaggle/working/attack.py` へ復元するだけの薄い Notebook を生成する。

base64 を使う理由: attack.py に `'''` や任意のバイト列が含まれても壊れない（文字列リテラル
埋め込みのエスケープ事故を避ける）。

併せて kernel-metadata.json の id / title / code_file を exp 名に同期する。

使い方:
    uv run python scripts/ops/build_notebook.py exp001
    # -> experiments/exp001/submission.ipynb と kernel-metadata.json を更新
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

import nbformat as nbf

EXPERIMENTS_DIR = Path("experiments")
KAGGLE_USER = "rikitomo0526"


def _code_cell_source(attack_src: str) -> str:
    """attack.py を base64 で埋め込み、/kaggle/working/attack.py へ復元するセル本体。"""
    b64 = base64.b64encode(attack_src.encode("utf-8")).decode("ascii")
    return (
        "# 自動生成: experiments/<exp>/attack.py を /kaggle/working/attack.py へ復元する。\n"
        "# 評価器はこのファイルを単一ファイルとしてロードして AttackAlgorithm.run() を実行する。\n"
        "import base64\n"
        "import pathlib\n"
        "\n"
        f'_ATTACK_B64 = "{b64}"\n'
        '_src = base64.b64decode(_ATTACK_B64).decode("utf-8")\n'
        '_out = pathlib.Path("/kaggle/working/attack.py")\n'
        "_out.write_text(_src)\n"
        'print("wrote", _out, ":", len(_src), "bytes")\n'
    )


def _serve_cell_source() -> str:
    """評価サーバ（JEDAttackInferenceServer）を起動し提出フォーマットを出力するセル。

    公式 getting-started と同じ: competition data の kaggle_evaluation を sys.path に載せ、
    ``serve()`` で attack.py をロードして採点・submission を出力する。このセルが無いと
    submission.csv が生成されず「submission.csv が必要」提出エラーになる。
    """
    return (
        "import sys, glob\n"
        "from pathlib import Path\n"
        "# competition data 直下（kaggle_evaluation / aicomp_sdk がある）を import パスへ。\n"
        "for _c in glob.glob('/kaggle/input/**/kaggle_evaluation', recursive=True):\n"
        "    _root = str(Path(_c).parent)\n"
        "    if _root not in sys.path:\n"
        "        sys.path.insert(0, _root)\n"
        "    break\n"
        "# 評価サーバ起動 → attack.py をロードし submission を出力（実採点は競技 rerun 時）。\n"
        "import kaggle_evaluation.jed_attack_134815.jed_attack_inference_server as _srv\n"
        "_srv.JEDAttackInferenceServer().serve()\n"
    )


def build(exp: str) -> Path:
    """experiments/<exp>/attack.py から submission.ipynb を生成し、メタを同期する。"""
    exp_dir = EXPERIMENTS_DIR / exp
    attack_path = exp_dir / "attack.py"
    if not attack_path.is_file():
        raise FileNotFoundError(f"{attack_path} が存在しません")

    attack_src = attack_path.read_text()

    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell(
            f"# {exp} — submission\n\n"
            "① `attack.py` を `/kaggle/working/` へ書き出し、② 評価サーバ `serve()` を起動して"
            "submission を出力する（公式 getting-started と同じ構成）。"
        ),
        nbf.v4.new_code_cell(_code_cell_source(attack_src)),
        nbf.v4.new_code_cell(_serve_cell_source()),
    ]
    nb.metadata["kernelspec"] = {"name": "python3", "language": "python", "display_name": "Python 3"}
    nb.metadata["language_info"] = {"name": "python"}

    out_path = exp_dir / "submission.ipynb"
    nbf.write(nb, str(out_path))
    print(f"[build] {out_path} を生成（attack.py {len(attack_src)} bytes）")

    _sync_kernel_metadata(exp, exp_dir)
    return out_path


def _sync_kernel_metadata(exp: str, exp_dir: Path) -> None:
    """kernel-metadata.json の id / title / code_file を exp 名に揃える。

    既存 id がこの exp の既定 slug（ai-agent-security-attack-<exp>）そのもの、またはその派生
    （末尾にサフィックスを付けた別名、例: -v2）の場合は尊重して上書きしない。Kaggle 側で slug が
    壊れて別名へ手動リネームした値を次回 build で既定 slug に戻さないため。それ以外（別 exp から
    複製した id や未設定）は既定 slug に設定する。
    """
    km_path = exp_dir / "kernel-metadata.json"
    if not km_path.is_file():
        raise FileNotFoundError(f"{km_path} が存在しません")
    km = json.loads(km_path.read_text())
    default_id = f"{KAGGLE_USER}/ai-agent-security-attack-{exp.replace('_', '-')}"
    existing = km.get("id", "")
    if existing != default_id and not existing.startswith(default_id + "-"):
        km["id"] = default_id
        km["title"] = f"AI Agent Security - Attack {exp}"
    km["code_file"] = "submission.ipynb"
    km_path.write_text(json.dumps(km, indent=2) + "\n")
    print(f"[build] {km_path} を同期（id={km['id']}）")


def main() -> None:
    parser = argparse.ArgumentParser(description="attack.py を提出用 submission.ipynb に焼く")
    parser.add_argument("exp", help="実験名 (例: exp001)")
    args = parser.parse_args()
    build(args.exp)


if __name__ == "__main__":
    main()
