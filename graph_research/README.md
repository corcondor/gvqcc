# グラフで探索し、実回路で判定した結果

採用となるローカル総合点は **27.327844644007193 → 27.327844992124593**。化学費用は **294887882.9465613 → 294887871.6772202**。変更していない化学検証器で78,080ショットPASS。DQI・invsqrtはscore11とバイト一致し、それぞれ以前の費用を使用した。採点差の原因は化学の係数再最適化。Kaggleには未提出。

| 実験 | 実測または検証した範囲 | 採用 |
|---|---|---|
| ANGLEのシュタイナー点＋経路探索 | 15本、307,634→306,105命令。4,030 Toffoli/片道、Q128のまま。公式検証78,080ショットPASS。 | 命令削減を採用。採点費用への寄与ゼロ |
| ANGLEの階数2支持超グラフ | 17区間、244,179低平面から4,108個の積。5項、6項結合を含む。各成分の出力方向独立。 | 探索範囲でToffoli削減ゼロ |
| DQIの生存区間 | e4の58,868,734命令。固定タイムラインの区間除去モデルで、889→888には最低3区間、889→857には最低4,935区間。 | 回路変換の証明は未成立 |
| DQIの1ビット条件で積を分割 | 消費型積を24→23追加量子ビット、99→121 Toffoli。現行の戻し計算を含めると24追加量子ビット、459→481 Toffoli。 | 部品合格、全体採用なし |
| invsqrtの時間展開した位相探索 | 115候補で内部HMR位相差を複数時点で回収。外側条件の合成位相が各1件残る。 | Toffoli削減ゼロ |
| 勾配ブースティングで探索順を選択 | 15バッチを分離した5分割、418経路候補集合。貪欲経路に対しMST優先429命令削減、学習モデルによる1候補選択210削減。 | 学習による優先順位は不採用 |
| 化学係数の再最適化＋新ANGLE | 306,105命令の回路で `W` と `H2_I` だけを変更。化学費用 −11.2693411。 | score12候補採用 |

## シュタイナー点と係数の再現

各頂点を固定した二本のピボットに載せる順序付きパリティと、出力のファンアウト状態で表す。GF(2)での行差分をCXで更新するコストを実ゲートで数える。投影されたパリティ座標を使ったハミング計量でMSTを作り、三頂点のビットごとの多数決を補助点として挿入する。木から得た順序について、実コストで二通りの制御順序を動的計画法で選び、2-optで順序を改善する。元の合成と候補の短い方を採り、各区間のアフィン写像と出力方向つき積の多重集合を比較した。シュタイナー木そのものの最適性は主張しない。

- [シュタイナー合成](steiner/graph_schedule.py)・[経路と再読出し記録](steiner/build_receipt.json)・[公式検証](steiner/full_verifier.json)
- [階数2の商空間](angle_nonlinear/README.md)・[検証された結果](angle_nonlinear/result_certified.json)
- [DQIの区間カットと1ビット条件](dqi/README.md)
- [invsqrtの時間展開](invsqrt/README.md)
- [係数デフォルト検証](score12/official_verify.json)・[全18ファイルのスコア表とハッシュ](score12/score12_scorecard.json)

```sh
python steiner/graph_schedule.py --repo <repo-root> \
  --implementation <repo-root>/algorithm_rework/chemistry \
  --source <score11-dfthcsos> --previous <algorithm-rework-angle-family> --out graph-family
python score12/stage_weights.py --source graph-family \
  --optimized score12/verified_weights.npz --output score12-family
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python <verifiers>/dfthcsos/verify.py score12-family > verify.json
python score12/build_portfolio.py --zip <score11-zip> --scorecard <score11-json> \
  --family score12-family --chemistry-receipt verify.json --out score12.zip --receipt score12.json
```

ANGLE合成は同じKickMixと旧ソースから各KMBのSHAを比較できる。score12のW/H2_Iパッチを適用し、元の検証済みNPZとバイト一致することを確認した。最適化からやり直す場合は、score11の実回路から復元した角度表を入れた最適化用NPZから、近接SQPを `--tight --schur --seconds 66` で再開する。終了時刻で停止するため完全同一の配列にはパッチを使う。

## XGBoostの使いどころとC++からの接続

XGBoostは探索候補の優先順位付けに使える。ラベルは近似成功率だけではなく、実コンパイルの費用減少と検証にかかった時間を記録する。候補の採否には、同値性や位相の検証、実ゲート数、必要に応じた公式検証を使用する。学習用と検証用の回路群を分離し、同じ計算予算で決め打ち、ランダム、学習優先を比較する。成功例のないToffoli削減ラベルで学習したとは主張しない。

今回実行したのはscikit-learnのヒストグラム勾配ブースティング。XGBoost本体はこの環境に入っていない。実データと再現コードを保存した。[コード](steiner/boost_priority.py)、[バッチ分離結果](steiner/boost_result.json)。

実用の構成は、Pythonで学習して `save_model("priority.ubj")`、C++で `<xgboost/c_api.h>` と `libxgboost` を使い、`XGBoosterCreate`、`XGBoosterLoadModel`、`XGBoosterPredictFromDMatrix` または `XGBoosterPredictFromDense` でまとめて推論する。C++からの推論にPythonインタプリタを埋め込む必要はない。Python側からC++探索器を呼びたい構成では、別途pybind11等で探索器を公開できる。今回はネイティブXGBoost接続を実行していない。

一次資料：[Kissinger–Meijer-van de Griend](https://arxiv.org/abs/1904.00633)（物理接続グラフのSteiner木。本実験はパリティ状態のグラフ）、[Chen–Guestrin](https://arxiv.org/abs/1603.02754)、[XGBoost公式C API](https://xgboost.readthedocs.io/en/stable/c.html)、[公式推論例](https://xgboost.readthedocs.io/en/stable/dev/inference_8c-example.html)。
