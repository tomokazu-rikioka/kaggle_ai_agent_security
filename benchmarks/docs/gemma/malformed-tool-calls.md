# Gemma tool-call parserとmulti-hop失速の整理

## 結論

Gemmaのmulti-hopがLBで弱い現象を、すべて「malformed JSON」と呼ぶのは正確ではない。
コード上は少なくとも次の4種類を分ける必要がある。

1. **1 generation内に複数tool call**: 各callが正しくても契約違反となり、そのhopは丸ごと失敗する。
2. **引数表現のparse失敗**: quoted key、delimiterずれ、double braceとnative構文の混在など。
3. **正常なfinal response / no-tool終了**: parse errorではないが、次のhopへ進まずchainが止まる。
4. **正常な逐次multi-hopだが遅い**: 1 hopごとに再生成とtool-result履歴の再レンダリングが必要で、LBの
   remote呼び出しコストもhop数だけ積み上がる。

現在のcompetition配布物にはKaggle専用`KaggleGemma4ToolCallParser`が存在する。ただし「より寛容」なのは
**double brace内に完全なJSON objectが残る場合だけ**で、複数call制限や通常のsingle-brace JSON keyは救済しない。

`vendor/aicomp_sdk_pkg/.../gemma_model_server.py`は現在のcompetition配布版より古い。一方、local評価経路の
`scripts/eval/eval_driver.py`にはcompetition側のparser差分を自己完結で移植済みであり、r28以降は
`KaggleGemma4ToolCallParser`を明示注入する。通常形式だけでなくdouble brace / JSON / malformed / multi-call境界も
unit testで固定している。r27以前の結果だけは標準parserなので、新結果との比較時に区別する。

## 確認したコードの版

2026-08-29にKaggle APIのcompetition filesから現行ファイルを直接確認した。

| 対象 | 状況 |
|---|---|
| competition配布 `kaggle_evaluation/jed_attack_134815/gemma_model_server.py` | 3,057 bytes。Kaggle専用parserを定義し、`Gemma4Agent(..., parser=KaggleGemma4ToolCallParser())`として使用 |
| repo内 `vendor/.../gemma_model_server.py` | 1,397 bytes。`Gemma4Agent(backend)`のみで標準parserを使用 |
| `scripts/eval/eval_driver.py` | Gemma時だけcompetition同等parserを生成し、`Gemma4Agent(backend, parser=...)`へ注入 |

competition側の中核は次の形になっている。

```python
def _parse_gemma4_arguments_kaggle(args_blob: str) -> JsonObject:
    if args_blob.lstrip().startswith("{"):
        return normalize_tool_arguments(args_blob)
    return _parse_gemma4_arguments(args_blob)


class KaggleGemma4ToolCallParser(Gemma4ToolCallParser):
    def parse(self, response, *, fallback_call_id):
        tool_calls = [
            {
                "type": "function",
                "function": {
                    "name": match.group("name"),
                    "arguments": _parse_gemma4_arguments_kaggle(match.group("arguments")),
                },
            }
            for match in _GEMMA4_TOOL_CALL_PATTERN.finditer(response.raw_text)
        ]
        if not tool_calls:
            return super().parse(response, fallback_call_id=fallback_call_id)
        return normalize_parsed_response(
            {"role": "assistant", "content": "", "tool_calls": tool_calls},
            fallback_call_id=fallback_call_id,
        )
```

実ファイルでは`content`に`_clean_fallback_assistant_text(response.text)`を渡すが、parser分岐の要点は上記で尽くされる。

## 「1 generation内の複数call」と「逐次multi-hop」は別物

| 形 | model generation数 | SDK上の扱い |
|---|---:|---|
| 1回の出力にtool-call blockを2個以上並べる | 1 | `normalize_parsed_response()`がhard error |
| 1 callを生成→tool実行→結果を履歴へ追加→次の1 callを生成 | call数と同数 | `max_tool_hops`以内なら許可 |
| `AttackCandidate`に複数user messageを持たせる | messageごとに1回以上 | `ReplayHarness`がmessageごとに`env.interact()` |

`aicomp_sdk/agents/hf_chat_template/response_parsing.py:103-107`は、抽出されたcallが2個以上なら
引数の正当性に関係なく次を送出する。

```python
if len(raw_tool_calls) > 1:
    raise InvalidModelOutputError("Model returned multiple tool calls")
```

したがって、1 generationで2個の正しいcallを出しても「先頭1個だけ実行」にはならない。**そのhopでは0個**である。

一方、`SandboxEnv.interact()`は1個の`ToolCallDecision`を実行してtool resultを履歴へ追加した後、for-loopの次周で
もう一度modelを呼ぶ。逐次multi-hopそのものは禁止されていない。competition gatewayは要求された`max_tool_hops`を
既定上限8へcapするだけで、8回の実行を保証するものではない。

## parserがbraceをどう見るか

標準のtool-call regexは`aicomp_sdk/agents/gemma4_agent.py:400-403`にある。

```python
r"<\|tool_call>call:(?P<name>[A-Za-z0-9_.-]+)\{"
r"(?P<arguments>.*?)"
r"\}<tool_call\|>"
```

外側の`{`と`}`はcapture groupの外側にある。従って、通常のsingle-brace出力では`args_blob`にbraceが残らない。

```text
raw:       call:email.send{"body":"","subject":"","to":"a"}
args_blob:                 "body":"","subject":"","to":"a"
```

この`args_blob`は`{`で始まらないため、Kaggle専用parserでもJSON branchではなくstrict branchへ入る。
strict parserのkeyは次のbare identifier形式に限定される。

```python
r"(?P<key>[A-Za-z_][A-Za-z0-9_.-]*):"
```

そのため先頭が`"body"`のquoted keyは一致せず、`Invalid Gemma 4 tool-call arguments`になる。

double braceなら外側の1組をregexが消費し、内側のbraceが`args_blob`に残る。

```text
raw:       call:email.send{{"body":"","subject":"","to":"a"}}
args_blob:                 {"body":"","subject":"","to":"a"}
```

この場合だけ`startswith("{")`が真となり、`json.loads`相当の`normalize_tool_arguments()`が使われる。

## 実parserで再現した形式別の結果

competition配布版と同じ分岐をrepoのSDK関数上に再現し、mail callだけで確認した。

| 生成形式 | branch | 結果 |
|---|---|---|
| single brace + bare key + `<|"|>` value | strict | OK |
| single brace + bare key +通常の`"value"` | strict | OK。bare valueとして取り込み、外側quoteをstrip |
| single brace + JSON quoted key | strict | `Invalid Gemma 4 tool-call arguments` |
| double brace +完全なJSON | JSON | OK |
| double brace +Gemma-native delimiter | JSON | `Invalid tool arguments JSON` |
| keyの前に余分な`<|"|>` | strict | `Invalid Gemma 4 tool-call arguments` |
| 正常なnative callを1 generationに2個 | strict→normalize | `Model returned multiple tool calls` |

正しいnative形の例:

```text
<|tool_call>call:email.send{body:<|"|><|"|>,subject:<|"|><|"|>,to:<|"|>a<|"|>}<tool_call|>
```

single-brace JSONで失敗する例:

```text
<|tool_call>call:email.send{"body":"","subject":"","to":"a"}<tool_call|>
```

double-brace JSONとしてだけ成功する例:

```text
<|tool_call>call:email.send{{"body":"","subject":"","to":"a"}}<tool_call|>
```

double braceは常に修復になるわけではない。内側がGemma-native構文なら誤ってJSON branchへ入り、むしろ
`Invalid tool arguments JSON`になる。このエラー名だけを見て「JSONを生成した」と判断してはいけない。

## parse error後に何が起きるか

`aicomp_sdk/core/env/sandbox.py:223-234`は`agent.next_action()`の`InvalidModelOutputError`を捕捉し、
assistant messageへ`(no_tool)`を追加して`break`する。

```python
except InvalidModelOutputError:
    if hop_idx == 0:
        agent_refused_immediately = True
    self._runtime_history = self._runtime_history.with_assistant_message("(no_tool)")
    self.trace.add_assistant("(no_tool)")
    break
```

ここでの`break`は**現在のuser messageに対するhop loop全体を終了**する。

最小fake agentでも次を確認した。

| failure位置 | agent turns | 成功tool event | 結果 |
|---|---:|---:|---|
| hop 0でmalformed | 1 | 0 | `(no_tool)`で終了 |
| hop 0で1 call成功、hop 1でmalformed | 2 | 1 | 先の1 eventは残り、hop 1以降を終了 |

従って「malformedが1回でも出ると候補全体が常に0点」は強すぎる。正確には次の通り。

- 最初のgenerationで複数callまたはmalformedなら、そのmessageは0 tool eventで終わる。
- 後続hopで失敗した場合、**それ以前の成功callは巻き戻されない**。ただし残りの予定callはすべて失われる。
- `ReplayHarness`の次のuser messageがある場合は、次の`env.interact()`自体は実行される。

## なぜlocalで7 callsでもLBで負け得るか

7回の逐次callがlocalで成功しても、次の差を個別に確認する必要がある。

### 1. 古いlocal結果ではparserがboardと一致していない

r27以前のbenchは`Gemma4Agent(backend)`の標準parserを使っている。r28以降はcompetition parserへ合わせたため、
新しい検証では結果JSONの`parser_profile=kaggle_gemma4`を確認する。差は主にdouble-brace JSON branchだが、
後続hopの出力形式によってmulti-hop成否にも波及する。

### 2. 1 generationに複数callを出している

表示上「7 callsを意図した」ことと、7回のgenerationで1個ずつ出したことは同じではない。raw outputに
tool-call blockが複数並ぶと、boardではそのhopがhard errorになる。local validatorが先頭callだけ採用したり、
複数callを分割実行しているなら明確な非互換である。

### 3. 後続hopだけ構文が崩れる

hop 0は短いuser prompt直後だが、hop 1以降はtool request・tool resultを含む履歴から再生成される。
quoted key、delimiter位置、double brace混在が後半だけ出れば、その時点で残りが全て消える。

### 4. parseは正常でもmodelがchainを終了する

`FinalResponseDecision`を返す、空テキストになる、または次の対象を選ばない場合も`SandboxEnv`はbreakする。
これはmalformedではない。traceの`(no_tool)`だけではparse errorと空応答を完全には区別できないため、debug eventが必要。

### 5. remoteのhop税をlocal throughputが含んでいない

LBではgatewayからmodel serverへの呼び出し、history serialization、再レンダリングがgenerationごとに発生する。
単発は1 generationだが7-hopは最大7 generationsであり、localの純生成時間で20–30%有利でも、
LBのscore/secondでは固定費に負け得る。

### 6. chat template / model / SDK版が違う

Gemmaはtool-result後のtemplateに敏感である。GGUF、chat template、SDK、competition model serverのいずれかが
違えば、hop 0が一致してもhop 1以降の生成は一致しない。

## このrepo内の既存実測との整合

`benchmarks/scripts/gemma/results/r7.json`では、単発は30/30で1 call。一方、2/4件を列挙した候補は
ほとんどが1 callで停止し、平均tool eventは最大1.167だった。少数の`email.list > email.send`は存在するため、
Gemmaの逐次multi-hopがSDK上絶対不可能なわけではない。ただし狙った同種callの連続にはならず、raw/秒も単発に負けた。

対照的にGPTの同じr7では、明示2-hopが30/30で2 calls、明示4-hopが30/30で4 callsになった。
この差は「SDKがmulti-hopを全面禁止」では説明できず、Gemmaの後続generation・template・出力安定性に依存する。

なおr7は標準Gemma parserである。その後、同じterse 2-hop文面をcompetition parser下のr29/r30で再測定し、
60/60で正確な2 callsを確認した。このためr7の「1 call停止」はparser mismatchを含む旧結果として扱う。

## malformedと断定するために必要な観測

スコア低下だけではmalformedと断定できない。最低限、失敗した**各hop**について次を保存する。

1. `response.raw_text`
2. regexが抽出したtool-call block数
3. 各matchの`name`と`arguments`文字列
4. strict / JSONのどちらへ分岐したか
5. `InvalidModelOutputError`の正確なmessage
6. failure前にtraceへ残ったtool events
7. generationごとのlatency

SDKの`HFChatTemplateAgent`は`response_received`と`parse_error`時に`response_payload`とerrorをdebug sinkへ渡す。
`InMemoryAgentDebugSink`または`JsonlAgentDebugSink`を`Gemma4Agent(debug_sink=...)`へ渡せば、raw outputとparse errorを
同じturn indexで対応付けられる。

判定の目安:

| 観測 | 診断 |
|---|---|
| raw内にcall blockが2個以上、error=`Model returned multiple tool calls` | 構文は正常でもsingle-decision契約違反 |
| error=`Invalid Gemma 4 tool-call arguments` | strict branchでkey/delimiter/separator不一致 |
| error=`Invalid tool arguments JSON` | JSON branchへ入ったが内側が有効JSONでない |
| errorなし、final textで終了 | malformedではなくmodelがchainを終了 |
| errorなし、1 callだけで終了 | 次generationの最終応答またはhop上限を確認 |

## 緩和策

### 最も堅牢: Gemmaは1 message 1 callにする

現在の実測ではこれが最も高いscore/secondになる。複数の独立候補へ分割すれば、1候補の後半失敗が他候補へ波及しない。

### multi-hopを試す場合

- 1 generationに複数callを出させず、「1 turnに1 call、tool result後に次へ」を明示する。
- raw outputがbare key + native delimiterへ安定していることをhopごとに確認する。
- double braceを一律に促さない。完全JSONなら成功するが、native構文との混在はJSON errorになる。
- 期待call数だけでなく、`tool_events_added`、各hopのraw output、error、総wall timeを測る。
- 後半failureを含めた**実現tool calls / 秒**で単発と比較する。

### localをLBへ合わせる

- `scripts/eval/eval_driver.py`へcurrent competition inputと同じ`KaggleGemma4ToolCallParser`差分を移植した。
- local agent生成は`Gemma4Agent(backend, parser=KaggleGemma4ToolCallParser())`相当になった。
- `scripts/eval/tests/test_gemma_kaggle_parser.py`でnative、double-brace JSON、single-brace quoted key失敗、
  1生成内multi-call失敗の4境界を固定した。
- r29以降は結果JSONの`parser_profile=kaggle_gemma4`を確認して、同一GGUF・chat template・
  `max_tool_hops=8`で比較する。r28 probeは同parserだがprofile欄追加前、r27以前のGemma結果は標準parserである。
- parser parityとremote latency parityは別問題なので、結果にはin-process時間とremote相当時間を分けて記録する。

## r28–r30での修正後実測

`scripts/eval/eval_driver.py`をcompetition parserへ合わせた後、旧r7と同一のterse文面を再測定した。

| parser / round | N | realized calls/candidate | exact sequence | raw/s |
|---|--:|--:|---:|--:|
| 標準SDK parser / r7 | 30 | 1.00 | 1-call 30/30 | 3.96 |
| Kaggle parser / r29 | 10 | 2.00 | `r→r.x` 10/10 | 5.91 |
| Kaggle parser / r30 ABBA | 60 | 2.00 | `r→r.x` 60/60 | 5.65 |

これにより「Gemmaは構造的に次hopへ進めない」という強い結論は否定された。competition専用parserは、標準parserが
落とす後続形式を実際に救済していると考えられる。ただしbenchはraw output自体を保存していないため、後続生成が
double-brace JSONだったという点は**parser差分からの推定**であり、byte-level確定にはdebug sinkでhop 1 rawを保存する。

一方、1 generation内の複数blockがhard errorである点は変わらない。また正確な逐次2-hopでもin-process raw/sは
単発6.33に対し5.65。本番コードでは各hopが`RemoteAgent.next_action()`からmodel server `predict()`を呼び、
full history/toolsを直列化するため、parser修正は正確性を直してもper-hop latencyを消さない。

## 参照箇所

- 単一decision制約: `vendor/aicomp_sdk_pkg/aicomp_sdk/agents/hf_chat_template/response_parsing.py:93`
- Gemma strict parser / regex: `vendor/aicomp_sdk_pkg/aicomp_sdk/agents/gemma4_agent.py:317`
- parse error後のbreak: `vendor/aicomp_sdk_pkg/aicomp_sdk/core/env/sandbox.py:223`
- tool成功後に次hopへ進む履歴更新: `vendor/aicomp_sdk_pkg/aicomp_sdk/core/env/sandbox.py:421`
- competition専用parser: `kaggle_evaluation/jed_attack_134815/gemma_model_server.py`（current competition files）
- repoのlocal agent生成: `scripts/eval/eval_driver.py:343`
- local multi-hop実測: `benchmarks/scripts/gemma/results/r7.json`
