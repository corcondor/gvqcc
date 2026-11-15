# DQI：2つの古典gaugeチャートを比較する実装

## 変更の要点

現在の全4096ラベル探索を維持し、異なる69個の固定零点を持つ第2チャートを追加した。両チャートの最大頻度を正確に数え、より多くの位相maskをゼロにする方を入力ごとに選ぶ。選択は入力の古典maskだけを読む。量子syndromeへの補償は古典制御のCZで行う。

この方法は、固定されたXOR–AND局所窓の書き換えではない。位相oracleが持つsyndrome gaugeの自由度と、古典制御による位相演算の省略を使う。量子デコーダ本体、既存の誤り訂正入力領域、量子幅889は維持する。

新候補は `/workspace/scratch/3815fb5fae06/score8_dqi_twochart/dqi.kmb`。

- SHA-256：`1d66248da1fc23e3a41817fe8a2b39cdbba957ba0aa908fe2aacea7e2b36e9e9`
- 639,980,658 bytes、72,402,797命令。
- Q889、古典bit261,506。
- 静的Toffoli-like数382,905。既存より11多いが、実行されるscan費用を減らす構成。
- 旧候補はSHA `e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`。

**主候補には採用しない。** 公式defaultの400バッチ、102400入力は実行を完了し、平均Toffoliは382062.92126953125に減った。しかし値エラーを2件観測し、旧e4のdefault0件に対するRの増加がゲート削減を上回った。さらに全バッチ終了後、最終集計中にprocessがexit137になり、公式結果のJSONは返らなかった。公式PASSとは表示しない。

観測した累積値に公式の変更していないClopper–Pearson関数とR関数だけを適用して、費用362761948064.14136を復元した。旧e4の359707293756.04297より**0.8492055516%悪い**。`score8_dqi_twochart_progress.json`、`score8_dqi_twochart_full_recovered.json`、再計算用 `score8_dqi_recover_progress.py`、`score8_dqi_twochart_scalar_recovery.json` に、実行結果と集計の復元を区別して記録した。回路・seed・saltを変えた再採点やKaggle提出は行っていない。

## 位相恒等式

体は公式のGF(4096)。体元aを掛ける12×12の二進行列をM_a、その転置をT_aとする。maskは体元そのものというより、12bitの内積を取る双対座標として扱う。

\[
 (T_a m)\mathbin{\cdot}e=m\mathbin{\cdot}(ae),\qquad
 T_a T_b=T_{ab}.
\]

物理点x_iと誤り値e_iに対し、syndromeは

\[
 S_j=\sum_i e_i x_i^{j+1},\qquad 0\le j<70.
\]

定数項ゼロで次数70以下のg(x)=Σ_j g_j x^{j+1}と古典mask λについて、

\[
 \lambda\mathbin{\cdot}\sum_jg_jS_j
 =\sum_i(T_{g(x_i)}\lambda)\mathbin{\cdot}e_i.
\]

したがって各oracle maskにT_g(x_i)λを加え、左辺の位相を元のsyndromeへ一度補償すれば、同じ誤りwordの位相oracleになる。λは古典maskから選んでよい。入力syndromeを測定して古典化する操作ではない。

既存の70点補間gaugeを開いた後、公開点1,…,70の実効maskはゼロになる。そのうち1点を再び自由にする多項式を、次の2つから選ぶ。

\[
 g(x)=x\prod_{r=1}^{69}(x+r),\qquad
 h(x)=x(x+70)\prod_{r=1}^{68}(x+r).
\]

gは点1,…,69を、hは点1,…,68と70をゼロに保つ。どちらも固定零点は69個で、

\[
 \dfrac{h(x)}{g(x)}=\dfrac{x+70}{x+69}
\]

となる。4025個の残余点では分母・分子とも非ゼロであり、この比の作用は公開定数による古典CX回路で実装できる。

既存gで正規化された残余maskをr_iとする。第1チャートの最適ラベルλ_0は、4025個のr_iと仮想zero pivot1個の最頻値。第2チャートのラベルλ_1は、4025個のT_{g(x_i)/h(x_i)}r_iと仮想zero pivot1個の最頻値である。

どちらも飽和しない12bitカウンタで正確に数える。同点は既存チャートを保持する。非選択側のラベルは古典的にゼロへ戻す。

## 実行Toffoliが減る理由

チャートcの最大頻度をn_cとする。そのチャートでゼロになる物理mask数は69+n_cで、実行されるscan費用は

\[
 T_{\rm scan}(c)=11(4026-n_c).
\]

新候補はmax(n_0,n_1)を選ぶため、任意の古典mask入力について

\[
 T_{\rm scan,new}\le T_{\rm scan,old}
\]

が成り立つ。最大頻度探索に量子Toffoliや量子補助bitはない。

静的命令としては、以前省略していた点69のcellを1つ加えたため11T増える。しかし、第2チャートが勝った場合は既存の点70のmaskをゼロにして、そのcellを省略する。第1チャートなら新しい点69を省略する。残余点の追加のzero maskが純削減となる。

scanに含まれるHMRの数が変わるため、同じsimulator seedを指定しても、その後の測定乱数の割り当てが変わる。上の不等式はscan実行費用の点ごとの主張である。scan以外の新鮮なHMRの分布は変わらないので、全回路の期待費用も改善する。一方、固定seed1本の全回路T数が必ず減るとは主張しない。

## 古典maskモデル

4025個の独立一様な12bit maskを16,384組、構築とは独立に固定したseedで比較した。

| 項目 | 結果 |
|---|---:|
| 既存チャートの平均追加零点 | 6.19696044921875 |
| 第2チャート単独の平均追加零点 | 6.188232421875 |
| 2つから選んだ平均追加零点 | 6.51611328125 |
| 第2チャートへの厳密な改善選択 | 4,323 / 16,384 |
| 予測される平均Toffoli削減 | 3.51068115234375 / shot |

これは `score8_dqi_twochart_model.json` のモデル値であり、全デコーダやKaggleの実測スコアではない。

## ネイティブ検証と全回路への結合

gauge部品は32ケースで検証した。両チャートの強制勝者、最上位bit、全零、ランダムmask、元の70点補間maskが非ゼロのケースを含む。誤りweight1、18、31、35の物理誤りwordから独立にsyndromeを作り、元mask oracleと新残余mask oracleとの差分が、実際に量子syndromeへ付いた位相と一致することを確認した。

syndromeは不変、閉じた後の全4095 maskは元へ復元、古典scratchは全零だった。量子補助bitやToffoliは追加しない。記録は `score8_dqi_twochart_native.json`。

点69は既存回路のFFT coset64へ挿入する。完全な2つのcoset変換と既存point70・point71を含む14,440命令を生成し、既存e4回路へ、命令と全演算子の対応で一意に照合した。syndrome由来の量子データ位置と元の古典入力bit位置は恒等対応を要求した。

- 旧回路の挿入境界：operation30,263,126。
- locator値：q732,…,q743。
- value：q696,…,q707。
- 既存のclean ladder：q869,q872,q885,q888,q871,q873,q887,q878,q867,q877。
- maskの公開体スケール：1199。
- 新しい点69 cell：459命令、11T、既存Q889以内。

追加cellはlocatorの全4096値と、locator=0でmaskの全4096値を含む8192入力を、2つのHMR seedで確認した。位相は `[locator=0] * dot(value,T_1199 mask)` と一致し、量子データ・maskを保持、ladderを0へ戻した。実行Tは厳密に11*[mask≠0]だった。

旧gaugeのprefix/suffixは10本のKMB命令列すべてで既存回路と完全一致していることを確認してから置換した。それ以外のデコーダの全バイトを保持し、照合した境界にcellを挿入した。記録は `score8_dqi_twochart_binding.json` と `score8_dqi_twochart_splice.json`。

## 同じ2560入力の比較

既知の2つの回帰ケースを含む512入力と、事前に固定した独立2048入力を、旧e4と新候補へ同じ入力seedで再生した。

- 2560入力で実行T合計を12,184削減、平均4.759375削減。
- 値エラーは旧・新とも1、位相エラーはとも0。
- 全syndrome出力、補助量子bit、復元したE入力は一致。
- 非失敗入力の位相はすべて一致。
- 既知weight33ケースの修復は保持。
- 既知weight31の1入力は同じvalue failureを残した。この既存失敗入力の位相だけは異なる。全入力の出力等価性という主張にはしない。

デコーダの正しさが保証される既存の入力領域について、gaugeの位相恒等式が成立する。元から間違ったデコーダ出力を返す領域で、その間違った位相を保存する必要はないが、新たな失敗を導入していないことは全デコーダの検証で別途確認する。

対応記録は `score8_dqi_twochart_paired_plan.json`、`score8_dqi_twochart_paired_before.json`、`score8_dqi_twochart_paired_after.json`、`score8_dqi_twochart_paired_comparison.json`。

## 独立レビュー

別の実装者による `score8_dqi_twochart_independent_review.py` は、候補のGF演算コードを流用せず、49,152個の基底積、全4095点のg/h、4025個の比、追加cellの定数1199を再計算して一致を確認した。69個のmask fixtureで物理scanの費用差が11*(max(n_0,n_1)-n_0)になることも確認した。旧ラベル0から新しい非ゼロラベルへ切り替わる3例も含む。

旧回路の古典bit範囲が0,…,208168、新しく保持するpivotが208169から始まること、Q889、新候補のファイルhashも独立に確認され、blocking defectは見つからなかった。レビュー結果は `score8_dqi_twochart_independent_review.json`。

## default全バッチの観測と集計の復元

公式verifierは変更せず、102400入力、seed未指定、salt空、log2_delta=-128、batch256、worker1で実行した。

| 項目 | 観測または復元した値 |
|---|---:|
| 完了したbatch callback | 400 / 400 |
| 完了した入力 | 102400 |
| 値エラー / 位相エラー | 2 / 0 |
| Toffoli合計 | 39,123,243,138 |
| 平均Toffoli | 382062.92126953125 |
| 旧e4の別default入力集合に対する平均T差 | −3.6080957031 |
| 公式関数から復元したε上限 | 0.0009488155716079551 |
| 復元したR | 1.2013880602795501 |
| 復元した資源費用 | 362761948064.14136 |
| 全batchまでの検証時間 | 392.543秒 |
| process終了code | 137 |

最終の `reaction_depth` と完全な操作統計は得られていない。終了原因は確定していない。最終集計時のメモリ増大が疑われるが、kernelの原因記録は取得できなかった。別processで回路を読み、公式と同じcanonical serializationのSHAを計算して、raw KMBのSHAと同じことは確認した。

復元した費用は、保存済み累積件数からのスカラー計算であり、公式関数が結果を正常に返したという証明ではない。全400バッチをやり直したり、新しい入力を選び直したりしていない。

## 観測した2件の失敗を旧e4と照合

上記defaultの進捗から、最初の失敗を含むbatch100–124と、2件目を含むbatch275–299を特定した。その50batch・12800入力だけを、元の候補defaultの入力seed・simulator seedを保持して旧e4へ再生した。旧e4にも値エラーが2件あった。その2つのbatchだけを、バイト列を変更していない新候補で再生し、同じ入力・同じ失敗位置であることを確認した。

| 0始まりbatch | batch内shot | 全体shot | 物理誤りweight | 旧e4 | 新候補 |
|---:|---:|---:|---:|---|---|
| 110 | 152 | 28312 | 32 | value failure | 同じvalue failure |
| 280 | 52 | 71732 | 30 | value failure | 同じvalue failure |

2batchの全512入力で、入力syndrome・mask・期待位相のハッシュ、および出力syndrome・量子補助bit・復元maskのハッシュは旧新一致した。値が正しい入力の位相は、旧新とも全件で公式oracleと一致した。誤りweight32の失敗入力は、失敗記録の全項目が一致した。weight30の失敗入力では既に間違っている値出力は一致する一方、実際の位相が旧trueから新falseへ変わった。このため、既存失敗領域まで含む全入力の位相等価性は主張しない。公式と同じ分類では、両回路ともvalue error 2・phase error 0である。

したがって、今回defaultで観測した2件は**旧e4にも存在するデコーダの失敗**であり、この2件から新方式の失敗確率増加を結論してはいけない。旧e4の保存済みdefault0件と新候補default2件は、canonical hashが異なるため別の入力集合を用いている。ただし、新候補で観測済みのRと資源費用が悪化した事実はそのまま記録し、主候補へは採用しない。今回の診断は、全102400入力の旧新同時比較や、公式verifierの正常終了の代わりではない。

記録は `score8_dqi_twochart_failed_ranges_before.json`、`score8_dqi_twochart_failure_after.json`、比較結果 `score8_dqi_twochart_failure_comparison.json`。比較は `score8_dqi_twochart_compare_failures.py` で再計算できる。

実行した2つのfailure replay planには、複製元の `created_utc`、`independent_seed_label`、`comparison_baseline_result` が説明用メタデータとして残っている。それらは今回の実行日時・標本数・比較相手を表すものではない。実行を決めたのは各groupの実際の `seed_sha256` と `batches`、回路ハッシュ、保存された数値seedであり、記録はそれらに基づく。証拠のハッシュを維持するため、実行済みplanを後から修正していない。

## 再現

`score8_dqi_twochart.py` の `--action model` でmaskモデル、`--action build --pieces DIR` でgauge prefix/suffix、`--action native --pieces DIR` でネイティブ位相検証を行う。元のApache-2.0公開ソースは `--source-root SOURCE/src` で指定し、書き換えない。

`score8_dqi_twochart_bind.py` は既存e4とQ889のFFT境界を照合してpoint69を生成する。`score8_dqi_twochart_splice.py` は追加cellをネイティブ検証し、旧gaugeとの完全な境界一致を確認して新候補を作る。

実行環境、公式verifierとKickmixのハッシュ、seed、salt、信頼度は各JSONへ保存する。既存合格回路を上書きせず、別候補として作成する。
