# exp024 — deadline-aware probe fill の天井押し上げ（SAFETY 0.30→0.50）

exp020（probe fill, SAFETY=0.30）の**唯一の変更版**。SAFETY 定数だけを 0.30→0.50 に
上げ、probe・候補生成・フォールバック・その他定数（N_MAX=2000 含む）は完全に同一。

## 背景（exp020 の実測）

exp020 は大成功: **ローカル N_safe=1375・provenance 40.62・fire 率 98.5%・exp010 比 4.65 倍**。
SAFETY=0.30 は各 replay の予算（live 9000 / ローカル 8000）の 30% しか使わず保守的だった。

## 狙い

SAFETY↑で fill の天井を押し上げる。`N_safe = floor(budget × SAFETY / t_cand)` なので
0.30→0.50 で N_safe が約 1.67 倍に増える。

- ローカルは gemma が速い（t_cand≈1.75s）ため N_safe ≈ 0.50×8000/1.75 ≈ 2285
  → **N_MAX=2000 にクランプ**。
- provenance の天井 ≈ 2000 × 0.985 × 6 / 200 ≈ **59** を確認し、fire 率と N 線形が
  N~2000 でも保たれるかを検証する。
- ローカル replay wall-clock ≈ 3 × 0.50 × 8000 = 12000s ≈ 3.3h（Kaggle T4 枠内）。

N_MAX=2000 は SDK の `MAX_REPLAY_FINDINGS=2000` 上限なので据え置き（これ以上は無意味）。

## 提出安全性のトレードオフ（重要）

**SAFETY=0.50 は live で各 replay を予算の 50% まで使うため、INVALID_SUBMISSION への
余裕が 0.30 より減る。** replay 総時間 ≈ N_safe × t_cand × ガードレール数 が 9000s/モデル/
フェーズを超えると submission 全体が丸ごと失格（grace 5s のみ）。

- ローカル指標（provenance）の最大化には SAFETY=0.50 が有効。
- **本番提出は SAFETY=0.30〜0.40 が安全**という判断材料として本 exp を使う。
  0.50 はあくまで「N~2000 での天井」と「fire 率・N 線形の維持」を測る探索用。

## モック自己検証（実施済み・全通過）

`scratchpad/test_exp024.py`:
- SAFETY=0.50 を確認、その他定数（N_MIN=300 / N_MAX=2000 / FALLBACK_N=340）は exp020 と同一
- t_cand=1.75s（gemma 相当）→ floor(2285) → **N_MAX=2000 クランプ**
- t_cand=4.0s → N_safe=1000（SAFETY0.30 の 600 から増加）
- t_cand=20s → N_MIN=300 クランプ
- t_cand 範囲外（<0.05 / >600）・None → FALLBACK_N=340 維持
- run() 全分岐: fast→N_MAX / fail・none・env=None→340
- 全候補が単一メッセージ・宛先一意・禁止語0・probe 宛先の非漏洩を確認

## 比較対象

| exp | SAFETY | ローカル N_safe | provenance | fire率 | 備考 |
|---|---|---|---|---|---|
| exp010 | （固定 N=300） | 300 | 8.73 | 97.0% | 文面ベースライン |
| exp020 | 0.30 | 1375 | 40.62 | 98.5% | fill 初実証（4.65倍） |
| **exp024** | **0.50** | **（eval 待ち, 想定 2000 クランプ）** | **（eval 待ち, 天井 ≈59 想定）** | **（eval 待ち）** | 本 exp |

### 評価結果（make eval 後に追記）

- ローカル probe t_cand = （記入）
- ローカル算出 N_safe = （記入, N_MAX=2000 に張り付くか）
- provenance score / raw / findings = （記入）
- fire 率が N~2000 でも 98.5% 近辺を保つか = （記入）
- exp020(40.62, N=1375) との比較 = （記入）

## 次にやること

- オーケストレータが `make eval EXP=exp024` を実行 → 上表を埋める。
- N~2000 で fire 率・N 線形が崩れなければ、provenance 天井が ~59 と確認できる。
- 提出用には SAFETY=0.30〜0.40 を採用（本 exp は天井測定用）。SAFETY=0.40 の中間点も
  必要なら別 exp で。
