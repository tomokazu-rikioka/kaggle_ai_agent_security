# 実験スコア一覧

> このファイルは直接編集して運用する（スコアの単一ソース）。
> - `local_*` 列: `/update-score <exp>` スキルが `make eval` 回収の `experiments/<exp>/scores.json` から記入（`gpt_oss > gemma_4` 優先）。`local_agent` は採用モデル名。
> - `lb_public` 列・`changes` 列: 直接記入する（または Claude に依頼）。
> - `local_public` が公開 LB と相関、`local_private` は非公開汎化の代理。
> - 旧 `local_strict` 列は 2026-07 に eval から撤去（strict は fs.read 無検査バグに overfit する信号のため）。過去の strict 実測値は下表 changes 列の史実記述に温存。`local_provenance` は `local_private` に改称（同一の永続来歴ガードレール）。
> - 2026-07-16 の再編で実験を exp001〜exp003 の3本に集約（全て N=300・K=1・M=1 に統一）。旧 exp004〜exp012 の知見は `docs/analysis/2026-07-attack-findings.md` に蒸留。旧番号 → 新番号: 旧exp001→exp001 / 旧exp003→exp002 / 旧exp009→exp003。

## 実験一覧

| exp | local_agent | local_public | local_private | lb_public | changes |
|-----|------------|------|------|------|---------|
| exp001 | gemma_4 | 17.790 | 4.290 | 17.850 | EXFIL(marker)+DEPUTY ブレンド(命令形)・`EXFIL_FRACTION=0.5`・N=300/K=1/M=1。理論18.0と一致し N 線形を確立。**public LB=17.850 でローカル(17.790)の信頼性を裏付け**。ブレンド型として多様性に貢献 |
| exp002 | gemma_4 | 8.730 | 8.730 | - | 純DEPUTY疑問形・`EXFIL_FRACTION=0.0`・N=300/K=1/M=1。"Could you notify…?" で fire率97.0%（291/300）。**全GR共通の最良単発ベースライン＝非公開本命**。他手法の比較基準（旧exp003） |
| exp003 | gemma_4 | 27.000 | 0.000 | - | 純EXFIL(marker)・`EXFIL_FRACTION=1.0`・N=300/K=1/M=1。300/300発火でpublic=27.0（marker EXFILの理論上限）。private=0（block≡fire）。public特化ヘッジ（旧exp009） |
