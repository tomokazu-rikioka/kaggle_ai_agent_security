---
name: lb-submit
description: '実験(expNNN)を Kaggle のリーダーボード(LB)へ提出する。push → Claude in Chrome で Edit 画面から Submit → time_manager をバックグラウンド監視（1時間おき）→ docs/SCORE.md の lb_public / lb_time へ記録、までを一本で行う。日次上限5/日を消費する不可逆操作。トリガー: "LB提出", "リーダーボードに提出", "expNNNを提出", "LBへ出して", "/lb-submit"'
---

# lb-submit — LB 提出と採点結果の記録

`experiments/expNNN` を Kaggle のリーダーボード（LB）へ出し、採点完了まで見届けて
`docs/SCORE.md` に結果を書くまでを一本で行う。**提出（Submit）と記録（record）は同じ流れの
前半・後半**なので分けない。

## 大原則（過去の失敗から確定・厳守）

1. **LB 提出は日次上限 5/日・最終審査は 2 件選択の不可逆な外部アクション**。
   **このスキルの起動＝ユーザの明示指示**とみなし、以降は都度確認を取らずに Submit まで進める。
   ただし各 Submit の直前にスクリーンショットで**対象 exp 名 / Version / 残枠**を必ず目視し、
   **食い違ったら押さずに止めて報告する**。枠が足りないときも提出せず報告して止める。
2. **提出は Kaggle の Edit（ノートブック編集）画面の「Submit to competition」からのみ通る**
   （2026-07-22 exp021 で確定）。通らない2経路:
   - `competition_submit_code` API は **403 Forbidden**（叩いていた `scripts/ops/submit_lb.py` は撤去済み）。
   - ビューアの「Submit to Competition」ダイアログは
     「requires submission.csv and the selected Notebook Version does not output this file」で **Submit 無効**。

   理由: push（Save & Run All）した version は `submission.csv` を出力しない（`serve()` は競技リラン時のみ
   生成）ので、commit 済み version を事前チェックする上の2経路は弾かれる。Edit 画面の Submit だけが
   **新 version を保存＋実行して提出**するため、競技リランで `submission.csv` が生成されて通る。
3. **ブラウザ操作は Claude in Chrome（`mcp__claude-in-chrome__*`）**。ユーザのログイン済み Chrome を
   そのまま駆動できる。Playwright MCP は別プロファイルで Kaggle 未ログイン（Sign In 表示）なので
   Edit 画面に到達できない。※Kaggle の**閲覧・調査**は従来どおり Playwright（用途で使い分ける）。
4. **長時間待ちに背景 bash を使わない**（この環境では系統的に kill される）。push 完了待ちも採点待ちも
   **Monitor ツール**で張る。
5. **想定外のモーダル / JS ダイアログを踏まない**。出たら操作を止めて報告する。ブラウザ操作が
   2〜3 回失敗したら深追いせず、何を試して何が起きたかを添えて停止しユーザの判断を仰ぐ。

## kernel id / URL 体系

```
kernel id  : rikitomo0526/ai-agent-security-attack-script-<exp>
viewer     : https://www.kaggle.com/code/rikitomo0526/ai-agent-security-attack-script-<exp>
editor     : https://www.kaggle.com/code/rikitomo0526/ai-agent-security-attack-script-<exp>/edit
submissions: https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks/submissions
```

状態確認は full id を直接叩く（`make status EXP=<exp>` も同じ id を叩くので等価）:

```bash
uv run kaggle kernels status rikitomo0526/ai-agent-security-attack-script-<exp>
```

## 手順

### 0. 対象 exp と日次枠の確認

- 引数から対象を決める。`exp076` / `exp076,exp078` / `exp076-exp080`（範囲）を受ける。
  **省略時はユーザに確認する**（推測で提出しない）。
- 残枠を数える。今日（UTC）の提出件数を見て、`対象件数 > 残枠` なら**提出せず報告して止める**:

  ```bash
  uv run scripts/ops/check_submissions.py --max 10
  ```

### 1. push（デプロイ）— 同時 GPU 枠 2 を守って 2 件ずつ

`make submit` は build + `kaggle kernels push` のみで、**LB 枠は消費しない**。
**すでに push 済みで COMPLETE の exp はこの手順を飛ばす**（先に status を見る）。

```bash
make submit EXP=<expA>
sleep 8
make submit EXP=<expB>
```

### 2. push 完了（COMPLETE）を Monitor で待つ

quick run 自体は ~17–25s だがキュー待ちがある。終端状態（complete / error / cancel）を**全部**拾う
ポーリングを Monitor（`persistent: false`, `timeout_ms: 1800000`）で張り、揃ったら1行出して終了する:

```bash
while true; do
  done_all=1; line=""
  for e in <expA> <expB>; do
    s=$(uv run kaggle kernels status rikitomo0526/ai-agent-security-attack-script-$e 2>&1)
    st=$(echo "$s" | grep -oiE 'complete|error|cancel' | head -1)
    [ -z "$st" ] && done_all=0
    line="$line $e=${st:-running}"
  done
  [ $done_all -eq 1 ] && { echo "PUSH_DONE$line"; break; }
  sleep 20
done
```

`error` / `cancel` で終わった exp は**提出しない**。原因を報告して止める。

### 3. Claude in Chrome で提出（exp ごとに繰り返す）

必要なツールを **1 回の ToolSearch でまとめて**ロードする（1つずつ引かない）:

```
select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__find,mcp__claude-in-chrome__get_page_text
```

1. `tabs_context_mcp` で現状のタブを把握 → `tabs_create_mcp` で作業タブを1枚作る
   （**前セッションのタブ ID は再利用しない**）。
2. submissions ページへ `navigate` → `get_page_text` で **DAILY 残枠**を確認する。
3. **エディタ URL（`.../edit`）へ直接 `navigate`** する。ビューアの Edit ボタンのクリックは
   読み込み中に空振りしやすい（過去3セッションで再現）ので、直リンクを既定の経路にする。
   読み込みが済むと URL が `/edit/run/` になる。
4. 右パネル下部の **「Submit to competition」** を展開 → パネル内の **Submit** を押す。
   要素の特定は **`find`（ref ベース）を第一手**にする:
   `find {query: "Submit to competition section"}` → `computer left_click {ref: "..."}`。
   **座標クリックはウィンドウサイズ依存でセッション間に安定しない**（過去3回とも別座標）ので、
   `find` が効かないときの退避手段にとどめる。必要なら右パネルを `scroll` してから探す。
5. 提出ダイアログを `computer screenshot` で確認する。**対象 exp 名・`Version N`・
   "You have N submissions remaining today"** の3点が期待と一致していれば最終 **Submit** を押す。
   一致しなければ**押さずに停止**して報告する。
6. 受理を `computer screenshot` で確認する。証拠は3つ:
   右パネルの **DAILY SUBMISSIONS が n/5 に増加** / アクティビティに
   **「Competition submission … Scoring…」** / 新 Version が **Running（または Queued）**。
7. 次の exp へ。**提出 description は既定文のまま変えない**
   （`AI Agent Security - Attack script expNNN | Version 2`）。
   `script expNNN` の並びが `time_manager.py` の `EXP_RE` の一致キーなので、崩すと回収できなくなる。

### 4. 提出した事実を先に SCORE.md へ書く

受理を確認した時点で `docs/SCORE.md` の該当行を Edit する（行が無ければ追加。**7 列・`|` の整合を崩さない**）:

- `lb_public` = `-`、`lb_time` = `-`（スコアはまだ出ない）
- `changes` 列の末尾に `YYYY-MM-DD 提出（DAILY n/5）。判定=live LB。` を追記（既存行の記法に合わせる）
- **`local_*` 列は触らない**

### 5. 採点を time_manager でバックグラウンド監視（1時間おき）

改修済みの `time_manager.py` は **1 ポーリング＝改行付き 1 行**を出すので、Monitor に張ると
その 1 行がそのまま 1 通知になる。`persistent: true` で張る:

```
Monitor({
  description: "LB採点の進捗（1時間おき）",
  command: "uv run scripts/ops/time_manager.py --exps <spec> --interval 3600 2>&1",
  persistent: true,
})
```

届く行:

| 行 | 意味 |
|---|---|
| `[monitor] 監視開始: exp076,exp077 (2件) interval=3600s` | 監視開始 |
| `[status] exp076=PENDING(60min) …` | **1時間おきの定期確認** |
| `[done] exp076 COMPLETE public=88.155 private=- 952min` | 1件完了（`public=-` は **VOID**） |
| `[failed] exp077 ERROR 120min` | 採点エラー |
| `[all-done] 2件すべて終了` | 全件終了（Monitor もここで閉じる） |
| `[error] …` | API 取得失敗（非ゼロ終了） |

**採点はキュー込みで ~800〜1000 分（13〜16 時間）**かかる。セッションがそれより先に終わるのが普通なので、
**後日 `uv run scripts/ops/check_submissions.py --max 10` で回収して手順 6 をやり直す**運用を必ず併記して伝える。
`time_manager.py --exps <spec>` を後日そのまま回してもよい（起動時点で完了済みの提出は
`[done] …（後追い・上限目安）` として即報告される）。

### 6. 採点結果を SCORE.md へ記録

`[done]` 行（または `check_submissions.py` の出力）を元に `docs/SCORE.md` を Edit する:

- `lb_public` に **小数3桁**（例 `88.155`）、`lb_time` に **`952分`** を記入。
- `changes` 列の末尾に結果コメントを追記（既存の記法: `**結果 LB88.155 で完走（非VOID）…**`）。
- **`local_*` 列は触らない**。列数・`|` の整合を保つ。
- **COMPLETE なのに public が空欄（`public=-`）＝ VOID（live 競技リランの時間切れ・9000秒/フェーズ超過）**。
  フォーマットバグでも attack.py バグでもない（ユーザ確定事項）。`lb_public` は `空欄(VOID)` と書き、
  `changes` にその旨を追記する。
- まだ PENDING の exp は `-` のまま残し、経過分と目安（~800〜1000 分）を報告する。

### 7. 報告

- どの exp をどの枠（DAILY n/5）で提出したかを列挙する。
- SCORE.md をどう書き換えたか（before → 記入値）を簡潔に伝える。
- 未完了が残るなら、経過分・完了目安・後日の回収コマンドを示す。

## 落とし穴

- `competition_submit_code` API は **403**。これを叩く `make submit-lb` / `scripts/ops/submit_lb.py` は
  撤去済みで、**API 経由の提出経路は存在しない**。作り直しても通らない。
- ビューアの「Submit to Competition」は `submission.csv` 未出力で**ボタンが無効**。必ず Edit 画面から。
- ビューアの Edit ボタンは読み込み中のクリックが空振りする → **`/edit` 直リンク**を使う。
- **座標クリックはセッションをまたいで再利用できない** → `find` の ref を優先。
- 提出 Notebook には **`serve()` セルが必須**（無いと「submission.csv が必要」で弾かれる）。
  `scripts/ops/build_notebook.py` が入れているが、Edit 画面で目に入るなら確認しておく。
- 提出 description の **`script expNNN` を変えない**（回収の一致キー）。
- `lb_time` は「提出 → COMPLETE **検知**までの経過分」。後追い回収は検知遅れ分だけ上振れするので
  **上限目安**として扱う（`~952分` のような書き方でよい）。
- **同時 GPU 枠 = 2**。push は 2 本ずつ。連続 push は枠飽和 → kernel id 破損の連鎖を招く。

## 参照

- `AGENTS.md`「LB 提出までの流れ」（要約とポインタ。手順の正典は本スキル）
- `scripts/ops/time_manager.py`（採点監視）/ `check_submissions.py`（1回きりのスナップショット）/
  `submit.py`（build + push）
- `docs/SCORE.md`（スコアの単一ソース。スクリプトでは書かず Edit で反映する）
- `docs/knowledges/02-実測台帳.md`（VOID = 時間切れ・live 予算の考え方・cap 別の全実測）
