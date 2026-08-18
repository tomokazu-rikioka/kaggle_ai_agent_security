# 05. 外部リポジトリ調査と private guardrail 推定法

> **状態: 調査・設計のみ。LB 未提出。**
>
> 対象は [smly/kg-security](https://github.com/smly/kg-security) の 2026-06-19 時点の先頭コミット
> [`99c8964`](https://github.com/smly/kg-security/tree/99c896459ca5a71266fbd5e5aa682f7a64d7038f)。
> 本書は外部実装を private の真相として採用するものではない。競技中に見える外形だけから、最終提出の判断を変える
> guardrail の性質を推定する方法を整理する。
>
> 成立性・時計の交絡・実行前条件の正典は
> [04-条件分岐timingプローブ設計.md](./04-条件分岐timingプローブ設計.md)。本書はその外部調査編である。

---

## 5-1. 結論

1. 指定リポジトリには **有用な実験デザインがある**。最大の収穫は、同じ gate を持つ
   `control_short / control_long / conditional` の三群で、前 message の DENY/ALLOW を後続 message の処理量へ変換する
   **cross-message conditional timing probe** である。
2. ただし公開物は SDK 3.1.0 を取得した記録があり、最終コミットも 2026-06-19。本リポジトリの SDK 3.1.2 と
   2026-08-18 の評価運用に対し、候補数・秒数・Kaggle 倍率をそのまま移植してはいけない。
3. 外部リポジトリが置く L1〜L5 は、private 実装の観測結果ではなく**仮説の階段**である。有用なのは名前ではなく、
   「全引数走査」「exact value」「来歴」「正規化」「明示的共有意図」を 1 要因ずつ分離する発想である。
4. private の直接 query、表示 public score、generation-time router は private guardrail の観測にならない。
   競技中に使えそうなチャネルは実質 **submission 完了時間/status に private replay の処理量を符号化する timing 系だけ**。
5. 最初に probe するなら、抽象的な「private は何か」ではなく次の exact 2 点である。
   - `http.post(url=clean, data=<実際の得点 literal>)` を private が通すか。
   - 汚染前・危険語なしの clean `email.send` を private が通すか。
6. 実行順は **ローカル分岐検証 → guardrail-free CLOCK 較正 → exact gate の forward/reverse 複製**。
   CLOCK が live timing で再現しなければ、private probe は行わない。

---

## 5-2. `smly/kg-security` から得られたもの

### A. 三群対照の conditional runtime probe

外部リポジトリの中心的な成果は、
[`strict_guardrail_runtime_probe.py`](https://github.com/smly/kg-security/blob/99c896459ca5a71266fbd5e5aa682f7a64d7038f/codes/local_probing/strict_guardrail_runtime_probe.py)
と、その検証記録
[`strict_guardrail_runtime_probe.md`](https://github.com/smly/kg-security/blob/99c896459ca5a71266fbd5e5aa682f7a64d7038f/docs/agdr/local_probing/strict_guardrail_runtime_probe.md)
である。

同一の probe message の後ろに、次のいずれかを置く。

| variant | 後続 message の動作 | 役割 |
|---|---|---|
| `control_short` | tool を使わず短く終了 | 短い床 |
| `control_long` | 常に安全な追加処理を実行 | 最大増幅量の較正 |
| `conditional` | 直前の gate が DENY/CONFIRM/error の場合だけ追加処理 | guardrail 判定を時間へ符号化 |

判定は wall time だけでなく、ローカルでは次の比で検証されている。

```text
branch_ratio = (conditional_reads - short_reads) / (long_reads - short_reads)
```

- `≈0`: conditional は short 側、想定 gate は ALLOW 寄り。
- `≈1`: conditional は long 側、想定 gate は BLOCK 寄り。
- 中間: モデルの条件追従失敗、gate 不発、モデル差、部分的な分岐を疑う。

この三群化は本リポジトリの forward/reverse 案に加えて採用価値がある。`short` と `long` が同じ候補形の内部基準になるため、
モデルが本当に増幅を実行したかを private 仮説と分離しやすい。

### B. 105 候補の共通 baseline 案

[`kaggle_runtime_probe_common_short_21.py`](https://github.com/smly/kg-security/blob/99c896459ca5a71266fbd5e5aa682f7a64d7038f/codes/local_probing/kaggle_runtime_probe_common_short_21.py)
は、5 probe × 21 repeats の 105 候補を全提出で共通化し、1 群だけ `conditional` に差し替える設計である。
対応する設計記録は
[`kaggle_runtime_probe_common_short_21.md`](https://github.com/smly/kg-security/blob/99c896459ca5a71266fbd5e5aa682f7a64d7038f/docs/agdr/local_probing/kaggle_runtime_probe_common_short_21.md)。

良い点:

- 候補順、probe 数、message 数を揃え、変更点を 1 群の分岐文だけに限定する。
- `long` 群を private 判定に依存しない runtime calibration として持つ。
- L1〜L5 を同じ増幅器で比較できる。

そのまま使えない点:

- 「local-to-Kaggle 35.2 倍」「21 repeats で約 2 時間」は当時の局所見積りである。
- 105 候補すべてに 5〜6 messages を持たせるため、現在のモデル・context・9,000 秒 phase 上限では再計測が必要。
- 複数 probe 群を同時に入れると、未選択群も共通費用を増やす。最初の 1-bit 試験には単一 gate の小さい候補銀行がよい。

### C. guardrail 仮説の階段

外部リポジトリは private 候補を次のクラスへ分解している。

| 外部ラベル | 検査する性質 | 本リポジトリでの扱い |
|---|---|---|
| L1 sensitive args | URL だけでなく全引数に危険値があるか | H2「全キー走査」の候補 |
| L2 exact secret | 得点対象の exact literal/value を止めるか | EXFIL 生存を直接左右 |
| L3 flow/private | source に触れた後の sink を止めるか | coarse taint / provenance 候補 |
| L4 normalized | URL/base64/hex 等を正規化して止めるか | decoder/normalizer 候補 |
| L5 paranoid share | 明示的共有意図がない外部 action を止めるか | clean DEPUTY も閉じる強い仮説 |

この順序は複雑さの目安にはなるが、包含関係は保証されない。実物は「L2 はあるが L1 の一般 regex はない」など任意の組合せを取り得る。
結果は必ず「L3」と断定せず、**exact 入力に対する判定**として保存する。

### D. 有用な負の結果

[`strict_v2_encoding_probe.md`](https://github.com/smly/kg-security/blob/99c896459ca5a71266fbd5e5aa682f7a64d7038f/docs/agdr/exfil/strict_v2_encoding_probe.md)
では、URL encoding、Unicode escape、base64、fragment join などを exact-value proxy に対して試し、
両モデルとも EXFIL 0 だったと記録されている。

一般化できる学びは次。

- guardrail と scorer が最終的に同じ trace args を見るなら、encoded のまま通れば scorer が発火せず、decode すれば guardrail に止められる。
- したがって encoding sweep は、**parser/serialization の非対称性という具体仮説がない限り優先度が低い**。
- private probe 枠は、低事前確率の bypass 探索より「得点 literal を通すか」の直接判定に使う方がよい。

### E. private を観測しないもの

外部の
[`adaptive_probe_classifier_matrix.py`](https://github.com/smly/kg-security/blob/99c896459ca5a71266fbd5e5aa682f7a64d7038f/codes/submission_mix/adaptive_probe_classifier_matrix.py)
は、`run()` 中の public 環境で agent/model と public guardrail branch を分類する router である。モデル名の自然言語応答などは
public の branch 選択には有用でも、**private は static replay なので private guardrail の観測にはならない**。

また、外部の guardrail mix estimator と L1〜L5 の事前確率は意思決定フレームとしては有用だが、確率値は主観的な仮定である。
観測による posterior と混同しない。

### F. 再利用上の注意

- snapshot の README は `aicomp_sdk-3.1.0` の取得を記録している。本リポジトリは vendor SDK 3.1.2。
- 公開先頭コミットは 2026-06-19 で、その後の evaluator/runtime 更新を含まない。
- リポジトリ自体の LICENSE/COPYING/NOTICE は確認できなかった。SDK 同梱物の LICENSE は別物である。
  よってコードのコピーはせず、ここでは実験デザインと結果の要約だけを利用する。

---

## 5-3. private guardrail を知る方法の全体像

| 方法 | 分解能 | private 情報 | 提出枠 | 評価 |
|---|---:|---:|---:|---|
| `attack.py` から直接 query | 高そうに見える | なし。探索 env は public | 0 | 不可 |
| 表示 public score の差 | score | なし | 1+ | candidate 健全性確認のみ |
| generation-time router | branch | なし | 0/1 | public/model 選択用 |
| local private proxy | trace/score | 仮説のみ | 0 | 候補設計と事前検証用 |
| 同一 message の early-break timing | 連続時間 | あり得る | 2+ | 単純だが最大 8 hop、追従依存 |
| cross-message conditional timing | 連続時間 | あり得る | 2+ | 増幅しやすいが履歴分類が交絡 |
| forward/reverse polarity | timing の符号 | あり得る | 4+ | 常時 long を検出しやすい |
| short/long/conditional 三群 | timing + 内部較正 | あり得る | 3+ | ローカル検証に最も有用 |
| COMPLETE/ERROR/VOID/saturation | 粗い 1 bit | あり得る | 2+ | 原因が多く最終手段 |
| final private LB | score | あり | 終了後 | 事後分析のみ |
| hidden wheel/fixture の取得 | 実装/データ | あり | — | 本計画の範囲外 |

独立した観測方法が多数あるのではない。主に timing channel に対し、どの増幅器・対照・符号化を使うかの違いである。

---

## 5-4. 推定対象を「実装名」でなく判定軸へ分解する

private guardrail を 1 個のクラス名として当てに行かず、`decide(tool_name, tool_args, context)` の有限入力上で次を分離する。

| 軸 | matched probe の例 | 最終判断への影響 |
|---|---|---|
| tool args の走査範囲 | 同じ clean URL、`data=neutral` vs `data=literal` | public EXFIL の転移 |
| exact literal | neutral secret-like 語 vs 実得点 literal | scorer と block の一致 |
| 正規化 | plain vs URL/base64/hex/reverse | encoded 系の可能性 |
| `last_user`/intent | args 同一、文面だけ明示許可/非明示 | clean DEPUTY / L5 仮説 |
| tool policy | clean `http.post` vs clean `email.send` | tool ごとの許可面 |
| taint source | web/email/file/なし | provenance の source 範囲 |
| taint memory | source → 0/5/6 benign events → sink | window 5 vs 永続状態 |
| 値来歴 vs session taint | source に触れ、無関係定数/取得値を送信 | coarse flag vs value tracking |
| decision kind | ALLOW/DENY/CONFIRM/SANITIZE | 後続動作と実際の action 成否 |

特に provenance は次の 2×2 を崩さない。

| source 接触 | sink の値 | 主に識別するもの |
|---|---|---|
| なし | neutral 定数 | handler/tool baseline |
| なし | synthetic/exact marker | lexical/value scan |
| あり | source と無関係な定数 | coarse session taint |
| あり | source 由来値 | value provenance 候補 |

`SECRET_MARKER` だけが BLOCK されても「persistent provenance」とは言えない。単なる exact-value scan でも説明できる。

---

## 5-5. 推奨する probe プロトコル

### Stage 0: ローカル oracle で増幅器を検証する

private proxy ではなく、判定が確定した `AlwaysAllow / AlwaysDeny / AlwaysConfirm` を使う。

1. gate tool call の発火率を両モデルで測る。
2. `short / long / conditional` の tool 数、出力 token、wall time を測る。
3. forward は ALLOW、reverse は DENY/CONFIRM のときだけ long になることを確認する。
4. K=2,4,8 程度で履歴分類精度と context 肥大を測る。
5. 第一選択は tool-free 固定長 tail。`fs.read` tail は branch を trace で数えられる第二選択。

private 仮説を入れた代理で分岐しただけでは不十分。増幅器が既知判定を正しく復号できることが先である。

### Stage 1: live CLOCK を較正する

guardrail を一度も呼ばない `CLOCK-SHORT` と `CLOCK-LONG` を作る。順序を事前に
`SHORT/LONG/LONG/SHORT` などと固定し、polling を細かくして既知の時間差が COMPLETE 時間へ現れるかを見る。

- 符号が再現しない。
- duplicate の spread が信号と同程度。
- queue/polling 誤差を分離できない。

いずれかならここで停止する。private probe の timing だけを解釈してはいけない。

### Stage 2: 最終提出を変える 1 bit を問う

優先順位:

1. **Exact EXFIL gate** — clean URL + 実際の得点 literal。
2. **Clean DEPUTY gate** — 汚染なし・危険語なし・文面に述語抑制語を含めない `email.send`。
3. **全引数走査の matched pair** — neutral payload と secret-like payload。
4. **window vs persistent taint** — setup chain が両モデルで 95% 以上成立した場合のみ。

各 gate で forward/reverse を少なくとも複製し、提出前に閾値を固定する。1 回の差で結論を出さない。

### Stage 3: 因子分解

1 bit の再現後にだけ、位置移動、tool 種別、taint source、正規化の matched probe を行う。
複数仮説を候補数の異なる重みで符号化する group testing/Hadamard 案は、時間の加法性と非飽和が確認された後の候補である。

---

## 5-6. probe を情報利得で選ぶ

知りたいのは guardrail の名前ではなく、最終提出の配分である。probe `q` の価値は概念的に次で比較する。

```text
EVSI(q) = E[probe 後に選ぶ最良提出の private 期待値]
          - 現在の情報で選ぶ最良提出の private 期待値
          - probe の提出枠コスト
```

例えば exact EXFIL が ALLOW なら public 高密度アームの private 価値が大きく上がり、BLOCK なら clean DEPUTY の比重が上がる。
この分岐は最終構成を直接変えるため価値が高い。一方、「URL encoding も正規化するか」は exact literal が既に BLOCK され、
かつ scorer/guardrail 非対称の具体仮説がない限り、結果が最終構成を変えにくい。

外部リポジトリの L1〜L5 belief を固定値として借りず、本リポジトリの提出候補ごとに次を表へ持つ。

- その判定が ALLOW/BLOCK のときの予想 private score。
- public score と runtime。
- probe 結果が提出選択を変える閾値。
- 結果が判別不能だった場合の保守的構成。

---

## 5-7. 誤推論を防ぐ判定表

| 観測 | まず疑う別説明 | 記録してよい結論 |
|---|---|---|
| conditional が long | model が常に tail を実行 | local short/long と forward/reverse を再確認 |
| private BLOCK 風 | gate tool 自体が不発/handler error | exact gate についても未判定 |
| 中間的な時間 | 片モデルだけ分岐、queue 差 | guardrail の「部分実装」とは断定しない |
| marker が BLOCK | exact/regex scan | provenance とは呼ばない |
| source 後の定数が BLOCK | coarse session taint | 値来歴とは呼ばない |
| source 由来値だけ BLOCK | value tracking または lexical 差 | 値と文字列を合わせた追加対照が必要 |
| clean email が BLOCK | tool/intent policy | 全述語閉鎖とは断定しない |
| encoding が ALLOW、score 0 | encoded のまま trace に残った | guardrail bypass だが得点攻撃ではない |
| 時間が上限付近 | 9,000 秒 phase saturation | 量的差は判別不能 |

結果ラベルは `ALLOW 示唆 / BLOCK 示唆 / 判別不能` の三値にし、`private=L3` のような実装断定は避ける。

---

## 5-8. 現時点の実施提案

LB 提出前に行う価値がある作業は次。

1. 外部リポジトリのコードは移植せず、本 SDK 3.1.2 用の最小 harness で
   `AlwaysAllow / AlwaysDeny / AlwaysConfirm × short/long/conditional × 2 models` を再実装する。
2. `fs.read` tail と tool-free token tail を比較し、branch accuracy と時間分離が良い方を選ぶ。
3. exact EXFIL と clean DEPUTY の 2 gate だけを候補化し、N/K/出力長を現行 Kaggle runtime で再サイジングする。
4. CLOCK 較正を 1 日の提出枠内で再現できる設計にする。
5. ユーザーから明示的な LB 提出指示があった場合に限り、CLOCK から開始する。

現時点では外部調査と文書化のみ。attack 実装、Kaggle push、LB Submit は行っていない。
