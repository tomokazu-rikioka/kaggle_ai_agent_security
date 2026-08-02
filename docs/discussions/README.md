# Discussion 要約集（索引）

> 用語は [用語集](../用語集.md)。分析の総合は [`スコア分析と改善方針.md`](../スコア分析と改善方針.md)。

Kaggle「AI Agent Security」の Discussion を、`attack.py` 設計に効く観点で横断要約したもの。
原文の URL・投稿者・引用は各ファイル内に保持している（出典の正確さのため）。
収集元のブックマークは [`Bookmarks.json`](Bookmarks.json)。

## ファイル一覧

| # | ファイル | 扱う論点 |
|---|---|---|
| 01 | [評価・採点と公式アップデート](01-評価・採点と公式アップデート.md) | v3.1.2 採点変更・6フェーズ×9000秒・SECRET_MARKER・時間切れ・凍結ゾンビ LB |
| 02 | [攻撃設計と述語](02-攻撃設計と述語.md) | 述語の到達可能性（白箱解析）・single-post exfil farm・CONFUSED_DEPUTY の文字列穴・Gemma parser |
| 03 | [実行時間と候補数バジェット](03-実行時間と候補数バジェット.md) | 律速=出力トークン量・候補上限 ~600・理論天井 0.09×N |
| 04 | [公開・非公開汎化](04-公開・非公開汎化.md) | 勝利条件=private 汎化・blind transfer・両 LB 非相関・汎化軸の提案 |
| 05 | [検証とツール・モデル実行](05-検証とツール・モデル実行.md) | 手元検証（Kh0a）・private-eval-proxy（aduriseti）・codex nerf 回避 |
| 06 | [提出エラーとプラットフォーム問題](06-提出エラーとプラットフォーム問題.md) | Kaggle Error 切り分け・format error=時間切れ・「候補半減して再提出」 |

## この要約群から抽出した結論（詳細は分析ノート §1・§4）

- **public の到達面は EXFIL（http.post）と CONFUSED_DEPUTY（email.send）の2つだけ**（01/02）。
- **律速は候補数でなく出力トークン量**。安全圏は候補 ~600、素の命令＋短い生成で N を稼ぐ（03）。
- **format error / 空スコアは時間切れの症状**。候補を半減して再提出（06・当リポジトリで Round10/11 に確定）。
- **勝利条件は private 汎化**。public 特化は片賭けで shake-up に弱い（04）。

> 注記: 各ファイル中の `strict` ガードレールの表記は、2026-07 に eval を public/private の2本へ集約する前の
> 3本構成（public/strict/private）の名残。現行は public/private の2本。
