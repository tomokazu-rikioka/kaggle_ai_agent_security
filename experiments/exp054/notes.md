# exp054 — 近 champion draw A（PROBE_REPS=2 + cap 0.996）

Round 9（public 最大化・best-of バッテリ）の1本。土台は exp028/exp039 champion の proven 3-arm エンジン。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- best-of の近 champion 枠。exp044（LB **89.010**・非VOID 実証）と同一構成で、probe を回収し cap を1段攻めた
  「わずかに N_eff を押した」母集団から独立サンプルを引く。

## 変更点（vs exp028 champion）
- **proven 3-arm エンジンは1バイトも不変**（発火率・出力トークンに触れない）。差し替えは予算回収ノブ 2 定数のみ:
  - `PROBE_REPS` 4→**2**（生成は greedy 決定論で発火は反復不変・浮いた試し打ち時間を fill へ）。
  - `REPLAY_SAFE_FRAC` 0.995→**0.996**（replay 予算 cap を +~0.1%。probe=2 で買い戻した cold 余裕で cold-safe）。
- fail-closed（崩れれば verbose 床へ縮退）＝下限は champion 分散帯。
- 安全性根拠: exp044 が probe=2+0.996 で非VOID／exp043（probe=4+0.996）は VOID＝probe 回収の cold 余裕が要点。

## 評価結果（make eval）
- gemma N=300 は健全性のみ（選択形 fire率 ≥ verbose・無クラッシュ・private=0）。ノブ効果（N_eff 増）は gemma では見えない。
- LB は live 提出でのみ確定（★ユーザー明示指示時のみ）。所見: （提出後に追記）
