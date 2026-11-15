# 2026-11-15: 実提出と特殊対称性の検査

## 実際に提出した候補

2本とも Kaggle の Submit to Competition から提出し、新しい Pending 行を確認した。Notebook の保存だけで終了していない。公開スコアは採点完了前なので未確定。

| 候補 | Notebook version | ZIP SHA256の先頭 | 内容 |
|---|---:|---|---|
| GVQCC 821 score2 verified | 369715705 | dfacbef6 | DQI821 + e46 + 20語を更新した化学テーブルと対応する15ローダー |
| GVQCC exact4096 gauge score2 | 369719696 | 1807d6ae | DQIを9a82に更新し、他17メンバーを上記のZIPから保持 |

数値は Notebook の scriptVersionId であり、competition submission ID ではない。最終UI確認は2026-11-15 01:40:39 UTC（日本時間10:40:39）で、2件ともPendingだった。

提出の観測時刻・状態は [score2 receipt](kaggle_score2_submission_369715705.json) と [score3 receipt](kaggle_score3_submission_369719696.json) に記録する。

## スコア改善に結びつく対称性

DQIの残差ラベルの共通シフトと対応する位相補償を使い、4,096ラベル全部からゼロマスクが最多となる表現を選択する。選択器は古典ビットで計算する。量子側には必要なシフト、位相補償、復元をすべて含めた。

新しい9a82候補の公式ローカル検証は102,400 shotsでPASS、値・位相エラーとも0。Q=889、平均Toffoli=382095.68779296876、反復係数=1.1912604648115832。既存e986記録より平均約19.88個、821の既存比較記録より約504.31個少ない。比較する入力サンプルは同一ではなく、公開スコアの改善値ではない。

[独立した全検証](../../score3_full_20261115_verification.json) / [比較と制約](../../score3_full_20261115_comparison.json) / [再現するKaggle worker](../../score3_submit_worker.py)

## さらに削るために実行した検査

- **実DQI821のパターン照合:** GF(2^12)の42-CCXカーネル3,823件、GF(2^24)の99-CCXカーネル1,376件。命令と全operandを単射的なwire置換で照合した。以前の78→54という一般的な見積もりは、この実体の最適化根拠には使えない。
- **共役・線形基底変換:** 実際に共役対称性がありCX配線を短縮できるが、この変換だけではCCX数やQは減らない。
- **共有入力を持つ乗算の融合:** 隣接する193窓を確認。重複なしで同時に置換できるのは141窓。独立した2出力を含む84積のテンソルを探索したが、この予算では83以下を得なかった。
- **異なる乗算器の初期構成:** GF4上の混合次数補間から42積の20構成を生成。既存GF8構成と異なる因子集合であることを線形不変量で確認し、全20構成から400経路・4億stepを105.73秒で探索した。最良42のままで41積は未発見。初期構成と探索結果の全144基底対を独立に検査した。[構成と探索の記録](../../symmetry_dqi_mixed42_20261115_report.md)
- **化学の符号対称性:** 1,220行すべてで5タグを同時にゼロにできることをGF(2)方程式で構成。ベクトルの全体符号を除く差は数値丸めの範囲。汎用QROMに再合成すると片道4,033→18,270 Toffoliへ増えるため、この候補は採用しない。既存の非線形キャッシュを保持する合成が必要。
- **入力間の特殊関係:** 平方の線形化、共役norm、定数倍の専用化は参照ソース内で実装済み。AST269呼出しで同一operand式は0件。これはsemantic aliasや全到達経路を網羅した最適性証明ではない。

[実回路の照合・共有積探索](../../symmetry_dqi_20261115_report.md) / [化学gaugeとコスト検査](../../symmetry_chemistry_20261115_report.md) / [平方・共役入力の追加検査](../../symmetry_dqi_20261115_correlated_operands.md)

## 関連する一次文献

- Vandaele, *Quantum binary field multiplication with subquadratic Toffoli gate count and low space-time cost*: https://arxiv.org/abs/2501.16136
- Meuli et al., *The Role of Multiplicative Complexity in Compiling Low T-count Oracle Circuits*: https://arxiv.org/abs/1908.01609
- Ruiz et al., *Quantum Circuit Optimization with AlphaTensor*: https://arxiv.org/abs/2402.14396
- Gidney, *Halving the cost of quantum addition*: https://arxiv.org/abs/1709.06648

有限の探索で削減案が見つからなかったことは、全回路の大域的最適性を意味しない。基底変換で同値なテンソルの最小rankも変わらないため、異なる分解、複数出力の同時合成、実際の入力制約を区別して探索する。
