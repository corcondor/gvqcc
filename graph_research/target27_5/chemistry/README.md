# score19 の角度表で C を下げる検査

score19のローカル値 27.32812350537394 を基準に、4030 CCX/pass のANGLEをそのまま使う。(R=8,B=143)、量子ビット427で、公式コスト計算をCごとに再評価した。C41は絶対的な正規化下限を使っても総合27.498967204なので、化学だけで27.5を超えるにはC40以下が必要。C40なら総Toffoli14,408で、他の2課題を固定すると正規化が47.037411213未満で27.5に達する。

score19の15回路が読み出す1,220×75整数語を用いた。格納メタデータにある別の角度表は使わない。使用角度表のuint8 SHA-256は `8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea`。

| (C) | 最良の公式数値 (e_2) | 固定グループの必要下限 |
|---:|---:|---:|
| 39 | 未探索 | 21.53830 mHa |
| 40 | 27.52786 mHa | **20.42136 mHa** |
| 43 | 21.12647 mHa | 18.08099 mHa |
| 上限 | 20 mHa | |

`rank_reduce.py` は各群の射影子をCholeskyで直交化し、同一のFrobenius計量で小さい固有方向を落としてからL-BFGSで二体項を再フィットする。公式の数値関数で最良点を評価した。C40とC43はそれぞれ724回、686回の費用・勾配計算を行い、制限時間で止めた。許容精度を満たす新しい回路は得られず、公式の回路ショット検証には進まなかった。

`hard_threshold.py` は係数行列の直接更新とは別に、二体Gram行列をPSDのまま更新し、各群にC個の正固有値だけを残して実際の二次目的を評価する。任意のPSDランクで得たフィットから再開して、凸近似に基づく別初期値を試した。C40は27.53287 mHa、C43は21.13165 mHaで、採点に使える結果は得られなかった。

`span_rank.py` は1,144個の二体射影子の張る空間に参照テンソルを射影し、その中で任意のPSDランク (8C) を許す。C40の下限は16.62666 mHaで、射影子の再グループ化まで許す場合にはC40を排除できない。`group_rank_bound.py` は元の8グループへの係数のブロック対角制約を先に課す。この線形空間へのFrobenius直交射影と、その射影の最良PSDランク (8C) 近似を分けて評価する。直交射影の近似誤差は正規方程式残差とGram最小固有値で差し引いている。表の下限はfloat64の結果で、区間演算の証明ではない。元のグループに固定したC40以下は下限が許容値を超える。別の角度表、別の射影子配置、ANGLE削減と別課題の費用改善との組み合わせはこの下限の範囲外。

`group_dual.py` では上の直交射影を出発点に、グループ付き表現の線形空間に直交する対称行列を加えた。任意の固定グループ表現 \(H\) について \(\langle Z,H
angle=0\) なので、参照テンソル \(T\) に対する元の目的は \(\|T\|_F^2+\|H\|_F^2-2\langle T+Z,H
angle\) とも書ける。グループ制約を外してランクだけを残すと下限が得られる。下限は \(\|T\|_F^2\) から \(T+Z\) の射影子の張る空間に圧縮した行列の上位最大 \(8C\) 個の正固有値の二乗和を引いた値の平方根。独立した `direct_dual_check.py` は公式参照を再構築してこれを直接評価し、C40で20.42136 mHaを得た。境界との差は0.42136 mHa。直交残差は \(3.60\times10^{-18}\)。この数値結果は元のグループと角度表を固定した条件に適用する。

## 合法な行置換と六語キャッシュ

`row_label_screen.py` は、各16アドレス内で任意の置換を許し、既存のbit0アフィン符号と5タグを同時に保つ条件を調べた。score19の完全な76ブロックすべてで、既存アフィン列の係数が4次元を張る。この条件を保つ置換は4ビットのアフィン写像になる。タグには単独の値を持つ点が10個あり、タグの値を保つ置換はそれらを個別に固定する。非恒等な4ビットアフィン写像の固定点は最大8個なので、完全ブロックに非恒等の置換はない。終端の4要素は、タグを保つ全6置換を列挙した。非恒等な5通りのどれも、15バッチすべてで高位コファクターの階数を75から76へ増やした。別の符号か別のタグ間の受け渡しを導入する案はこの結果の範囲外。

`six_word_liveness.py` は、固定した六語バッチ13個について前後のスロットの対応を各720通り列挙した。全対応で高位のコファクター階数75、低位15。既存構成と同様に純高位と純低位の特徴をそれぞれ独立に張るバンクを同時保持するには、定数込み91次元が必要になる。データと選択線に59量子ビットが必要で、両方向で一定の出力パリティをすべて作業領域に使うと仮定しても、中央11バッチの必要幅は133量子ビットだった。自然な並びは136、初回は137、終端は134以上。128の公式上限に収めるには、旧バンクをそのまま移設する方法の外で特徴を作り直すか、時間分割が必要になる。これらはレイアウトの必要条件で、すべての六語回路の幅を制限するものではない。

## 再現

`SOURCE` は score19 ZIP の `dfthcsos/submission.npz`。 `WORDS` は `score9_rebatch_synth_source_words_1232.npy`。 `PYTHONPATH` に変更していない公式検証器の親ディレクトリと score19 の `chem_next_fixed_angles.py` 所在ディレクトリを入れる。NumPy、SciPy、FeMoCoの公式FCIDUMPが必要。

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python span_rank.py --npz "$SOURCE" --words "$WORDS" --output span_rank.json
python rank_reduce.py --npz "$SOURCE" --words "$WORDS" --rank 40 --seconds 48 --output c40.json
python rank_reduce.py --npz "$SOURCE" --words "$WORDS" --rank 43 --seconds 48 --output c43.json
python hard_threshold.py --npz "$SOURCE" --words "$WORDS" --out hard_threshold.json --seconds 22
python group_rank_bound.py --npz "$SOURCE" --words "$WORDS" --out group_global_rank_bound.json --save-projection grouping_projection.npz
python group_dual.py --projection grouping_projection.npz --out group_dual.json --rank 40 --iterations 1 --save-dual group_dual_vector.npz
python direct_dual_check.py --npz "$SOURCE" --words "$WORDS" --projection grouping_projection.npz --dual group_dual_vector.npz --out direct_dual_check.json
python row_label_screen.py --words "$WORDS" --out row_label_screen.json
python six_word_liveness.py --words "$WORDS" --out six_word_liveness.json
```
