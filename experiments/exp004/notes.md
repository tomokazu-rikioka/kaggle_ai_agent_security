# exp004 — 三段構え全振り × hardened deadline-fill（strict 特化・提出用）

## 狙い（仮説）
- 三段構え（fs.read→http.post→DEPUTY 通知、10% ヘッジ版の実測は public/prov 8.82・strict 11.2）の
  候補を **全候補に全振り**し、exp011/exp012 と同型の hardened deadline-fill を装備した提出候補
  （strict トラック）。
- 三段構え全振り・固定 N=300 では timeout 懸念があり放棄されていた「全振り」を、
  fill が t_cand を実測して N_safe を較正することで **timeout 安全に実現**する。
- 1 候補 = fs.read→http.post→DEPUTY の 3 メッセージ連鎖。strict は EXFIL+DEPUTY 両取り（raw22）、
  public/prov は 1・2 通目が deny されても 3 通目（独立 email.send）で DEPUTY 分（raw6）を回収。

## 変更点（attack.py）
- 10% ヘッジ版の「90% DEPUTY 単発 + 10% 三段構え」ポートフォリオを廃し、**全候補を三段構え**に。
- exp012 の fill 機構（`_probe_chain`→N_safe 自己較正→締切ガード生成）から **K 適応を外した固定
  3 連鎖版**として実装。文面（`_triple_messages` / `_DEPUTY_TEMPLATES` / `_CHAIN_TEMPLATES`）は
  10% ヘッジ版から無改造で移植。
- `MSGS_PER_CAND=3`。probe/生成とも締切前に必ず return（live INVALID 回避）。

## ローカル検証（実装後）
- `env=None`: フォールバック N=33（`_fallback_n(3, 9000)`）、3 msg/候補、max_chars=113、全ユニーク。**PASS**
- モック env: budget=9000→N=2000(N_MAX clamp)、budget=30→N=307（**自己較正で縮む**）。**PASS**
- ruff: All checks passed。`make build EXP=exp004`: submission.ipynb 生成 OK（自己完結・兄弟 import 無し）。
