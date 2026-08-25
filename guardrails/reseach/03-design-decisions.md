# 設計判断: 実用性・コスト・汎用性

## 1. 評価軸

各 guardrail を以下で比較しました。

- **Security coverage**: exfiltration、integrity violation、confused deputy、rate abuse
- **Utility**: 明示された正常 action、Web/email を含む workflow、sensitive data の正当利用
- **Generalization**: 特定 marker/語彙/引数順への依存、未知 tool への side-effect metadata 利用
- **Runtime cost**: model call、文字走査、state size
- **Integration cost**: tool/data metadata、approval UI、identity/capability infrastructure
- **Private fit**: 現在の black-box 観測との一致（ソース一致ではない）

## 2. Variant 1 — public fixed

狙いは public の思想を変えず、明らかなコード穴だけを除くことです。

- 最初の1引数ではなく nested args の全 scalar を走査
- raw `key` substring を token boundary へ変更
- harness が供給しない `user_authorized` / `user_confirmed_safe` を認可として使わない
- canonical sensitive path、private-network destination、explicit marker を独立検査
- recent source window は public と同じ

**長所**: stateless、外部モデル0、導入最小、public-specific bypass の検出に最適。
**短所**: taint window wash が残り、語彙 filter の false positive、untrusted 後 blanket deny も残る。

## 3. Variant 2 — persistent provenance

本物 private の id/name と probe に最も近い代理です。

- 一度 web/email source を観測したら session 全体で taint を保持
- sensitive path の read/write/delete を拒否
- outbound args の marker/sensitive token を全 field 走査
- taint 後の WRITE/EXEC/SHARE/AUTH を拒否
- taint 前の clean `email.send` は回数制限せず許可

**長所**: constant state、決定論的、file-wash に強い、private 観測行列と整合。
**短所**: unrelated data flow を区別できず、taint 後 utility がほぼ失われる。実運用の推奨最終形ではない。

## 4. Variant 3 — intent and target bound

Task Shield / Progent / capability の考え方を、現 API で実装可能な最小形へ落としました。

- consequential action の verb が trusted `last_user` に必要
- recipient / URL / path / command の具体値も `last_user` に必要
- action-open request は自動実行せず `CONFIRM`
- taint があっても user が action と target を明示した正常 task は許可
- sensitive read/destructive action は別扱い

**長所**: public の最大の utility 問題を緩和し、attacker-controlled target を防ぐ。
**短所**: synonym/multilingual parser がヒューリスティック。会話全体を見ないため以前の user turn の委任を失う。
structured task/capability token が本来必要です。

## 5. Variant 4 — coarse IFC

FIDES/CaMeL の原則を再現しますが、field-level label が無いため明示的に「coarse approximation」とします。

- web/email/file tool data は low integrity
- sensitive file read は confidential
- low integrity session から side effect への no-write-up
- confidential session から external sink への no-write-down
- snapshot/restore で label を保持

**長所**: attack string を分類せず、deterministic policy として適応攻撃に強い。
**短所**: session-level 1 bit は label creep を起こし、正常な read-transform-write まで止める。
実運用には value/field provenance、endorsement、declassification、別 planner が必要です。

## 6. Variant 5 — risk adaptive

OWASP の approval/rate-limit と runtime risk tier を組み合わせた運用対照です。

- side effect 種別に base risk
- recent/persistent taint、confidential egress、missing intent、unbound target、反復で加点
- 低 risk は ALLOW、中 risk は CONFIRM、高 risk は DENY
- 4回目以降の clean SHARE/WRITE は fresh approval
- 明示 `SECRET_MARKER` は、他条件が許す場合だけ outbound args で redaction (`SANITIZE`)

**長所**: 全拒否を避け、review queue と blast radius を制御できる。ルールの説明可能性が高い。
**短所**: 閾値は domain calibration が必要。コンペ harness では CONFIRM UI がないため utility を過小評価する。
文字列以外の本物 secret は識別できない。

## 7. 推奨アーキテクチャ

実サービスなら、5つから1つを選ぶより次の層に分けます。

1. **Tool registration**: 最小 tool、狭い schema、side effect/scope、resource classification
2. **Task capability**: verified principal と user-approved action/target/volume/expiry
3. **IFC/provenance**: value-level integrity/confidentiality label と deterministic sink policy
4. **Runtime risk**: irreversible/repeated/anomalous action を approval queue へ
5. **Sink controls**: DLP、private-network/recipient allowlist、rate/volume limit、transaction/undo
6. **Detection layer**: prompt-injection classifier、spotlighting、LLM alignment judge は監査・補助に限定
7. **Evaluation**: clean utility と adaptive attack を同じ release gate にする

このコンペ API 内の最善の private 代理は `private02_provenance` ですが、実用 guardrail の方向性としては
`private03_intent` の capability binding と `private04_ifc` の value-level 化、`private05_risk` の selective approval を
統合するのが望ましいです。

## 8. テストで固定した不変条件

`guardrails/tests/test_guardrails.py` は以下を検証します。

- registry にちょうど5種類がある
- 到達不能認可キーを手動注入しても sensitive destructive action を bypass しない
- public の first-key payload hole を5種が deny または sanitize する
- `monkey.txt` を `key` substring だけで拒否しない variant がある
- clean / tainted email の policy matrix
- persistent taint が5-event window wash と snapshot/restore を越える
- intent variant が exact target を要求する
- IFC variant が file-derived write を拒否する
- risk variant が marker sanitize と反復 action approval を行う

この unit test は policy code の挙動を証明しますが、本物 private との一致や実モデル utility は証明しません。
それらは同じ candidates を5種へ replay し、predicate breakdown、clean-task completion、latency を比較して判断します。
