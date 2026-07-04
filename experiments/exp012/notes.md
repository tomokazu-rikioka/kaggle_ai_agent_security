# exp012 — exp006(DEPUTY全振り) + exp008(実secret EXFIL)の小さいヘッジ・ブレンド

exp006（N=300 全 DEPUTY, score=8.61 が public/strict/provenance で完全一致、フル実測済み）
と exp008（fs.read→http.post の実 secret EXFIL 連鎖, strict score=27.0・
public/provenance=0、フル実測済み）を **90% DEPUTY / 10% EXFIL-real-secret** で
ブレンドしたポートフォリオを検証する。

## ブレンド比率の根拠

`jed_attack_gateway.py`（実評価ゲートウェイ本体）冒頭の docstring:
```
Guardrail Split:
- Public leaderboard: evaluated against OptimalGuardrail (default)
- Private leaderboard: evaluated against the private guardrail loaded
  via the 'aicomp_sdk.attack_guardrails' entry point group, specified
  by AICOMP_ATTACK_GUARDRAIL_ID env var.
```
かつ既知の唯一のフォールバック ID は `persistent_provenance_private`
（`aicomp_private_guardrails.persistent_provenance.Guardrail`）。**非公開最終評価は
local `provenance` に近いとほぼ確定的**（[[ai-agent-security-competition]] メモリ参照）。

exp008 の EXFIL-real-secret は provenance では 0（fs.read 自体が ultra-dangerous パス
検査で deny）。大きく配分すると非公開評価への寄与なく provenance を犠牲にするだけの
リスクが高いため、**保険として小さい割合（10%）だけ**残す設計とした。

## 期待値（fire rate は exp006=95.7%, exp008=100% の実測値を使用）

n_exfil=30, n_deputy=270（実際は重複排除で若干前後する可能性あり）:

| guardrail | raw 内訳 | 期待 raw | 期待 score |
|---|---|---|---|
| public | 270×0.957×6 | ≈1550 | ≈7.75 |
| strict | 270×0.957×6 + 30×1.0×18 | ≈2090 | ≈10.45 |
| provenance | 270×0.957×6（EXFIL分は0） | ≈1550 | ≈7.75 |

exp006（8.61 全GR共通）と比較すると、provenance は約1割減（8.61→7.75）、strict は
約21%増（8.61→10.45）。**provenance を主目標とする限り exp006 単体の方が有利**だが、
「provenance近似が完璧でない」という残存不確実性への保険として少額ヘッジする。

## 実装（`attack.py`）

- DEPUTY: exp006 と完全に同一の12テンプレート・宛先生成。
- EXFIL-real-secret: exp008 と完全に同一の6テンプレート・2メッセージ連鎖・URL生成。
- `EXFIL_REAL_SECRET_FRACTION = 0.10` で配分比率を一元管理。

## ローカル検証

（run() をローカル実行して候補数・重複・チェーン長・禁止語を確認）

## 評価結果

### smoke（N=30, 候補切り詰めの罠に注意）

`run()` は EXFIL-real-secret を先頭 30 件（=n_exfil）生成してから DEPUTY を続けるため、
`--candidates 30` がちょうど EXFIL ブロックのみを切り取ってしまい、**DEPUTY 部分は
未検証**（exp004 と同じ落とし穴）。strict 30/30=100%発火（raw=540, score=2.7）で
EXFIL-real-secret 単体の再現性は確認できたが、ブレンド全体の smoke 検証にはならず。
DEPUTY・EXFIL 双方とも exp006/exp008/exp010 で個別にフル実測済みのため、追加の smoke は
省略しフル N=300 評価に直接進む。

## 評価結果（make eval EXP=exp012 MODELS=gemma_4, N=300 フル実行）

**理論値とほぼ完全一致**:

| guardrail | score | raw | findings | predicates |
|---|---|---|---|---|
| public | 7.74 | 1548 | 258/270(DEPUTY分) | CONFUSED_DEPUTY 258 |
| strict | 10.44 | 2088 | 288/300 | EXFILTRATION 30 + CONFUSED_DEPUTY 258 |
| provenance | 7.74 | 1548 | 258/270(DEPUTY分) | CONFUSED_DEPUTY 258 |

- DEPUTY 部分の fire rate 258/270=95.6%（exp006単体の95.7%とほぼ一致）。
- EXFIL 部分は 30/30=100%（exp008と同じ）。
- raw=2088=258×6+30×18 と完全一致。設計通りの挙動を確認。
- exp006単体(8.61)と比較すると public/provenance は約10%減（7.74）、strict は
  約21%増（10.44）。理論値（≈7.75/≈10.45）とほぼ完全に一致。

## 結論

ブレンド設計は狙い通り機能した。ただし exp010（疑問形DEPUTY）の方が exp006（命令形）
より fire rate が高いため、exp013（exp010ベースのブレンド）の方が優れる見込み。
最終的な採用判断は exp013 の結果を待って行う。

## 次にやること

- 実測が期待値（public/provenance≈7.75, strict≈10.45）と一致するか確認。
- provenance を犠牲にしてでも strict ヘッジを厚くする価値があるかは、コンペ終盤まで
  「非公開評価がprovenance寄り」という前提の確度次第。現時点では10%が妥当な保険料と判断。
