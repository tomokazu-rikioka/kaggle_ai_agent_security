# 文献調査: tool-using LLM agent guardrails

## 1. 調査範囲と方法

2026-08-25 時点で、以下の語群を組み合わせて arXiv、ACL Anthology、公式研究リポジトリ、OWASP、
ベンダーの一次資料を検索しました。

- indirect prompt injection / tool-integrated agent / confused deputy
- provenance / taint tracking / information-flow control / capability / least privilege
- task alignment / action alignment / authorization / human approval
- prompt injection benchmark / adaptive attack / utility / false positive / latency
- tool-input firewall / tool-output sanitizer / runtime trace / reference monitor

採用条件は、tool-using agent の脅威または防御に直接関係し、設計・評価条件を確認できる一次資料であることです。
製品記事だけの主張は、同じ機構を扱う論文または標準的ガイダンスで補強しました。静的 benchmark の数値は
security guarantee と見なさず、適応攻撃、clean-task utility、false positive、モデル呼出し回数も併記して評価します。

「網羅的」は全世界の論文を漏れなく列挙する意味ではなく、現時点の主要な防御ファミリー、代表実装、主要 benchmark、
反証研究を設計判断に必要な範囲で覆う、という意味で用います。

## 2. 脅威モデル

Greshake らは indirect prompt injection (IPI) を、第三者が制御する Web、メール、検索結果などを通じて
LLM application の命令解釈を遠隔操作する問題として体系化し、API 操作、データ窃取、worming を実証しました
([Not what you've signed up for, 2023](https://arxiv.org/abs/2302.12173))。

tool agent では、同じ text channel に「権限あるユーザー命令」と「権限のない外部データ」が混ざります。
[InjecAgent](https://arxiv.org/abs/2403.02691) は17 user tools・62 attacker tools・1,054 test casesで
直接被害と private-data exfiltration を評価し、[AgentDojo](https://arxiv.org/abs/2406.13352) は
97 realistic tasks・629 security casesを持つ動的環境として security と utility を同時評価しました。
[Agent Security Bench](https://arxiv.org/abs/2410.02644) は tool、memory、prompt を含む10 scenario・400超 toolsへ
範囲を広げています。

この脅威は単なる「悪い文字列検出」ではありません。同じ `email.send` でも、ユーザーが宛先を指定した送信は正常で、
メール本文が勝手に選んだ宛先への送信は confused deputy です。2026年の形式化研究は、contextual security を
task alignment、action alignment、source authorization、data isolation の4性質として整理しています
([A Framework for Formalizing LLM Agent Security](https://arxiv.org/abs/2603.19469))。

## 3. 防御ファミリー

### 3.1 Prompt / model 内の instruction separation

- [Spotlighting](https://arxiv.org/abs/2403.14720) は untrusted text を継続的に変換・マーキングして provenance を
  モデルに知らせ、報告された実験では attack success を50%超から2%未満へ低減しました。
- [The Instruction Hierarchy](https://arxiv.org/abs/2404.13208) は system > user > tool output の権限順位を
  post-training でモデルへ学習させます。過剰拒否を別に評価している点が重要です。
- [The Task Shield](https://arxiv.org/abs/2412.16682) は harmfulness ではなく、各 instruction/tool call が
  user task に寄与するかを test-time に検証します。ACL 2025版は GPT-4o / AgentDojo で ASR 2.07%、
  utility 69.79%を報告しています
  ([ACL Anthology](https://aclanthology.org/2025.acl-long.1435/))。
- [LlamaFirewall](https://arxiv.org/abs/2505.03574) は軽量 PromptGuard、LLM-based AlignmentCheck、
  code static analysis を層状に組み合わせます。検出率だけでなく、AlignmentCheck の latency と utility cost が
  実用上の論点です。

これらは導入しやすく、正常 task を柔軟に扱えます。しかし model-visible な防御は確率的です。
[Adaptive Attacks Break Defenses](https://arxiv.org/abs/2503.00061) は8防御すべてを適応攻撃で迂回し、
一貫して50%超の ASR を得ました。2026年の [AutoDojo](https://arxiv.org/abs/2606.15057) も、静的 ASR 0%の
filter に対し全体28%、action-open tasksで64%まで回復し、ユーザーが action/target の選択を外部データへ委ねる
task 自体に構造的限界があると指摘します。

したがってこのファミリーは early filter、監査、risk signal には有用ですが、唯一の authorization boundary にはしません。

### 3.2 Deterministic reference monitor / least privilege

[Progent](https://arxiv.org/abs/2504.11703) は tool call の許容条件と fallback を DSL で表し、agent 本体を変えずに
最小権限を決定論的に仲介します。policy 生成/更新に LLM を使う部分は、生成結果をそのまま authority とせず、
最終 enforcement を deterministic に保つ必要があります。

[CaMeL: Defeating Prompt Injections by Design](https://arxiv.org/abs/2503.18813) は trusted query から control/data flow を
抽出し、untrusted data が program flow を変えない構造と capability で unauthorized flow を防ぎます。
AgentDojo tasks の67%を provable security 付きで解いた一方、研究実装自身が未成熟であるとの注意も公式 artifact に
明記されています
([google-research/camel-prompt-injection](https://github.com/google-research/camel-prompt-injection))。

[AgentArmor](https://arxiv.org/abs/2508.01249) は runtime trace を CFG/DFG/PDG のような program representation に変換し、
type system で sensitive flow と trust boundary を検査します。報告値は TPR 95.75%、FPR 3.66%です。

この系統は prompt 表現の巧妙さに依存せず、完全仲介と default-deny を実装できます。一方で task-specific policy、
tool metadata、target scope が必要で、粗い tool-level allowlist は utility を強く落とします。

### 3.3 Provenance / taint / information-flow control

[System-Level Defense from an IFC Perspective](https://arxiv.org/abs/2409.19091) は IPI を integrity flow の問題として扱い、
system-level IFC を提案します。

[FIDES: Securing AI Agents with Information-Flow Control](https://arxiv.org/abs/2505.23643) は各データに
confidentiality と integrity label を持たせ、伝播と policy enforcement を決定論的に行い、必要な情報だけを
選択的に隠す primitive を導入します。Microsoft の実装解説でも、tool result と tool call に label を伝播し、
sensitive tool の実行前に policy を評価する構成です
([Microsoft Agent Framework FIDES](https://devblogs.microsoft.com/agent-framework/fides/))。

強みは confidentiality（秘密を外へ出さない）と integrity（untrusted data に高権限 action を選ばせない）を
別々に扱えることです。弱みは label granularity と endorsement/declassification 設計です。会話全体を1 bitの
`ever_tainted` にすると安全ですが、無関係な正常 action まで永久に止めます。field/value-level label が無い API で
FIDES を名乗るべきではなく、「粗い近似」と明記すべきです。

### 3.4 Input minimization / output sanitization / DLP

[Indirect Prompt Injections: Are Firewalls All You Need?](https://arxiv.org/abs/2510.05244) は tool-input minimizer と
tool-output sanitizer の2 firewall で複数 benchmark をほぼ飽和させましたが、同時に benchmark の weak attacks、
metric bugs、実環境での bypass を報告しました。結論は「firewall だけで解決」ではなく、必要最小限の data exposure と
sink-specific validation は安価な層として有効だが、headline score を保証と誤認しないことです。

このリポジトリでは `decide()` に tool output が渡らないため、本物の output sanitizer は実装不能です。
`private05_risk` の `SANITIZE` は outbound args に現れる明示 sentinel の redaction だけに限定します。

### 3.5 Human-in-the-loop、least agency、rate limit

[OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) は privilege control、
least privilege、high-risk action の human approval、external content の分離、継続的 adversarial testing を推奨します。
[OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) は原因を excessive
functionality / permissions / autonomy に分け、送信・削除などの approval と rate limiting を具体策に挙げます。

[Meta Agents Rule of Two](https://ai.meta.com/blog/practical-ai-agent-security/) は1 sessionで次の3能力を同時に持たせず、
3つ必要なら autonomous にせず supervision を要求する実務的 heuristic です。

1. untrusted input を処理する
2. sensitive system / private data にアクセスする
3. state を変更する、または外部通信する

これは prompt detector の精度に依存せず blast radius を構造的に切ります。ただし「2つなら常に安全」ではなく、
untrusted data による destructive write のように confidentiality を伴わない integrity 被害は別 policy が必要です。

## 4. 評価方法

guardrail は security だけを最大化すると全拒否が最適になります。最低限、次を別々に測る必要があります。

- Attack success / predicate breach（攻撃を止めたか）
- Clean task utility / task completion（正常依頼を完遂したか）
- False positive と approval rate（人間疲労を含む）
- Latency、追加 model calls、token、memory（実コスト）
- Adaptive attacker（防御を知る攻撃）と out-of-distribution transfer
- target/recipient/path/volume を変えた boundary cases
- snapshot/restore、multi-turn、long-horizon で state が一貫するか

AgentDojo 自身も attack と defense の双方を更新可能な環境として設計されています。さらに静的 benchmark の飽和を
安全証明と扱わない根拠として、上記の適応攻撃研究と firewall benchmark の自己批判を必ず併読します。

## 5. この実装へ採用した原則

- 文字列検出より tool 実行前の policy enforcement を優先する。
- `tool_name` だけでなく全引数、canonical target、side effect、scope を見る。
- untrusted integrity と secret confidentiality を同一フラグに潰さない実装も用意する。
- explicit user intent だけでなく、recipient / URL / path / command の具体値を user turn に束縛する。
- irreversible、external、repeated action は deny 一択でなく confirm / rate limit を比較する。
- classifier/LLM judge は本コンペ API の情報量・GPU cost・適応攻撃耐性に合わないため、5実装の core には入れない。
- private の内部を知っているとは主張せず、複数仮説へ同一候補を replay する。

## 6. 参考資料一覧

| 年 | 資料 | 主な用途 |
|---:|---|---|
| 2023 | [Greshake et al., Indirect Prompt Injection](https://arxiv.org/abs/2302.12173) | 脅威分類・遠隔注入 |
| 2024 | [InjecAgent](https://arxiv.org/abs/2403.02691) | tool agent benchmark |
| 2024 | [Spotlighting](https://arxiv.org/abs/2403.14720) | data marking |
| 2024 | [Instruction Hierarchy](https://arxiv.org/abs/2404.13208) | privilege-aware model training |
| 2024 | [AgentDojo](https://arxiv.org/abs/2406.13352) | security/utility benchmark |
| 2024 | [System-Level IFC](https://arxiv.org/abs/2409.19091) | integrity flow |
| 2024 | [Agent Security Bench](https://arxiv.org/abs/2410.02644) | tool/memory/prompt 横断評価 |
| 2024/25 | [Task Shield](https://arxiv.org/abs/2412.16682) | task/action alignment |
| 2025 | [Adaptive Attacks Break Defenses](https://arxiv.org/abs/2503.00061) | adaptive evaluation |
| 2025 | [CaMeL](https://arxiv.org/abs/2503.18813) | control/data separation・capability |
| 2025 | [Progent](https://arxiv.org/abs/2504.11703) | least-privilege DSL |
| 2025 | [FIDES](https://arxiv.org/abs/2505.23643) | confidentiality/integrity IFC |
| 2025 | [LlamaFirewall](https://arxiv.org/abs/2505.03574) | layered runtime scanners |
| 2025 | [AgentArmor](https://arxiv.org/abs/2508.01249) | runtime trace program analysis |
| 2025 | [Tool firewalls / benchmark critique](https://arxiv.org/abs/2510.05244) | minimization・sanitization・評価限界 |
| 2025 | [OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) | defense in depth |
| 2025 | [OWASP LLM06](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) | least agency・approval・rate limit |
| 2025 | [Meta Agents Rule of Two](https://ai.meta.com/blog/practical-ai-agent-security/) | lethal combination の分離 |
| 2026 | [Formalizing LLM Agent Security](https://arxiv.org/abs/2603.19469) | contextual security 4性質 |
| 2026 | [AutoDojo](https://arxiv.org/abs/2606.15057) | adaptive / action-open task 限界 |
