# Guardrail research index

調査日: **2026-08-25**。このディレクトリは以下を分離して記録します。

1. [`01-literature-review.md`](./01-literature-review.md): 脅威・防御・評価研究の整理と一次資料一覧
2. [`02-repository-findings.md`](./02-repository-findings.md): public 実装、harness、private probe のコード根拠
3. [`03-design-decisions.md`](./03-design-decisions.md): 5実装への落とし込み、費用・有用性・汎用性の比較

## 要約

実用的な結論は「prompt injection を完全検出する」ことではなく、モデルが誤動作しても被害が成立しない
実行境界を作ることです。優先順位は次のとおりです。

1. tool schema / target / scope に対する決定論的な complete mediation
2. task 単位の最小権限と具体的 target binding
3. provenance と confidentiality/integrity label の伝播
4. irreversible / external action だけに fresh approval を要求
5. DLP、rate/volume limit、監査ログによる blast-radius 制限
6. classifier、spotlighting、LLM judge は補助信号として利用し、単独の安全境界にはしない

public の blanket taint deny はコンペの `UNTRUSTED_TO_ACTION` を閉じるには合理的ですが、実運用では
「Webを調査してレポートを保存」「受信メールを読んで依頼どおり返信」といった主要用途まで止めます。
逆に、現在の public の到達不能な認可分岐や全引数を見ない実装は、防御思想ではなく実装上の名残・穴です。

private の実装本体は非公開です。リポジトリ内の timing probe が示すのは tool call の成功/非成功という
外形だけであり、DENY / CONFIRM / tool error の内訳や内部ルールまでは識別できません。したがって5種は
「実用上あり得る政策」と「観測に整合する仮説」の両方を覆う test suite として扱います。
