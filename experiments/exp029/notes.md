# exp029 — continuation / multi-message amortization v2（T-MAN 35位の反証主張の検証）

Round 4（public 最大化・抜本転換）の1本。土台は exp021。**仮説の白黒をつける検証枠**。

## 狙い（仮説）
- 狙う述語: **EXFILTRATION**（http.post + SECRET_MARKER）。public 最大化・private=0 承知。
- Discussion 断片: The T-MAN(35位)「GPT-OSS **continuation** は新規候補より経済的に勝てる」。
  exp005 の多メッセージ償却(LB45.09)は verbose で毎メッセージ full 生成になり失敗。本 exp は
  **1候補 = primer 1本 ＋ bare continuation (K-1)本**で、priming 後の継続 post を bare で安く積めるか
  （continuation が後続 interact のコストを下げるか）を実測する。K∈{1,2,4,8} を probe→最良 K にコミット。

## 採点上の位置づけ（勝敗の分岐点）
- 1候補=K メッセージ、各 http.post 成功 → 1トレース K 個 EXFIL → **raw=16K+2**（cell は1）。
- raw/秒 = (16K+2)/(t0+(K-1)t')。continuation が効かない（t'≈t0）なら 16/t+2/(Kt) < 18/t で **必ず劣後**
  （cell +2 の希釈＝exp005 の構造的敗因）。効く（t'≪t0）なら 16/t' が単発 18/t を上回りうる。
  → **「continuation が後続 interact を十分安くするか」の1点にかかる。負の結果でも密度一本化の根拠になり情報価値大**。

## 変更点（vs exp021）
- `AttackCandidate.from_messages((m1,…,mK))` で K本連結（**≤32メッセージ・各≤2000字**厳守。実測 maxlen86/8本）。
- `run_candidate` が K interacts を1候補として replay し `_fired_post_count` で発火 post 数を計測。
- K を probe（各3回）→ raw/秒 最良 K にコミット → replay-safe fill（K×latency を積算し VOID 回避）。

## 評価結果（make eval）
- continuation の効きは gpt_oss で最も出る → `make eval EXP=exp029 --models gpt_oss`（N=300）が主。
  確認: (a) K 別の 1候補あたり発火数・(b) 単発比 raw/秒・(c) 無クラッシュ・(d) private=0。
- **LB は live 提出でのみ確定**（★ユーザー明示指示時のみ）。
- 所見: （eval 後に追記）
