# exp078 — v15 移植の cap 0.98→0.99（exp077 の単一レバー・完走 reach）

exp077（v15 忠実移植・cap 0.98）から `REPLAY_SAFE_FRAC` のみ 0.99 に上げた完走 reach 枠。JED エンジンの N_eff を +~1%。cap 0.99 は champion 系で完走実証済み。v15 verbose-forge slow-row の1候補コストが重い場合の保険として 0.98(exp077) を床に併走。

## バッテリ全体（Round14・exp076-080）
| exp | エンジン | cap | probe | 役割 |
|---|---|---|---|---|
| exp076 | champion 3-arm race | 0.995 | 4 | exp028 byte（歴代最高90.99）— 上端ギャンブル（「最高スコアの提出」） |
| exp077 | v15 JED（replay-safe × split × verbose-forge） | 0.98 | — | foysalemonshanto v15 忠実移植 — 新 selector・完走床 |
| exp078 | v15 JED | 0.99 | — | exp077 の cap +1段（単一レバー）— 新エンジン完走 reach |
| exp079 | champion 3-arm race | 0.99 | 2 | exp062 構成（LB89.370・完走実証best）— 完走コア |
| exp080 | champion 3-arm race | 0.993 | 2 | 0.99↔0.995 中間 reach（~90狙い・VOID確率↓） |

## 方針
確定レバーは best-of のみ（同一コードでも GPU draw で ±1.4〜4 分散）。本ラウンドは (a) 公開 v15 を独立エンジンとして取り込み（077/078）、(b) 最高実績 exp028 を cap リスク曲線に散らす（076/079/080）両建て。cap 0.98-0.99 は完走圏、0.995 は VOID 境界（上端ギャンブル）。

## 判定
local(gemma N=300) は fill 系 27 天井で LB 非予測。手元検証は fire率・無クラッシュ・private=0 のみ。LB は live 提出で確定。
