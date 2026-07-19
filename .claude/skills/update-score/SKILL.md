---
name: update-score
description: docs/SCORE.md（実験スコア表）の行を更新する。make eval の scores.json から local スコアを反映、LB スコアや変更内容の記入に使う。トリガー: "スコア更新", "SCORE.md 更新", "スコアを記入", "/update-score"
---

# update-score

`docs/SCORE.md` は実験スコアの**単一ソース**で、直接編集して運用する
（`changes.yaml` / `lb_scores.yaml` のような入力ファイルは使わない）。
本スキルは指定された exp の行を upsert（無ければ追加・有れば更新）する。

## 対象 exp の特定
- 引数で exp 名（例 `exp001`）を受ける。省略時は文脈上の対象 exp を使い、判らなければユーザーに確認。

## 手順

### 1. local スコアを取得
`experiments/<exp>/scores.json`（`make eval` が回収するマージ済み出力）を読む。複数モデルがあれば
**gpt_oss > gemma_4** の優先順で 1 つ採用する。次のコマンドで採用モデルと public/private
スコアを取得する（先頭の `EXP=exp001` だけを対象 exp 名に置き換える）:

```bash
EXP=exp001 uv run python - <<'PY'
import json, os, pathlib
exp = os.environ["EXP"]
prio = ["gpt_oss", "gemma_4", "gemma"]
path = pathlib.Path(f"experiments/{exp}/scores.json")
if not path.is_file():
    print("NO_SCORES")
else:
    models = json.loads(path.read_text()).get("models", {})
    model = next((m for m in prio if m in models), next(iter(models), None))
    if model is None:
        print("NO_SCORES")
    else:
        g = models[model].get("guardrails", {})
        def s(k):
            v = g.get(k, {}).get("score")
            return "-" if v is None else f"{v:.3f}"
        print(model, s("public"), s("private"))
PY
```

`NO_SCORES` が出たら、「先に `make eval EXP=<exp>`（Kaggle GPU で採点）を実行してください」と案内して終了する。

### 2. docs/SCORE.md を更新
- `docs/SCORE.md` を Read し、表のヘッダ列を確認する。
- 対象 exp の行があれば、`local_agent` と `local_public` / `local_private`
  列を Edit で更新する。無ければ表の末尾に新しい行を追加する
  （LB 列は `-`、`changes` 列は空または指定値）。
- **`lb_*` 列と `changes` 列は既存値を保持する**。ユーザーが LB スコアや変更内容を提示した
  場合のみ、その該当セルを記入する。
- 列数・区切り（`|`）がズレないよう、Markdown テーブルの整合を保つ。

### 3. 報告
どの行をどう変えたか（before → after）を簡潔に伝える。

## 注意
- スコアの単一ソースは `docs/SCORE.md`。yaml の入力ファイルは作らない。
- 手動列（`lb_*` / `changes`）を勝手に消さない。local 列のみ自動反映する。
- `local_public` が公開 LB と相関、`local_private` は非公開汎化の代理。
