# 参照実装 — 実績のある attack.py

`experiments/exp001–080` を削除する際に退避した 3 本。
アルゴリズムの解説は [../07-エンジン系統と参照実装.md](../07-エンジン系統と参照実装.md)。

| ファイル | 由来 | 実績 | 位置づけ |
|---|---|---|---|
| [`champion_exp028_attack.py`](champion_exp028_attack.py) | exp028 | **LB 90.990** | 歴代最高。純 throughput 単発 + cap 0.995 |
| [`champion_exp073_attack.py`](champion_exp073_attack.py) | exp073 | **LB 89.820** | Round13 best。同エンジンの cap 0.993 版 |
| [`deputy_exp040_attack.py`](deputy_exp040_attack.py) | exp040 | LB 20.780（public） | **private で得点できる唯一のベクトル**（`email.send` の CONFUSED_DEPUTY） |

## 使い方

これらは**そのまま `experiments/expNNN/attack.py` として使える**（単一ファイル自己完結・
兄弟 import なし・クラス名 `AttackAlgorithm` 固定）。

```bash
make new-exp NAME=exp081
cp docs/knowledges/reference/champion_exp028_attack.py experiments/exp081/attack.py
# 冒頭の docstring と定数を書き換えてから
make eval EXP=exp081      # 手元採点（Kaggle GPU）
make submit EXP=exp081    # push（LB 提出はしない）
```

## champion の全変種は定数 2 つで復元できる

`champion_exp028_attack.py` の**エンジン本体は 1 バイトも変えず**、
冒頭の `REPLAY_SAFE_FRAC` と `PROBE_REPS` を差し替えるだけで過去の全ドローが再現できる。

```python
PROBE_REPS = 4                # 各テンプレの試し打ち回数
REPLAY_SAFE_FRAC = 0.995      # リプレイ予算をどこまで攻めるか（cap）
```

| cap | probe | 実験と live LB |
|---|---|---|
| 0.997 | 2 | exp034=89.730 / exp055=90.405 / exp056–058=VOID |
| 0.9965 | 1 | exp045=87.705 |
| 0.996 | 2 | exp044=89.010 / exp054=83.655 |
| 0.996 | 4 | exp043=VOID |
| **0.995** | **4** | **exp028=90.990** / exp039=89.595 / exp051=88.830 / exp076=88.155 / exp042=86.805 / exp053=85.185 / exp052・059・060・071=VOID |
| 0.995 | 2 | exp072=77.895 |
| **0.993** | **2** | **exp073=89.820** / exp080=86.805 |
| 0.99 | 2 | exp062=89.370 / exp079=88.065 / exp074=VOID |
| 0.99 | 4 | exp061=87.075 |
| 0.985 | 2 | exp063=86.940 / exp075=VOID |
| 0.98 | 4 | exp064=86.940 |
| 0.98 | 2 | exp065=86.310 |

> **cap を下げても VOID は防げない**（0.985 でも VOID した）。
> 完走時の期待値が最も高いのは **cap 0.99–0.993**。
> 詳細は [../05-VOIDと提出運用.md](../05-VOIDと提出運用.md)。

## 削除した実験を復元するには

```bash
git show 9e0c3fe:experiments/exp055/attack.py > /tmp/exp055_attack.py
git show 9e0c3fe:experiments/exp077/notes.md          # v15 移植の設計メモ
git ls-tree --name-only 9e0c3fe experiments/          # 全 exp の一覧
```

`scores.json` と `submission.ipynb` は `.gitignore` されていたので履歴に無い
（前者は `make eval` の再実行、後者は `make build` で再生成できる）。
