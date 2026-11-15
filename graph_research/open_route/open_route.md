# 始点と終点を分離した作業線グラフ

従来版は二つの特徴量をキャッシュから外し、経路の最後には初期の二つを再び外してから作業線を元の配置に戻していた。新しい合成器は初期と末尾で無視できる作業線の組を別々に求める。各バッチに332個の終点候補がある。終点では、すでに外れている特徴量に対応する測定と補正を省略し、残る作業線の測定・補正を実際の量子ビット配置へ直接写像する。

- 頂点は外した特徴量の組。各頂点が実行できる積と線形補正をビット集合で保持する。
- 辺は、両端で保持する特徴量から交換時の消去と再生成の制御を取れる場合に生成する。重みは再生成のCCX数。
- 初期化が可能な複数頂点をビームの始点にする。状態は現在頂点と未処理項集合。未処理項をすべて消化した時点で、末尾の消去を実行できる終点までの最小費用も比較する。

第1ローダーでは、初期に論理作業線82と83を外し、末尾では115と120を外して完了する。再生成は以前の採用版31回から28回に減った。

| 指標 | 始点へ戻る経路 | 開路・幅24を加えた版 | 開路・幅80も加えた採用版 |
|---|---:|---:|---:|
| ANGLE全15本、片道CCX | 4,323 | 4,302 | 4,290 |
| 化学全体のToffoli | 15,308 | 15,266 | 15,242 |
| 最大ローダー量子ビット | 128 | 128 | 128 |
| 化学費用 | 306,625,698.92914605 | 305,784,421.20801824 | 305,303,691.0816595 |
| 公式検証ショット | 78,080 PASS | 78,080 PASS | 78,080 PASS |

最終候補は各バッチで `閉路・ビーム幅6 → 閉路・幅24 → 開路・幅24 → 開路・幅80` の順に候補を並べ、CCXが最少の候補を採用した。同点はこの順の最初。第0ローダーと係数ファイルは各候補で同じ。採用された15本すべてについて、全1,220アドレスに対する任意40ビットのXOR、選択の保存、作業ビットの消去、測定に依存する位相の相殺を保存後のKMBで証明した。

## 再現

`EXACT` は前段の厳密XOR合成器のディレクトリ。`SOURCE` はその合成に使った元の15本と係数ファイル。`REPO` は前段合成器のリポジトリ依存ライブラリ。`SCHEDULER` はその `algorithm_rework/chemistry`。`WORDS` は同じ角度表のNumpyファイル。`VERIFIERS` はコンペの検証データのディレクトリを指す。

```sh
python "$EXACT/leaf_census.py" "$SOURCE" > leaves.json
python "$EXACT/feature_cache.py" --source "$SOURCE" --output beam6 \
  --repo "$REPO" --scheduler "$SCHEDULER" --leaf-census leaves.json --beam 6
python "$EXACT/feature_cache.py" --source "$SOURCE" --output beam24 \
  --repo "$REPO" --scheduler "$SCHEDULER" --leaf-census leaves.json --beam 24
python open_cache.py --source "$SOURCE" --output open24 \
  --repo "$REPO" --scheduler "$SCHEDULER" --leaf-census leaves.json --beam 24
python open_cache.py --source "$SOURCE" --output open80 \
  --repo "$REPO" --scheduler "$SCHEDULER" --leaf-census leaves.json --beam 80
python "$EXACT/select_cache.py" --variants beam6 beam24 open24 open80 --out verified_family
python "$EXACT/prove_cache.py" verified_family "$WORDS" --out final_proof.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$VERIFIERS/dfthcsos/verify.py" \
  verified_family > final_verifier.json
```

公式化学ダイジェスト `ac0140956847ed5b5429fa9151fb8803cf63c7d55c19c4664d326d3dafd82d1b`。DQIとinvsqrtを同じバイナリで評価した場合のローカル総合点は **27.013467688678**。Kaggleの提出スコアはこの検証に含まない。
