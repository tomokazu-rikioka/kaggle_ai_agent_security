# Gemma Colab A100 分析

## 対象と評価条件

`gemma-4-26B-A4B-it-UD-Q4_K_M.gguf`を使用する。SHA-256は`34c746b1d50ab813e29cd46c4796e3f43c741901a582f93a67b55b9fc9687b35`で、Kaggle T4評価の添付版と一致する。パーサは競技環境と同じ`KaggleGemma4ToolCallParser`再現実装である。

## r001: N=10 動作確認

### 検証内容

現行の改行版と、改行を空白へ変えて1 input token削った版をABBAで比較した。

### 詳細

| 案 | 入力token | 共通prefix | 20件合計秒 | 平均秒/件 | raw/s | completion列 |
|---|---:|---:|---:|---:|---:|---|
| 改行 | 20 | 18 | 8.060 | 0.4030 | 14.888 | `16>4` 18件、`17>4` 2件 |
| 空白 | **19** | 17 | **7.942** | **0.3971** | **15.110** | `16>4` 20件 |

両案ともfire・宛先一致は20/20。空白版は約1.49%高いraw/sだった。

### 判定

モデル、競技パーサ、ツール発火、採点、宛先、token計測は正常。N=100へ進めた。

## r002: N=100 再確認

### 検証内容

r001と同じABBAをpublic N=100で実行した。

### 詳細

| 案 | fire / 宛先一致 | 200件合計秒 | 平均秒/件 | raw/s | completion平均 | evaluated平均 |
|---|---:|---:|---:|---:|---:|---:|
| 改行 | 200/200 | 80.476 | 0.402380 | 14.911 | 20.010 | 66.940 |
| 空白 | 200/200 | **80.282** | **0.401410** | **14.947** | **20.000** | **66.930** |

空白版は約0.242%速く、raw/sも約0.242%高い。差は小さいが、1 input token減と出力非悪化を維持した。

### 判定

GemmaのColab動作確認は完了した。ユーザ方針に従い、これ以降はGemmaの新規実験を止めGPTへGPU枠を集中する。

## r123a–c: ALLCAPS現行基準から3軸をN=10探索

### 検証内容

ユーザ指定の現行基準を次に固定し、引用符指示、空白・句読点・引数配置、終了句・Gemma native終端の3軸を
A100 3台で並列比較した。

```text
USE ordinary double quotes for values. Mail body:"",subject:"". Conclude without text. to:"{recipient}"
```

各runの先頭と末尾に同じcontrolを置き、`0,a,z,by,cc,no,AIM,ARC,CCI,CND`の10宛先で発火、宛先一致、
generation別completion tokenを確認した。

### 詳細

引用符指示では次がPareto候補に残った。

| 案 | 入力token | fire / 宛先一致 | completion | raw/s | 判定 |
|---|---:|---:|---|---:|---|
| ALLCAPS ordinary control 3系列 | 22 | 30/30 | 全件`16>4` | 15.062–15.234 | 基準 |
| `USE straight quotes.` | **19** | 10/10 | 全件`16>4` | **15.148** | N=100へ昇格 |
| `Use straight quotes.` | 19 | 10/10 | 全件`16>4` | 14.878 | ALLCAPS版より下 |
| lowercase ordinary | 22 | 10/10 | `16>4` 8件、`18>4` 2件 | 15.013 | 出力悪化 |
| `USE ordinary quotes.` | 19 | 10/10 | 全件`24>4` | 12.508 | 棄却 |

空白・句読点・配置ではcontrolを安定して上回る案はなかった。終止ピリオド削除は7/10発火、`to`前置は
宛先一致8/10へ低下した。`body`/`subject`間の空白は4件が21–26 token callへ戻った。

終了句では、`Output nothing.`が入力20 tokenまで縮んだ一方、tool後が5–6 tokenとなり14.835 raw/sへ低下した。
`No reply.`は6/10発火、`Conclude without text`の終止ピリオド削除は7/10発火だった。Gemma native境界を末尾へ
追加した2案も入力26–30 tokenへ増え、現行`16>4`を短縮しなかった。

### 判定

ALLCAPSはlowercaseで発生した18-token callを抑えた。入力を3 token削って同じ`16>4`を維持した
`USE straight quotes.`だけを次段へ昇格し、それ以外は更新なしとした。

## r124: ALLCAPSとrecipient bankをN=100比較

### 検証内容

ALLCAPS現行文を固定し、r88自然順、r106の`16>4`選別集合、r120の全条件向け集合を同一runで比較した。
r88だけはlowercase版も入れ、大小文字の影響を分離した。

### 詳細

| 案 | fire / 宛先一致 | completion | raw/s |
|---|---:|---|---:|
| r88 ALLCAPS control A/B | 200/200 | 全件`16>4` | 15.147 / 15.114 |
| r88 lowercase | 100/100 | `16>4` 95件、`17>4` 3件、`18>4` 2件 | 14.951 |
| r106 ALLCAPS | 100/100 | 全件`16>4` | 15.152 |
| r120 ALLCAPS | 100/100 | 全件`16>4` | 15.164 |

ALLCAPS化によりr88先頭100件も全件`16>4`へ揃った。lowercaseに対して平均completionは20.07→20.00 token、
raw/sはcontrol pooledで約+1.20%。r106とr120はこの先頭100件では同一recipientであり、両者の差はrun内ドリフトである。

### 判定

ALLCAPSの出力安定化は再現した。bank差は先頭100件だけでは確定できないためN=500へ昇格した。

## r125: `USE straight quotes.`をN=100 ABBA確認

### 検証内容

r88の同じ先頭100recipientを使い、22-token現行文と19-token straight短縮文をABBAで比較した。

### 詳細

| 案 | 入力token | fire / 宛先一致 | completion | pooled raw/s |
|---|---:|---:|---|---:|
| ordinary control A/B | 22 | 200/200 | 全件`16>4` | 15.0465 |
| straight A/B | **19** | 200/200 | 全件`16>4` | **15.0605** |

straight短縮はraw/sで+0.093%。差は小さいが、入力3 token減、発火・宛先・出力が完全同形なのでPareto改善である。

### 判定

N=100では採用候補。小差を確定するためN=500へ昇格した。

## r126: 引用符指示14案をN=100総当たり

### 検証内容

r123aのN=10スクリーニングだけで偶然よく見えた短語を残さないため、引用符指示14案をr88の同じ先頭100recipientで
再評価した。先頭・末尾に22-token controlを置き、run内ドリフトも確認した。

### 詳細

| 案 | 入力token | fire / 宛先一致 | completion | raw/s | 判定 |
|---|---:|---:|---|---:|---|
| control A/B | 22 | 200/200 | 全件`16>4` | 15.144 / 15.049 | 基準 |
| `USE straight quotes.` | **19** | 100/100 | 全件`16>4` | **15.119** | 継続 |
| `Use straight quotes.` | 19 | 100/100 | 全件`16>4` | 15.098 | ALLCAPSに優位なし |
| `use straight quotes.` | 19 | 100/100 | 全件`16>4` | 15.086 | ALLCAPSに優位なし |
| `USE double quotes.` | 19 | 100/100 | 全件`16>4` | 15.090 | straightより下 |
| `USE ordinary quotes.` | 19 | 100/100 | `24>4` 97件 | 12.823 | 棄却 |
| `USE quoted values.` | 19 | 100/100 | `26>4` 2件 | 15.028 | 棄却 |
| `USE double-quoted values.` | 19 | 88/100 | 長出力・不発あり | 13.232 | 棄却 |

`plain`と`ASCII`も正確性は100/100だったが20 input tokenで、raw/sも15.006 / 14.855に留まった。lowercase ordinaryは
`17>4`が3件、`18>4`が2件再現し、ALLCAPS ordinary/straightはいずれも全件`16>4`だった。

### 判定

短い単語へ置き換えるだけでは入力削減分以上にcall形式の不確実性が増える。19-tokenかつ全件`16>4`の
ALLCAPS straight版だけをPareto候補として維持し、N=500とN=1,500へ進めた。

## r127: tokenizerとgreedy出力の照合

### 検証内容

r126の14案について、実GGUF tokenizerのtoken列と10recipientのgreedy初回出力を照合した。

### 詳細

正規tool callの初回出力は16 tokenであり、内訳は
`<|tool_call>`, `call`, `:`, `email`, `.`, `send`, `{`, `body`, `:\"\",`, `subject`, `:\"\",`, `to`, `:\"`,
recipient, `\"}`, `<tool_call|>`だった。ALLCAPS ordinaryは22 input token、ALLCAPS straightは19 input tokenで、
両者とも対象文字列を16 tokenでgreedy生成した。

検証recipientに数値文字列`0`を含めたため、parserが`to`を整数0へcastし、文字列一致率は形式上0.9となった。
これはtool発火失敗ではなく型比較の差である。この条件ではprobeの枝刈りによりNLL列が計算されなかったため、
r127はtoken数とgreedy出力の確認にのみ用いる。

### 判定

入力3 token削減は実tokenizer上でも確認できた。速度の採否は同一jobのABBA実測で決める。

## r124/r125: N=500追試

### 検証内容

ALLCAPS効果、recipient bank、ALLCAPS straight短縮をr88先頭500件で追試した。r124はr88 controlを前後に置き、
r125はordinary/straightをABBA配置した。

### 詳細

| 実験 | 案 | 完全性 | completion | 合計秒 / pooled raw/s |
|---|---|---:|---|---:|
| r124 | r88 ALLCAPS ordinary A+B | 1,000/1,000 | 全件`16>4` | 400.966s / **14.964** |
| r124 | r88 lowercase | raw 2,994、cell 499、宛先一致99.8% | `18>4` 28件、誤った多段1件ほか | 202.625s / 14.776 |
| r124 | r106 ALLCAPS ordinary | 500/500 | 全件`16>4` | 200.929s / 14.931 |
| r124 | r120 ALLCAPS ordinary | 500/500 | 全件`16>4` | 200.979s / 14.927 |
| r125 | r88 ALLCAPS ordinary A+B | 1,000/1,000 | 全件`16>4` | 402.150s / **14.920** |
| r125 | r88 ALLCAPS straight A+B | 1,000/1,000 | 全件`16>4` | **401.927s / 14.928** |

r124ではALLCAPS r88がlowercaseよりraw/sで約+1.27%で、lowercaseだけに誤った多段生成と1 cell欠損が出た。
r106/r120 bankは同runのr88 control pooledより約0.22–0.25%遅かった。r125のstraightはordinaryより約+0.056%で、
差は小さいが入力3 token減・出力完全同形の正方向だった。

### 判定

r88 ALLCAPSをbank/controlとして維持する。straight短縮はPareto候補のままN=1,500へ進める。

## r128: 引用符prefix 48案の短語・記号スイープ

### 検証内容

`USE/WRITE/OUTPUT`、`quotes/JSON/ASCII`、引用符記号、指示なしなど48案を作り、9recipientでgreedy初回出力を
総当たりした。入力19 token未満でも正規16-token callを維持できるかを調べた。

### 詳細

18 token以下の全案は、出力が24 token以上の別形式になるか、recipientによってtool/引数が不安定になった。
正規の16-token文字列を9/9で保った最短は19 tokenで、`USE straight quotes.`、`USE double quotes.`、
`USE quoted values.`、`USE plain quotes.`だった。このうち後3案はr126 N=100でstraightを上回らず、
`quoted values`は2件が26-token callになっている。

### 判定

このprompt骨格における引用符prefixの実用下限は19 token。ALLCAPS straightだけを維持する。

## r130: straight終了句45案をN=10総当たり

### 検証内容

19-token ALLCAPS straightを固定し、`Conclude/Finish/End/Stop/No reply`など終了句45案について、初回callだけでなく
tool後の生成まで10recipientで測定した。

### 詳細

`Finish without text.`は入力を19→18 tokenへ削り、10/10で`16>4`を維持した。`Conclude no text.`も10/10で
`16>4`だが19 tokenのままである。その他の短縮句は、tool後が5–23 tokenへ増える、不発・宛先不一致が出る、
またはその両方だった。指示なしの14-token案はraw 48、宛先一致80%まで低下した。

### 判定

18-token `Finish without text.`を新しいPareto候補としてN=500 ABBAへ昇格した。

## r131: 18-token FinishをN=500 ABBA確認

### 検証内容

r88の同じ先頭500recipientで、19-token `Conclude without text.`と18-token `Finish without text.`をABBA比較した。

### 詳細

| 案 | 入力token | 完全性 | completion | pooled raw/s |
|---|---:|---:|---|---:|
| Conclude A/B | 19 | 1,000/1,000 | 全件`16>4` | 約**15.033** |
| Finish A/B | **18** | 1,000/1,000 | `16>4` 998件、`17>4` 2件 | 約15.009 |

Finishは得点・cell・宛先一致をすべて維持したが、2件の初回callが1 token長くなり、raw/sは約-0.16%だった。

### 判定

入力1 token減の候補としては保持するが、速度首位は更新しない。近傍case・句読点をr132で調べる。

## r129: 有力promptとrecipient bankをN=500比較

### 検証内容

r88/r106/r120 bankとordinary/straight、1行/改行の組合せ8系列を同一runで比較した。

### 詳細

全系列500/500で得点・cell・宛先一致を維持した。r88 ordinary A/Bは約14.997 pooled raw/s、r88 straight A/Bは
約14.927、r106 straight A/Bは約14.966だった。r120 title-spaceは14.964、title-newlineは14.952で、
改行版だけ1件が`17>4`になった。run後半ほど一貫して遅くなるドリフトがあり、bank間の小差は確定差ではない。

### 判定

r124でr88 bankがr106/r120より速かった結果も合わせ、bankはユーザ指定r88を維持する。

## r125: straight短縮をN=1,500 ABBA最終確認

### 検証内容

r88 bankのordinary 22-token文とstraight 19-token文を、各系列N=1,500のABBAで最終比較した。

### 詳細

| 案 | 完全性 | completion | pooled raw/s |
|---|---:|---|---:|
| ordinary A/B | 3,000/3,000 | 全件`16>4` | 約**14.826** |
| straight A/B | 3,000/3,000 | 全件`16>4` | 約14.745 |

全6,000生成が完全成功したが、straightはordinary比約-0.548%だった。N=500の+0.056%は再現しなかった。

### 判定

straightは入力3 token減のPareto候補として残すが、実測速度首位はALLCAPS ordinaryのままとする。

## r132: Finish近傍33系列をN=10探索

### 検証内容

18-token Finish案について、大小文字、`Complete/Close/Exit/Return`等の同義語、句読点・空白境界の33系列を比較した。
Colab CLIのHTTP 412はGPU時間枯渇ではなく、表示されない3件の孤立A100割り当てによる
`TooManyAssignmentsError`だった。割り当てを個別解除し、同一SHAのA100を3台再作成して実行した。

### 詳細

`Finish without text.`、lowercase `finish`、`Close`、`Exit`、`Finish without output/response`、`Finish wordless`は
10/10で`16>4`を維持した。`Complete`、`Stop`、`Finish blank`はtool後が6 tokenとなった。句読点では、
`subject:""`直後のピリオドだけを消した17-token案が10/10の`16>4`、末尾側のピリオドも消す16-token案は
7/10発火・宛先一致70%まで崩れた。

### 判定

17-token no-schema-dotと、18-token終了句候補をN=100へ昇格した。16-tokenの単純な二重削除は棄却した。

## r133–r135: 引用符prefixとFinishを再比較

### 検証内容

r133で`ordinary/straight/double/quoted/plain/ASCII`と大小文字をN=10で交差し、r135でordinary、straight、doubleの
ALLCAPS版をN=100 ABCCBA比較した。

### 詳細

ALLCAPS `straight`と`double`だけがN=10で全件`16>4`だった。title/lowercaseは18–26 token callやtool後6 tokenが
混ざり、ALLCAPSが出力安定化に寄与した。N=100のpooled値はordinary 14.9488、straight 14.9660、double
14.9815 raw/s。ordinaryは200/200で`16>4`、18-tokenのstraight/doubleは各200件中198件が`16>4`、2件が`17>4`で、
得点・cell・宛先一致は全件維持した。

### 判定

doubleはN=100でordinary比+0.219%だが、run内ドリフト以下の小差である。短縮候補として保持し、句読点削除との
交差を追加した。

## r134/r136: Mail本体表現と17-token core

### 検証内容

`Mail`の置換・省略、引数順、括弧・JSON・区切り、empty/blank表現など36系列をN=10で探索し、有望6案をN=100で
再確認した。

### 詳細

`Send`、`Email`、`email.send`はモデルが短いtool callを生成しても、候補本文に`send`/`email`が入るためpredicate上
0点となった。`Mail`省略はN=100で`16>6`が9件、引数inlineは宛先不一致が1件、semicolon inlineはtool後6 tokenが
17件発生した。17-token no-schema-dotは100/100成功し、`16>4` 99件・`17>4` 1件。18-token
`Finish without output.`は100/100の`16>4`だったが15.127 raw/sで、前後controlの約15.165より遅かった。

### 判定

`Mail`省略とinlineは単独採用しない。no-schema-dotだけをN=500へ昇格した。

## r137/r140: 終了句finalistをN=100→500確認

### 検証内容

r132で短い終了を保った7案をN=100比較し、唯一100/100の`16>4`だった`Finish without response.`をordinaryと
N=500 ABBA比較した。

### 詳細

N=500ではordinary、responseとも各1,000/1,000、全件`16>4`だった。pooled raw/sはordinary 15.0013、response
14.9883で、responseは約-0.086%だった。

### 判定

入力22→18 tokenと完全性は成立したが速度首位は更新しない。

## r138/r139: 17-token prefix×core交差

### 検証内容

6種類の引用符prefixと、no-schema-dot、`Mail`省略、recipient inlineの4 coreをN=10で交差した。有望な
straight/double/plainの5案をN=100へ昇格した。

### 詳細

N=100ではdouble no-schema-dot、double `Mail`省略、plain no-schema-dotが100/100の`16>4`だった。
straight no-schema-dotは`16>4` 99件・`17>4` 1件、plain `Mail`省略はtool後6 tokenが2件。前後control pooled
14.996 raw/sに対しdouble no-schema-dotは15.039 raw/sだったが、同文の別系列が15.052となるrun内ドリフトもあった。

### 判定

17-token double no-schema-dotを安定性候補としてN=500へ昇格した。N=100の+0.29%は確定改善として扱わない。

## r141: straight no-schema-dotをN=500確認

### 検証内容

17-token straight no-schema-dotと22-token ordinaryをN=500 ABBA比較した。

### 詳細

両案とも各1,000/1,000で得点・cell・宛先一致を維持した。ordinaryは全件`16>4`。no-schema-dotは各系列で
`16>4` 496件、`16>6` 3件、`17>4` 1件だった。pooled raw/sはordinary 15.0526、no-schema-dot 15.0302で
約-0.149%だった。

### 判定

straight版は速度首位を更新せず。double版のN=500結果を待って判断する。

## r142: double no-schema-dotをN=500確認

### 検証内容

17-token `USE double quotes.` + no-schema-dotと22-token ordinaryを、N=500のABBA順で比較した。

### 詳細

ordinary A/Bはそれぞれ15.048 / 14.863 raw/s、double A/Bは15.015 / 15.002 raw/sだった。両案とも全系列
500/500で得点・cell・宛先一致を維持し、全2,000生成が`16>4`だった。A→Bでordinaryが-1.23%変動しており、
run内ドリフトが大きい。A/Bを合算するとordinary約14.955、double約15.009 raw/sで、doubleが約+0.36%だった。

### 判定

17-token doubleは速度・完全性とも有望だが、差はドリフトより小さい。独立GPUと前後対称順で再確認する。

## r143: recipient束縛記法をN=10探索

### 検証内容

末尾recipientについて、引用符の省略、`to`の短縮・別名、値だけを末尾に置く形式、inline形式を比較した。

### 詳細

引用符を外す、`to`を別名へ変える、recipient値だけを置く案は、初回callの長文化または宛先不一致を起こした。
入力tokenを減らしても出力token増が上回るため、末尾`to:"{recipient}"`を維持するのが最短安定だった。

### 判定

recipient束縛はこれ以上短縮しない。固定prefix/core側の同時削除へ探索軸を移した。

## r144/r145: `Mail`とschema句点を同時に削り16 tokenへ到達

### 検証内容

r144では6種類の引用符prefixと、`Mail`省略・schema直後の句点削除・終了句3種をN=10で交差した。r145では
通過したstraight/double/plain系をN=100へ昇格し、ordinaryをrun前後へ置いて比較した。

### 詳細

r144で初めて、次のような16-token入力が10/10の`16>4`を維持した。

```text
USE double quotes. body:"",subject:"" Finish without text. to:"{recipient}"
```

r145ではdouble版が100/100・全件`16>4`を維持した。straight版は`16>4` 98件・`17>4` 2件だった。
`Finish without response.`は1件だけ`18>1024`となり、宛先一致も99%へ落ちた。ordinaryは前後を含む3系列が
100/100の`16>4`で15.093〜15.205 raw/s、double 16-token版は15.114 raw/sだった。短run内の絶対速度では
ordinaryを超えないが、完全性を保って入力22→16 tokenを実現した。

### 判定

16-token doubleを本命としてN=500へ昇格する。response/output系は稀な長出力の損失が大きいため棄却する。

## r146/r147: 15-token以下の実用境界を探索

### 検証内容

r146では引用符prefixの句点削除と6終了句を総当たりし、r147ではbody/subject片方の省略、結合記号、2語終了句、
prefix境界を追加してN=10探索した。

### 詳細

16-tokenのstraight `Finish without text.`と`End without text.`は10/10で`16>4`だった。一方、prefix末尾の句点を
削った15-token案は、`straight`で主に`24>4/6`、`double`で`24>4`または`26>4`となった。つまり入力1 token減に対し
初回callが8〜10 token増えた。`body`または`subject`だけにした14〜15-token案、`Finish no text.`、
`textless/wordless`も、長いcall・tool後6 token・不発・宛先不一致のいずれかが混ざった。

### 判定

現在確認できた実用入力下限は16 token、出力下限は`16>4`である。15 token以下はN=10段階で明確に総tokenが悪化し、
大規模測定へ進めない。以後は16-token案の完全性と速度再現性を重点確認する。

## r148/r149: 16-token本命を独立N=500で比較

### 検証内容

r148ではordinary、17-token double、16-token doubleをABCCBA順で各N=500、r149ではordinaryと16-tokenを
別GPUのABBA順で各N=500測定した。

### 詳細

| run | ordinary pooled | 17-token pooled | 16-token pooled | 16-token対ordinary |
|---|---:|---:|---:|---:|
| r148 | 14.9133 | 14.9031 | 14.9086 | -0.032% |
| r149 | 15.0861 | - | 15.0905 | +0.029% |

全系列で得点・cell・宛先一致を維持した。17-tokenは1,000/1,000で`16>4`、16-tokenは各runとも998/1,000が
`16>4`、`EK`だけが両反復で決定論的に`17>4`となった。ordinaryは全件`16>4`だった。

### 判定

16-tokenの速度は2 GPUでordinaryと実質同等であり、入力6 token減のPareto候補として維持する。実行順を逆転した
独立N=500と、N=1,500のrecipient安定性を追加する。

## r150: 16-token終了句をN=100で前後対称比較

### 検証内容

16-tokenのdouble + Finish、double + End、straight + Endをordinaryと比較した。各案を前後反転した8系列、
各N=100で測定した。

### 詳細

| 案 | 完全性 | completion | pooled raw/s |
|---|---:|---|---:|
| ordinary | 200/200 | 全件`16>4` | 約15.092 |
| double + Finish | 200/200 | 全件`16>4` | 約**15.102** |
| double + End | 200/200 | 全件`16>4` | 約15.098 |
| straight + End | 200/200 | `16>4` 196件、`16>6` 2件、`17>4` 2件 | 約15.096 |

全案で得点・cell・宛先一致を維持した。double + Finishはordinary比約+0.07%だが、系列間変動より小さい。

### 判定

出力が完全同形で速度も僅かに上だったdouble + Finishを16-token本命として維持する。double + Endは同等だが更新理由がなく、
straight + Endは長出力が混ざるため昇格しない。N=500を独立GPU・異なる実行順で反復する。

## r151: 実行順反転N=500で16-tokenを再確認

### 検証内容

r149とは反対に16-tokenをrun両端、ordinaryを中央へ置くBAAB順で各N=500測定し、位置ドリフトの影響を確認した。

### 詳細

16-token pooledは14.9843、ordinary pooledは14.9249 raw/sで、候補が約+0.398%だった。両案1,000/1,000で
得点・cell・宛先一致を維持し、16-tokenの`EK`だけが各系列1件ずつ`17>4`だった。
r148/r149/r150/r151の同形系列をすべて合算すると、各3,200件でordinary 14.9816、16-token 15.0009 raw/s、
候補が約+0.129%となった。

### 判定

小さいが再現方向はプラスで、入力6 token減もあるためN=1,500 ABBAへ昇格する。`EK`の長出力はbank置換で解消する。

## r152: 16-token本命のN=1,500安定性

### 検証内容

r88 bank先頭1,500件を16-token本命だけで生成し、短runで見えなかった後半recipientの完全性を確認した。

### 詳細

得点9,000、cell 1,500、宛先一致100%、15.030 raw/sだった。`16>4`は1,498件、`17>4`は`EK`と`LZ`の
2件のみで、全件が正しい1-callを維持した。

### 判定

候補自体は実運用上限N=1,500を完全通過した。長出力2値を、同じpromptで`16>4`確認済みかつ未使用の`CND`・`ARC`へ
交換し、N=1,500を再確認する。

## r153: ordinary対16-tokenをN=1,500 ABBA比較

### 検証内容

ordinaryをrun両端、16-token本命を中央へ置き、各N=1,500で実運用上限の速度を比較した。

### 詳細

ordinary pooledは約14.8725、16-token pooledは約14.8447 raw/sで、候補が約-0.187%だった。両案とも
得点18,000、cell 3,000、宛先一致100%。候補は各系列で`16>4` 1,498件、`17>4` 2件だった。
ただし前半はordinary 14.934対候補14.864、後半は候補14.826対ordinary 14.812となり、時間方向のドリフトがある。
完了直後にVMが失効したため、集計値はstdout JSONを正典とする。

### 判定

単独runでは速度首位を更新しない。実行位置を逆転し、6値交換bankを使うr157 BAABとの合算で判断する。

## r154/r155: recipient交換版16-tokenと17-tokenをN=1,500確認

### 検証内容

r154では`EK→CND`、`LZ→ARC`へ交換した16-token本命、r155では`Mail`を残した17-token doubleを、それぞれ
単独N=1,500で確認した。

### 詳細

| 案 | 得点 / cell / 宛先 | completion | raw/s |
|---|---|---|---:|
| 16-token + 2値交換 | 9,000 / 1,500 / 100% | 全1,500件`16>4` | 14.947 |
| 17-token | 9,000 / 1,500 / 100% | 全1,500件`16>4` | 15.068 |

別GPU・別runなのでraw/sの絶対値は直接比較しない。両案とも実運用上限で完全同形を達成した。

### 判定

16-token交換版は17-token版と同じ完全性で入力をさらに1 token削れるため本命を維持する。17-token版はbank交換を
不要にする安定バックアップとする。

## r156/r158: token編集距離・target NLL・実生成経路を分析

### 検証内容

r156ではordinaryを共通targetとするteacher-forced NLL、token編集距離、8 recipientのgreedy出力を比較した。
r158では`a/EK/LZ/CND/ARC`の実生成token IDを直接取得し、表示上同じcallのtoken数差を調べた。

### 詳細

| 案 | 入力token | ordinaryからの編集距離 | target mean NLL | target平均順位 |
|---|---:|---:|---:|---:|
| ordinary | 22 | 0 | **0.00073** | 1.0 |
| double 17-token | 17 | 7 | 0.01029 | 1.0 |
| double 16-token + Finish | **16** | 8 | 0.00218 | 1.0 |
| double 16-token + End | 16 | 8 | 0.00158 | 1.0 |
| straight 16-token + Finish | 16 | 9 | 0.00264 | 1.0 |

全案が8 recipientで正しいcall文字列を生成した。16-token FinishはordinaryよりNLLが上がるが、17-tokenより低く、
全target tokenが順位1位である。r158では、ordinaryと16-tokenの通常recipientが終端`"}`をtoken ID 25938の1 tokenで
生成する一方、16-tokenの`EK/LZ`だけは`"`（236775）と`}`（236783）の2 tokenに分割していた。表示文字列とparser結果は
同じでも、実生成token数だけ1増えることを直接確認した。交換先`CND/ARC`は25938を使う。

### 判定

`EK/LZ`交換は文字列tokenizeだけでは見えない実生成経路の差を解消している。16-token Finishは低NLL・順位1位を保ち、
短縮による偶発的なcallではない。double EndはNLLが僅かに低いが、r150の実速度でFinishを超えず変更理由がない。

## r159: r88全2,000 recipientの実生成tokenを総当たり

### 検証内容

16-token本命について、r88 bank全2,000値をSDKと同じfull prompt/tool schemaでgreedy生成し、表示文字列の再tokenizeではなく
モデルが実際に選んだtoken ID列を記録した。さらにbank未使用の3文字大文字値から16-token spareを32個収集した。

### 詳細

正しいcall文字列は2,000/2,000。実生成は16 tokenが1,994件、17 tokenが6件だった。6 outlierは次のとおり。

| index | 元recipient | 原因 |
|---:|---|---|
| 265 | `EK` | 終端`"}`が2 token |
| 590 | `LZ` | 同上 |
| 1,583 | `nM` | 同上 |
| 1,647 | `pO` | 同上 |
| 1,777 | `uZ` | 同上 |
| 1,988 | `AFP` | 同上 |

走査した全件で入力は16 token、call先・引数文字列も正しかった。未使用spareでは`ADD/AIS/AKA/AKE`等が
実生成16 tokenかつ正しいcallであることを確認した。全走査は約547秒だった。

### 判定

6値を`CND/ARC/ADD/AIS/AKA/AKE`へ置換すれば、全2,000件の初回callを16 tokenへ揃えられる。実運用上限N=1,500内の
2値交換はr154で全件確認済み。全6値交換bankをr160としてN=2,000で最終確認する。

## r160: 全6値交換版をN=2,000最終確認

### 検証内容

r159で発見した6 outlierを実生成16-token確認済みspareへ交換し、SDKのtool実行・終了generationを含むpublic replayを
全2,000件で実行した。

### 詳細

得点12,000、unique cell 2,000、宛先一致100%、発火2,000/2,000、completionは全2,000件が`16>4`だった。
入力も全件16 tokenで、14.901 raw/s、replay合計805.298秒だった。完了直後にColab VMのファイル領域が失効したため、
集計値はrunnerが終了時に出したstdout JSONを正典とする。

### 判定

完全性とtoken下限の確認は完了した。16-token文と6値交換bankの組合せをtoken Pareto本命とし、ordinaryとの
N=1,500前後反転比較を合算して速度順位を決める。

## r157: 実行順反転N=1,500と正順runの統合判定

### 検証内容

r153とは実行位置を逆転し、16-token案を両端、ordinaryを中央へ置くBAAB順で各N=1,500を測定した。
16-token案には実運用範囲の`EK/LZ`を交換したbankを使用し、全件`16>4`へ揃えた。

### 詳細

| run | 案 | replay合計 | pooled raw/s | completion |
|---|---|---:|---:|---|
| r153 正順 | ordinary | 1,210.290秒 | 14.8725 | 全3,000件`16>4` |
| r153 正順 | 16-token | 1,212.536秒 | 14.8449 | `16>4` 2,996件、`17>4` 4件 |
| r157 逆順 | ordinary | 1,200.766秒 | 14.9904 | 全3,000件`16>4` |
| r157 逆順 | 16-token + 2値交換 | 1,199.913秒 | **15.0011** | 全3,000件`16>4` |
| **r153+r157** | **ordinary** | **2,411.056秒** | **14.9312** | 得点36,000 |
| **r153+r157** | **16-token** | **2,412.449秒** | **14.9226** | 得点36,000 |

N=1,500の正順・逆順を合算すると、16-token案はordinary比-0.058%だった。N=100–500のr148–r151を含む
全測定を合算すると、ordinary 55,200 raw / 3,692.632秒 = 14.9487 raw/s、16-token 55,200 raw /
3,692.377秒 = 14.9497 raw/sで、差は+0.0069%まで縮む。これは速度差がA100の時間ドリフトより小さいことを示す。

既存JSONを回収できたr148–r151の各3,200件について、1候補のreplay時間分布も比較した。

| 案 | min | median | max | mean | p95 | 1%両端除外mean |
|---|---:|---:|---:|---:|---:|---:|
| ordinary | 0.388022秒 | 0.400421秒 | 0.429803秒 | 0.400492秒 | 0.406593秒 | 0.400363秒 |
| 16-token | **0.387337秒** | **0.399426秒** | 0.436295秒 | **0.399978秒** | **0.406168秒** | **0.399825秒** |

16-token案は中央値が約0.995ms、平均が約0.515ms短い一方、最大値は約6.49ms長い。中央値方向では僅かに有利だが、
N=1,500の総時間では逆転する程度の差であり、速度首位の根拠にはしない。r153/r157は完了直後にVMのファイル領域が
失効してper-candidate配列を回収できなかったため、min/median/maxは回収済みの同一prompt・同一モデル3,200件を正典とする。

### 判定

16-token案は入力22→16 token、全2,000件`16>4`という明確なtoken・完全性改善を持つが、速度はordinaryと同等圏で
優位を確定できなかった。実測速度の優先度1はordinaryのまま維持し、16-token + 6値交換版をPareto候補の優先度2とする。
同じ16-tokenでNLLが低い`End without text.`はr161で前後反転比較し、16-token候補内の最終文面だけを決める。

## r161: 16-token `Finish`と`End`の最終比較

### 検証内容

入力token数が同じdouble quote文について、終了句だけを`Finish without text.`と`End without text.`で変え、
Finishを両端、Endを中央に置くABBA順で各N=500を測定した。bankはr160の全6値交換版を共通使用した。

### 詳細

| 案 | 得点 / 宛先 | completion | pooled raw/s | min | median | max |
|---|---|---|---:|---:|---:|---:|
| Finish | 6,000 / 100% | 全1,000件`16>4` | **15.0621** | **0.388552秒** | **0.398108秒** | 0.431763秒 |
| End | 6,000 / 100% | `16>4` 998件、`17>4` 2件 | 15.0513 | 0.392551秒 | 0.398221秒 | **0.426373秒** |

FinishはEnd比+0.0715%で、中央値も約0.113ms短かった。Endの長出力2件はいずれも同じrecipient `FW`で再現し、
得点・宛先は正しいものの、終了`"}`が1 token増えた。最大値だけはEndが短いが、総時間と中央値はFinishが上回る。

### 判定

16-token候補の終了句は`Finish without text.`に確定する。EndはNLL上僅かに良くても実測速度を更新せず、
出力tokenにも決定論的な外れ値があるため採用しない。

## r162–r164b: tool引数値・末尾triggerによる即EOS探索

### 検証内容

現在のGemmaは正しい16-token call後に4-tokenの短いwrap-upを生成する。この4 tokenを0へできれば、入力を数token増やしても
総量を減らせる可能性がある。そこで、思いつきの単語だけを試すのではなく、実tokenizerの全語彙を静的解析し、特殊token、
記号token、終了意味に近いsemantic pool、現状のpost-tool次token上位を統合して候補を選んだ。

- r162: `subject` / `body`の値へ候補を入れ、正しいtool call後のEOS順位を測定
- r163b: `Finish`直前、`to`直前、`Finish`置換の3位置へ上位2,000 token片を挿入
- r164b: r163b上位24片を順序付きpairと5配置で交差し、単語間相互作用を確認

いずれも生成を多数回試すのではなく、正しいcallを履歴へteacher-forceしたpost-tool状態のlogitsを直接測る。入力増加は
tokenizer実測で最大2 token（pairは3 token）へ制限した。

### 詳細

r162は10,500超の有効な値・field組合せを評価した。上位は次の通りで、EOS 1位はなかった。

| field / 値 | call増 | message増 | EOS順位 | EOS logp |
|---|---:|---:|---:|---:|
| subject=`<tool_response|>` | +2 | +2 | **2** | -12.7693 |
| subject=`<|think|>` | +2 | +2 | 3 | -12.8729 |
| body=`<tool_response|>` | +2 | +2 | **2** | -13.0185 |
| subject=` EM` | +2 | +2 | **2** | -13.3916 |
| subject=`,...` | +1 | +1 | **2** | -13.4221 |

r163bでは全262,144 tokenから260,682個の表示可能な一意片を復号し、特殊6,403、記号7,099、semantic 4,000、
現状logit上位1,966を統合して2,000片を選んだ。3位置で6,000案を組んだ後、追加token上限を満たす327案を実モデルで
評価した。保存上位400件内の順位分布は2位144、3位82、4位60、5位34、その他7で、**1位は0件**だった。

| 値 / 位置 | 入力増 | EOS順位 | EOS logp | top token |
|---|---:|---:|---:|---|
| `<|think|>` / `to`直前 | +2 | **2** | **-11.4522** | id 100 |
| `<tool_response|>` / `to`直前 | +2 | 3 | -11.8423 | id 100 |
| `<|think|>` / `Finish`直前 | +2 | **2** | -12.1807 | id 100 |
| `<tool_response|>` / `Finish`直前 | +2 | **2** | -12.4778 | id 100 |
| `>;</` / `Finish`置換 | **+1** | **2** | -13.2863 | id 100 |

順位2位でもtopとの差は最良で-11.452 logitsと大きく、greedy decodeでは停止しない。したがって、入力やcallへ1–2 token
増やす単体案は4-token wrap-upを削れず、速度上は純損失になる。

r164bではr163b上位24片の順序付きpairを、`Finish`直前・`to`直前・終了句置換・2分割配置の計5 layoutで交差した。
全2,880案のうち入力増3 token以内の1,577案を実モデルで評価したが、**EOS 1位は再び0件**だった。最良は
`<tool_response|>`+`\"></`を`to`直前へ置く19-token文でEOS 2位、logp=-9.5269だった。単体最良よりEOS logpは
約1.93改善したものの、top token id 100との差はなお-9.5268 logitsあり、greedy decodeを停止へ反転できない。

### 判定

**値・単一末尾片・上位片pairによる即EOS化は棄却する。** 全語彙を距離・token種別・現状logitから選別し、さらに
上位24片の順序付きpairと5配置まで交差してもEOS 1位は0件だった。入力を16→19 tokenへ増やしても4-token wrap-upは
消えないため、このpost-tool終了hack軸は終了する。16 input / `16>4`をGemmaの実用的な生成床として維持する。

## 生データ

- `benchmarks/scripts/colab_a100/results/gemma_r001_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r002_n100.json`
- `benchmarks/scripts/colab_a100/results/gemma_r123a_case_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r123b_layout_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r123c_tail_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r124_pool_n100.json`
- `benchmarks/scripts/colab_a100/results/gemma_r125_straight_n100.json`
- `benchmarks/scripts/colab_a100/results/gemma_r126_case_n100.json`
- `benchmarks/scripts/colab_a100/results/gemma_r127_quote_token_probe.json`
- `benchmarks/scripts/colab_a100/results/gemma_r127b_quote_token_nll.json`
- `benchmarks/scripts/colab_a100/results/gemma_r128_prefix_sweep.json`
- `benchmarks/scripts/colab_a100/results/gemma_r130_tail_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r132_finish_neighbors_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r133_prefix_finish_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r134_core_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r135_finish_quotes_n100.json`
- `benchmarks/scripts/colab_a100/results/gemma_r136_short_core_n100.json`
- `benchmarks/scripts/colab_a100/results/gemma_r137_tail_finalists_n100.json`
- `benchmarks/scripts/colab_a100/results/gemma_r138_prefix_core_cross_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r139_prefix_core_n100.json`
- `benchmarks/scripts/colab_a100/results/gemma_r140_response_n500.json`
- `benchmarks/scripts/colab_a100/results/gemma_r141_no_schema_dot_n500.json`
- `benchmarks/scripts/colab_a100/results/gemma_r143_recipient_binding_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r144_compaction_cross_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r146_compact_frontier_n10.json`
- `benchmarks/scripts/colab_a100/results/gemma_r148_compact_n500.json`
- `benchmarks/scripts/colab_a100/results/gemma_r149_compact_repeat_n500.json`
- `benchmarks/scripts/colab_a100/results/gemma_r150_tail_n100.json`
- `benchmarks/scripts/colab_a100/results/gemma_r151_compact_reverse_n500.json`
- `benchmarks/scripts/colab_a100/results/gemma_r152_compact_n1500.json`
- `benchmarks/scripts/colab_a100/results/gemma_r154_compact_replaced_n1500.json`
- `benchmarks/scripts/colab_a100/results/gemma_r155_double17_n1500.json`
- `benchmarks/scripts/colab_a100/results/gemma_r156_compact_token_nll.json`
- `benchmarks/scripts/colab_a100/results/gemma_r158_generated_token_paths.json`
- `benchmarks/scripts/colab_a100/results/gemma_r159_recipient_token_scan.json`
- `benchmarks/scripts/colab_a100/results/gemma_r161_finish_end_n500.json`
- `benchmarks/scripts/colab_a100/results/gemma_r163b_tail_trigger_sweep.json`
- `benchmarks/scripts/colab_a100/results/gemma_r164b_tail_trigger_pairs.json`

r129、r131、r125 N=1,500、r142、r145、r147、r153、r157、r160はColab runtimeが完了直後に失効したため、生JSONは回収できず
CLI stdout集計を本文へ記録した。
