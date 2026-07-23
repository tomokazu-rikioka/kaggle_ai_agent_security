---
name: eval-batch
description: 複数の実験(expNNN)をまとめて Kaggle GPU の eval パイプラインに流す。gemma のみ・N=300 既定・同時GPU枠=2 をラウンド分割で厳守し、背景bashに頼らず「push(--no-wait)→Monitorで完了待ち→fetch+merge」で scores.json を回収する。トリガー: "evalパイプラインを回して", "expNNN〜MMMをeval", "まとめてeval", "バッチeval", "/eval-batch"
---

# eval-batch — 複数 exp をまとめて eval に流す

`experiments/expNNN/attack.py` を Kaggle GPU 上で実モデル採点し `scores.json` を回収する一連の運用を、
**複数 exp のバッチ**として安全に回すためのスキル。1本の `make eval` の中身は `docs`/CLAUDE.md 参照。
ここでは「複数本を GPU 枠を守って捌く」オーケストレーションに専念する。

## 大原則（過去の失敗から確定・厳守）

1. **gemma のみ・N を意識する**。eval は `--models gemma_4` で回す（gpt_oss は遅く律速。手法比較は gemma で揃える）。
   候補数(N)は**必ず意識して選ぶ**（既定任せにしない）:
   - **手法比較 exp（固定 N 前提）**は `--candidates 300`（N=300）で揃える。**N を無断で上げると手法比較が無効化**する（CLAUDE.md 教訓の中核）。
   - **fill 系 exp（canqiang/exp006 派生など・in-file cap 無し）**は既定(`--candidates` 無し)だと **fill が `MAX_REPLAY_FINDINGS=2000` まで詰まり local が跳ねる**（例: exp021 gemma で public=180.0/findings=2000）。
     これは health としては有効（全数発火＝OK）だが、**SCORE.md 他行の N=300 基準（~27.0）とは非互換**。表を揃えるなら `--candidates 300`（→~27.0）。
   - **重要**: `--candidates` は eval_driver で**生成後の事後 truncate**（`generate_candidates` は env に cap を渡さず run() は `budget_s` で自走 → `[:MAX_REPLAY_FINDINGS]` → `[:candidates]`）。
     よって **`--candidates 300` にしても生成時間は縮まない**（詰め切ってから 300 に切るだけ）。速く health だけ見たいなら `--budget-s` を下げる（結果は非基準）。
   - ユーザが別の制約（モデル・N）を指定していればそれを最優先。**どの N で回すかは記録の意味に直結するので、fill 系では特に明示的に決める**。
2. **同時 GPU 枠 = 2**。3本以上を同時に push しない。対象 exp を**2件ずつのラウンド**に割る。
   テスト/提出カーネルの実行も枠を数える。
3. **背景 bash は系統的に kill される**。`make eval`（wait 付き）を背景で回し続けるのは不可。
   代わりに **`run_eval.py --no-wait`（push のみ）→ Monitor で完了待ち → 手動 fetch+merge** で回収する。
4. **連続 push を避ける**（枠飽和 → kernel id が "Notebook not found" 恒久破損の連鎖）。push の間に数秒あける。
5. **提出(LB)はこのスキルの範囲外**。`make eval` / push は自由。LB 提出はユーザ明示指示時のみ（別運用）。

## kernel id 体系

gemma eval の kernel id は決め打ちで導出できる（`build_eval_notebook._write_kernel_metadata`）:

```
rikitomo0526/ai-agent-security-eval-script-<exp>-gemma-4
```

例: `exp021` → `rikitomo0526/ai-agent-security-eval-script-exp021-gemma-4`。
状態確認は必ずこの full id を直接使う（`make status` の slug は別体系なので使わない）。

## 手順

### 0. 対象 exp と枠の確認
- 対象 exp を確定（例: `exp021 exp022 exp023 exp024 exp025`）。**2件ずつのラウンド**に割る。
- 走行中カーネルが無いか確認して空き枠を把握:
  ```bash
  uv run kaggle kernels list --mine -s "ai-agent-security-eval" | head -20
  ```
  直近 `lastRunTime` が過去でも RUNNING とは限らない。疑わしければ対象 id を個別に status 確認。

### 1. ラウンドを push（2件・--no-wait）
1ラウンド＝2件。各 exp を `--no-wait`（build+push のみ、ポーリングしない）で出す。push 間に数秒あける:

```bash
uv run python scripts/ops/run_eval.py <expA> --models gemma_4 --no-wait
sleep 8
uv run python scripts/ops/run_eval.py <expB> --models gemma_4 --no-wait
```

push 直後に両方が RUNNING になったか確認:

```bash
for e in <expA> <expB>; do
  uv run kaggle kernels status rikitomo0526/ai-agent-security-eval-script-$e-gemma-4 | tail -1
done
```

### 2. 完了を Monitor で待つ（背景bashは使わない）
両カーネルが終端状態（complete/error/cancel）になるまで静かにポーリングし、**揃ったら1行だけ出して終了**する
Monitor を張る（`persistent: true`, `timeout_ms: 3600000`）。fill 系 eval は数時間かかり得る。
完了時に1回だけ通知が来て自分が再起動される。`error`/`cancel` も拾うので「沈黙＝成功」の取りこぼしは無い:

```bash
d_A=0; d_B=0
while true; do
  sA=$(uv run kaggle kernels status rikitomo0526/ai-agent-security-eval-script-<expA>-gemma-4 2>&1)
  sB=$(uv run kaggle kernels status rikitomo0526/ai-agent-security-eval-script-<expB>-gemma-4 2>&1)
  echo "$sA" | grep -qiE "complete|error|cancel" && d_A=1
  echo "$sB" | grep -qiE "complete|error|cancel" && d_B=1
  if [ $d_A -eq 1 ] && [ $d_B -eq 1 ]; then
    echo "ROUND_DONE <expA>=$(echo "$sA"|grep -oiE 'complete|error|cancel'|head -1) <expB>=$(echo "$sB"|grep -oiE 'complete|error|cancel'|head -1)"
    break
  fi
  sleep 120
done
```

### 3. fetch + merge（scores.json 回収）
complete になった exp について scores を回収し `experiments/<exp>/scores.json` にマージする。
**`kaggle kernels output` は `--force` 欠落で古い scores.json を読む既知の罠**があるので、先に
`build/eval/<exp>/gemma_4/output/` を消してから取得する（`run_eval` のテスト済みヘルパを再利用）:

```bash
EXP=<exp> uv run python - <<'PY'
import sys, json, pathlib, shutil, os
sys.path.insert(0, "scripts/ops")
from run_eval import _fetch_scores, _merge_and_save
exp = os.environ["EXP"]; model = "gemma_4"
out_dir = pathlib.Path(f"build/eval/{exp}/{model}")
kid = json.loads((out_dir/"kernel-metadata.json").read_text())["id"]
out = out_dir/"output"
if out.exists():
    shutil.rmtree(out)          # 古い scores.json を掴まないよう毎回まっさらに
scores = _fetch_scores(kid, out_dir)
assert scores is not None, f"{exp}: scores.json を回収できず（error/未完了?）"
_merge_and_save(exp, {model: scores})
g = scores.get("guardrails", {})
for name, v in g.items():
    print(f"{exp} {name}: score={v['score']:.3f} raw={v['score_raw']:.1f} findings={v['findings_count']} cells={v['unique_cells']}")
PY
```

`error`/`cancel` で終わった exp は scores が取れない → 原因を kernel ログで確認（下の落とし穴参照）。

### 4. health 判定
- **発火している**（findings_count > 0、EXFIL 等が立つ）・**非INVALID**・**クラッシュ無し**を確認する。これが health の本体。
- fill 系の local 値は**回した N しだい**: `--candidates 300` なら ~27.0、uncapped なら fill が 2000 まで詰まり **public~180.0（findings=2000）**。
  どちらでも「発火・非INVALID」は確認できるが、**local 絶対値はランキング信号にならない**（公開LB優劣は LB 提出でのみ判定）。
  → **SCORE.md の local 数値列は N 基準を揃えて記録する**（他行が N=300 の 27.0 なら 180 を混ぜない。揃えられない/uncapped なら数値列は保留し、changes 列に「uncapped n=2000: pub 180/全発火」等と注記して非INVALID を残す）。
- `public` で出て `private` で消える攻撃は overfit の疑い（http.post EXFIL は private で発火不能＝仕様。fill 系 EXFIL は private=0 が想定通り）。

### 5. 次ラウンドへ
残りの exp があれば **1〜4 を次の2件で繰り返す**（枠が空いてから push）。全ラウンド完了で回収終了。

### 6. 記録
- 各 exp について `/update-score <exp>` で `docs/SCORE.md` の local 列を反映。
- 必要に応じ `experiments/<exp>/notes.md` の「結果」と `docs/analysis/` に所要時間・発火数・逆算 raw を追記。

## 落とし穴（詰まったら CLAUDE.md「Kaggle eval 運用の落とし穴」）

- **枠オーバーで壊れた kernel id は "Notebook not found" が恒久化**（同 id 再 push で回復しない）。
  → `EVAL_ID_SUFFIX=-r2` 等を付けて**新 id に切替**（id・title 両方に付く。title を揃えないと 409 Conflict）:
  `EVAL_ID_SUFFIX=-r2 uv run python scripts/ops/run_eval.py <exp> --models gemma_4 --no-wait`
- **CLI キャンセルは走行中 GPU を殺さないことがある**。status API は最新版を返すので裏で走る旧版が見えない。
  確実な枠解放は **Kaggle UI の Stop Session**。
- **`_fetch_scores` は `--force` 無し**。同一出力先で smoke→本番を続けると古い scores を読む。
  → 手順3のとおり fetch 前に `output/` を消す（out先を分けるのでも可）。
- **error 終了の切り分け**: 競技データの一時未マウント（`aicomp_sdk 未検出`）は再 push で直ることが多い。
  ログは `uv run kaggle kernels output <id> -p <dir>` の後 `<dir>/*.log` か Kaggle UI で確認。
  `run_eval` の wait 経路は error を最大2回まで自動再 push するが、`--no-wait` 運用では手動で再 push する。

## 参照
- 実装: `scripts/ops/run_eval.py`（build→push→wait→fetch→merge）/ `scripts/ops/build_eval_notebook.py`（id 体系）。
- 単発の詳細・採点構造: CLAUDE.md / `docs/analysis/`。実験制約でユーザ指示があればそれを最優先。
