# Private guardrail hypothesis suite

非公開ガードレールを断定的に復元するものではなく、同一の攻撃候補を異なる防御仮説へ replay して
汎化を測るための5実装です。実装根拠と文献調査は [`reseach/`](./reseach/README.md) にあります。
ディレクトリ名 `reseach` は依頼時の指定表記を維持しています。

## 5種類の位置づけ

| eval 名 | 実装 | 主機構 | 状態 | 実用性 / コスト | private 適合度 |
|---|---|---|---|---|---|
| `private01_fixed` | `private_01_public_fixed.py` | public の全引数走査・境界付き語彙・到達不能認可の除去 | なし | 最安。過剰遮断は public と同程度 | 中 |
| `private02_provenance` | `private_02_persistent_provenance.py` | web/email taint の永続化、機密 read/egress 遮断 | 小 | 安価で監査容易。ただし taint 後の正常業務を広く止める | **最高（既定代理候補）** |
| `private03_intent` | `private_03_intent_bound.py` | ユーザー意図と具体的 target を capability として束縛 | 小 | 正常な明示依頼を通しやすい。言語ヒューリスティック依存 | 中 |
| `private04_ifc` | `private_04_information_flow.py` | integrity/confidentiality の二軸 IFC | 小 | 決定論的で強いが、field-level label 不在のため過剰遮断最大 | 高 |
| `private05_risk` | `private_05_risk_adaptive.py` | risk tier、確認、回数制限、限定的 sanitize | 小 | 運用向き。閾値調整と承認 UI が必要 | 低〜中 |

全実装は外部モデルを呼ばず、判定コストは概ね `O(context + tool_args)`、状態は定数個のフラグと
ツール別カウンタだけです。各ファイルは SDK 契約どおり `Guardrail` クラスを公開します。

## 推奨する使い分け

- private LB の最有力代理には `private02_provenance` を使う。モジュール名
  `persistent_provenance` と既存 timing probe の観測に最も整合するためです。
- 攻撃の private 汎化を保守的に確認する場合は `private02_provenance` と `private04_ifc` の両方で試す。
- 実サービス設計の比較には `private03_intent` と `private05_risk` を含める。public/private の blanket deny が
  失う正常系を可視化できます。
- `private01_fixed` は public 実装の偶発的な穴だけに依存していないかを測る差分対照です。

## 実行

単体テスト:

```bash
PYTHONPATH=vendor/aicomp_sdk_pkg uv run python -m unittest discover -s guardrails/tests -v
```

既存の Kaggle replay 評価:

```bash
uv run python scripts/ops/run_eval.py expNNN \
  --guardrails public,private,private01_fixed,private02_provenance,private03_intent,private04_ifc,private05_risk
```

`scripts/ops/build_eval_notebook.py` が `guardrails/*.py` を評価 Notebook へ base64 埋め込みするため、
Kaggle 上でも同じ実装がロードされます。既存の `private` は過去スコアとの互換用代理のまま残してあります。

## 重要な限界

この SDK の `decide()` は tool output、tool 成否、verified principal、認可 token、計画、会話全体を受け取りません。
見えるのは tool 名・全引数と、直近5 tool の source/name、最後の user turn、side effect/scope、seed だけです。
したがって field-level IFC、真正なユーザー認可、tool output sanitizer を完全には実装できません。

また `CONFIRM` はこの harness では確認 UI に遷移せず、その tool attempt を失敗として hop loop を終了します。
本実装の `CONFIRM` は「実運用なら fresh approval に送る」という政策表現ですが、コンペ replay 上は hard block と
同じ結果になります。
