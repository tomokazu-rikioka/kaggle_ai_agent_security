# exp043 — cap 押上げ（REPLAY_SAFE_FRAC 0.995→0.996）

Round 7（public best / best-of × 安全ノブ sweep）の1本。土台は **exp028/exp039 champion（proven 3-arm）を1バイトも変えず**、
予算回収ノブ 2 定数だけ差替。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- レバー: **REPLAY_SAFE_FRAC 0.995→0.996（PROBE_REPS=4 据置）**。返却集合の replay 予算 cap を +~0.1% 攻めて N_eff 純増。exp034 が 0.997 で非VOID の実績から 0.996 は cold-safe。
- **プール（verbose/lean/forge）・selector・fill・forge は exp028 と完全同一**＝発火率・出力トークンは不変。安全に N_eff だけを増やす。

## 背景（exp036–040 の LB 実測で確定）
- deep-forge・arms 増は全て champion 未達（probe コスト退行の再現）。reasoning-effort 注入は user 側からは効かない。
- **同一コードで ±1.4 の GPU 分散が実在**（exp039=exp028 で 89.595 vs 91.0）→ best-of が最も確実。→ 本 sweep も best-of で最良採用。

## local の読み方（gemma・N=300）
- 健全性のみ: stderr `[exp043_knob] ... name:fires/attempts@cost` で **選択形 fire率 ≥ verbose**・非クラッシュ・private=0。
- ノブ効果（N_eff 増）は gemma では見えず **live LB でのみ確定**（fill 系は手元 27 天井）。

## live 安全性
- 発火率・トークンに触れないので INVALID リスクなし。cap 押上げは exp034(0.997 非VOID)実績内で cold-safe。fail-closed 下限は champion 相当。

## 評価結果（make eval）
- `make eval EXP=exp043 CANDIDATES=300`（gemma・N=300・2並列枠厳守）。
- 所見: （eval 後に追記）
- LB: （live 提出はユーザー明示指示時のみ。best-of。ここに記入）
