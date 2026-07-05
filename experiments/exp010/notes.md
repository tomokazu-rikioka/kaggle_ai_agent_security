# exp010 — real-secret EXFIL × hardened deadline-fill（strict 特化・提出用）

## 狙い（仮説）
- real-secret EXFIL（fs.read→http.post 2 連鎖, 固定 N=300 での実測は strict=27.0）に
  exp011/exp012 と同型の hardened deadline-fill を装備した提出候補（strict トラック）。
- real-secret fill・旧 SAFETY 版で eval 放棄・scores.json 汚染となっていた既存の検証の hardened 版。
- strict 限定（strict は fs.read 無検査 allow + 秘密判定が SECRET_MARKER センチネル限定という穴で
  本物の秘密値を素通し）。public/prov は fs.read の path="secret.txt" が deny され 0。

## 変更点（attack.py）
- exp012 の fill 機構（`_probe_chain`→N_safe 自己較正→締切ガード生成）から **K 適応を外した固定
  2 連鎖版**として実装。文面（`_CHAIN_TEMPLATES`）は固定 N=300 版を無改造で移植。
- `MSGS_PER_CAND=2`（2 メッセージ分 t_cand で N_safe が約半分に自動較正）。締切前に必ず return。

## ローカル検証（実装後）
- `env=None`: フォールバック N=50（`_fallback_n(2, 9000)`）、2 msg/候補、max_chars=113、全ユニーク。**PASS**
- モック env: budget=9000→N=2000(N_MAX clamp)、budget=30→N=478（**自己較正で縮む**）。**PASS**
- ruff: All checks passed。`make build EXP=exp010`: submission.ipynb 生成 OK（自己完結・兄弟 import 無し）。
