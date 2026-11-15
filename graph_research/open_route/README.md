# 採点済みの提出との比較と、実回路のグラフ

確認できた提出のベストは **Public 27.31512**。2026-11-15 02:27 UTC にComplete、同日02:27 UTCに選択済みを画面で確認した記録。該当する実行のローカル値は27.31511。今回の作業からのKaggle提出は0件。[提出ノートブックの版](https://www.kaggle.com/code/geocpuresearch/qcc-v27-4030-toffoli-coded-word-chemistry?scriptVersionId=369721985)

| 回路 | ANGLE片道Toffoli | 化学費用 | 確認したスコア |
|---|---:|---:|---:|
| Public 27.31512 の提出 | 4,030 | 294,888,332.104263 | Public 27.31512、対応するローカル27.31511 |
| 同じ提出のANGLEだけにグラフ順序を適用 | 4,030 | 294,888,332.104263 | 化学費用に差なし |
| 任意入力XORを満たす閉路版 | 4,323 | 306,625,698.929146 | ローカル26.97458917 |
| 任意入力XORを満たす開路版 | **4,290** | **305,303,691.081660** | **ローカル27.01346769** |

元の高得点回路に直接適用した実験では、命令数609,579→306,105、公式78,080ショットPASS。減ったのは採点されない線形命令。[ビルドとKMBハッシュ](public_baseline/build_receipt.json)・[公式化学結果](public_baseline/graph_verifier.json)。

27.31512版の第2ローダーは任意の初期語に対する文書のXOR定義に反例があるscore11と同じKMB。Kaggleが実際に採点した27.31512と、そのXOR反例は両立する。他チームの提出を検査した結論ではない。任意入力を満たす開路版では再生成などで片道の支払いが260増え、公開済みの高得点回路と比べると費用が上がる。26.19960424は任意入力XORを満たす四語の別回路を用いた研究比較値で、アカウントの点数とは別。[反例](../gemini/chemistry/arbitrary_tag_witness.json)・[形式仕様](https://github.com/Inzainos/quantum-circuit-compilation/blob/4277c767440df9efb8a90860ae2ce47028e46ba9/verifiers/dfthcsos/scoreinfra/circuits.py#L8-L16)

## 開路探索と図

ノードを同時に省く2特徴量の組、辺をHMRとCZで消去してCCXで特徴量を再生成できる遷移とする。始点には初期化を省ける組、終点には最後の消去が安全な組を使う。終点でそのまま片付けられるので、初期配置への復帰費用を省ける。[開路の合成・比較](open_route.md)

- [KMBから照合した全10グループの経路と実際の命令図](visual/README.md)
- [全15本のグラフ往復でKMBがバイト一致した確認](circuit_graph_receipt.json)
- [全命令を持つANGLE_13グラフ](angle_k_13.graph.json.gz) と [往復変換コード](circuit_graph.py)
- [任意40入力ビットの証明](final_proof.json)・[公式78,080ショットPASS](final_verifier.json)・[完全ZIPのハッシュと費用](score14_scorecard.json)

グラフの量子線の辺は同じ量子線に連続して触れる命令間、古典線の辺は測定結果の生成、判定、再代入の順序を記録する。命令の元の位相と順序を維持して再出力する。

```sh
python circuit_graph.py export /path/to/dfthcsos build-graphs --publish-batch 13
python circuit_graph.py restore angle_k_13.graph.json.gz replayed.kmb
```

## 採点と提出枠

Kaggleの大会説明では、提出の採点は約45分。アカウント画面で最後に記録した提出枠は2026-11-15 02:42 UTCの「0件、1日5件を使用、リセットまで21時間」。現在の残り枠は未確認。[大会ページ](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation)
