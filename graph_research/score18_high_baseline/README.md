# 最高ローカル版からの採点改善と依存グラフ

基準はscore12のローカル27.327844992124593。ZIPのSHA-256は
`a339f391056756c72a9f3a994090d509d3bf38ebee94a075a6d68fe13f2bffea`。
元の15本のANGLE、DQI、invsqrtはバイト一致。化学NPZのWとH2_Iの二配列のみ変えた。
公式化学検証器で78,080ショットPASS。化学費用は294,887,871.6772202から
294,878,855.8279802へ下がり、総合点は**27.328123503355716**。
18ファイルのZIPと全ハッシュを再読出しして照合した。
Kaggleへの提出は0件。

係数は公開Heliosli v56由来のNPZで同じ角度回路がPASSすることを確認してから、
公式の誤差・ギャップ制約で再最適化した。増分の大半は公開初期値から来る。
再最適化の前後の化学費用は294,878,860.57649696と294,878,855.8279802。
ノートブック、元データ、Apache-2.0の出典は [化学の記録](chemistry/README.md)。
任意の初期ANGLE出力についての元の反例はそのまま残る。
ここで報告するのは同じ公式検証器で得たローカル値。
[スコア表](score18_scorecard.json)・[公式化学検証出力](chemistry/public_metric_official_verify.json)。

## グラフが扱う採点項目

逆平方根の採点は、最大量子ビット数とToffoli相当費用の積。
23,881命令の量子・古典依存を有向グラフにし、条件分岐を一つの頂点へまとめても
残る必須生存区間を調べた。作業値を作る頂点が切断点に先行し、消去する頂点が
切断点より後続するなら、その切断点の直後で値を保持する必要がある。
最初のボトルネックでは22入力と24作業値が同時に必要になった。
この依存関係を保つ並べ替えだけでは幅46から下がらない。

回路自体も変形した。一時ANDの前後をアフィン写像として表し、出力
`A x + v (x_a AND x_b)` を分離する。Aが可逆で、`A^{-1} v` が
元の二つの入力制御を変えない場合、積をデータ線へ直接足してからAを適用できる。
この変形と不要になった測定補正の相殺まで4区間で証明し、最初の幅ピークの一時値を消した。
実回路で全3,133,452入力を各1ショット検証してPASS。
後続のピークが残るため最大幅46と課金対象のゲート数は同じで、
採点用ポートフォリオには採用しなかった。
[依存グラフ](invsqrt_graph/width_dag.json)・[変換と証明](invsqrt_graph/product_transfer.json)・
[全入力1ショットの結果](invsqrt_graph/transfer_full_domain_one_shot.json)。

化学で現在のT・Qと他2課題の費用を固定すると、正規化の数式から係数調整の上限は27.35186423未満。
この条件下で28に進むには採点される回路資源を減らす必要がある。
[採点コードからの導出](chemistry/README.md)・[数値定数と範囲](chemistry/normalization_bound.json)。

## 再現

```sh
python chemistry/stage.py "$SCORE12_ZIP" "$SCORE12_JSON" chemistry/public_weights_xor_patch.npz family --xor-patch
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$VERIFIERS/dfthcsos/verify.py" family > verified.json
python build_portfolio.py --zip "$SCORE12_ZIP" --scorecard "$SCORE12_JSON" --family family --chemistry-receipt verified.json --out local.zip --receipt scorecard.json
python invsqrt_graph/width_dag.py "$PINNED_INVSQRT_KMB" width.json
python invsqrt_graph/product_transfer.py "$PINNED_INVSQRT_KMB" transfers.json --candidate transfer.kmb
python "$VERIFIERS/invsqrt/verify_submission_invsqrt.py" transfer.kmb --shots-per-x 1 --batch-size 511
```

[同じ最高版でのDQIの追加検査](dqi/README.md)と
[逆平方根での測定補正の追加検査](invsqrt_search/README.md)も保存している。
