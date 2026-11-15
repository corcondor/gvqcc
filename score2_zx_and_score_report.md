# ZX簡約と実スコアに結び付ける回路・数値最適化

実験日: 2026-11-14 UTC。対象は既存の4033-Toffoli ANGLE familyと、手元で再現済みのAsterios因子である。

## 1. 採用できた結果

**Clifford部分の厳密な再合成と実際のPyZXグラフ簡約を適用し、ANGLE 15回路の総ゲート数を611,422から408,394へ削減した。さらに20個の整数角度変更を追加Toffoliなしで実装し、H2_Iも再フィットした最終採用候補は408,788ゲートで公式78,080ケースの検証を通った。同一の再現ベースラインに対する化学タスク費用も下がった。**

| 指標 | 再現ベースライン | 今回の採用候補 |
|---|---:|---:|
| ANGLE総命令数 | 611,422 | 408,788 |
| SWAPを3 CXに展開した命令数 | 611,422 | 409,466 |
| ANGLE片道Toffoli | 4,033 | 4,033 |
| 化学タスク総Toffoli | 14,728 | 14,728 |
| 化学タスク総量子ビット | 427 | 427 |
| lambda_eff | 46.90658950862355 | 46.906472675810164 |
| error_1 / Ha | 0.01999999799999866 | 0.01999998000005401 |
| error_2 / Ha | 0.019999998499405293 | 0.0199999936269957 |
| 公式費用 | 294,988,786.87084424 | 294,988,052.12610483 |
| 完全公式検証 | PASS / 78,080 | PASS / 78,080 |

費用差は734.7447394、低下率は0.0002490755%。採用版のゲート削減は202,634、33.1414310%である。Clifford削減自体はこの費用式に含まれないため、33.1%のゲート削減を33.1%の競技スコア改善とは表現しない。数値的な改善は実際の整数角度変更とH2_Iの再フィットを組み合わせたもの。Wとtree_edgesは元のままで、91,500個のangle_wordsのうち20個をXOR 1した。

ユーザーの別環境で報告されたlambda_eff=46.905894137よりは高い。そのNPZと同一条件で比較できていないため、ユーザーの最良値更新やKaggle Public Score更新を主張しない。今回の候補をKaggleへ提出してはいない。

実証資料:

- `score2_best_full_verification.json`: 正式な最終評価。SHAで結び付けた基準の公式PASSと比較している。
- `score2_best_reachable_proof.json`: 全アドレス・正逆方向・全測定位相の厳密検査。
- `score2_candidate_manifest.json`: 配布ファイルとハッシュ。
- `score2_dfthcsos_candidate_verify.py`: NPZを一切置換せず、そのまま公式回路検証に渡すランナー。

採用NPZのSHA-256は`5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357`、公式評価のsubmission family hashは`142af563255af76b2d2097fb5e8cbc61340c583ea70dadeddf7858de501faf84`。配布物はDFTHCSOSコンポーネント一式であり、DQI/invsqrtを含めた3タスク全体の提出ZIPではない。

## 2. 実行したZX・Clifford最適化

### 2.1 GF(2)上の厳密な線形回路再合成

X/CX/SWAPからなる各区間を、任意の入力ビットに対する可逆アフィン写像`x -> A x XOR b`として取り出した。複数の消去順序と転置行列側の合成を試し、ゲート数が減ったものだけを採用した。元の写像と再合成写像は独立したGF(2)計算で比較した。

CCX、位相演算、HMR、条件付き命令などは境界として保持した。したがって、測定をまたいで通常のユニタリー回路と仮定する変換は行っていない。この段階は611,422 → 416,697、194,725ゲート削減だった。

### 2.2 実際のPyZXグラフ簡約と回路抽出

PyZX 0.10.8で、区間ごとに次を実行した。

```python
graph = circuit.to_graph()
zx.simplify.full_reduce(graph)
extracted = zx.extract_circuit(graph, up_to_perm=False, optimize_cnots=3)
optimized = zx.optimize.basic_optimization(
    extracted.to_basic_gates(), do_swaps=False
)
```

最初の大きい12区間では12件すべてで削減し、6,243ゲート減った。次の32区間では20件を採用し、さらに2,060ゲート減った。全体で416,697 → 408,394となった。2回目は前段の出力に対する再走査を含むため、「独立した44区間」とは数えない。

採用条件は、抽出結果が許可されたX/CX/SWAPへ戻ること、PyZXの等価性検査でワイヤ置換・大域位相を無視せず一致すること、独立GF(2)写像が一致すること、ゲート数が減ること、の全てである。抽出結果が長くなった区間は元を維持した。

理論的な対応はDuncanほかのlocal complementation / pivoting / gflowを使うZX回路簡約である。一般に大きな単一ユニタリー行列を作る必要はない。[1]

### 2.3 回路全体の検証

1220アドレス × 15ローダー × 正逆2方向 = 36,600遷移を、サンプリングせず検査した。HMR結果を独立な形式変数として扱い、それぞれに付く位相係数が全アドレスで消えることを確認した。スクラッチ復元も含む。最後に、変更していない公式verifierを既定の78,080ケースで実行した。

ここで証明したローダー契約は、実アルゴリズムが使用する前後バッチを結ぶ到達可能部分空間上のもの。元4033回路について既に判明している任意40bitターゲットへのXOR拡張問題は、今回のClifford変換によって新たに改善・悪化したものではない。書き換えた各アフィン区間自体は任意入力で等価である。

以前の固定語verifier wrapperは、同一因子で費用が1 ULP変わっただけでも`lower`を立て得た。新wrapperは32 ULPの比較幅を設け、初期Clifford-only検証を費用不変と分類した。今回の696.0113の差は、この比較幅約0.000001907を大きく上回る。

## 3. 位相多項式とユニタリー距離の直接最適化

### 3.1 この回路に適した距離

計算基底の写像が同じで、位相だけが異なる論理回路を

\[
 U|x\rangle=e^{i\phi(x)}|f(x)\rangle,\qquad
 V|x\rangle=e^{i\tilde\phi(x)}|f(x)\rangle
\]

と書くと、検証対象の入力部分空間に制限した作用素ノルム差は

\[
 \|U-V\|=\max_x 2\left|\sin\frac{\tilde\phi(x)-\phi(x)}2\right|.
\]

invsqrtのようにBoolean特徴が固定された位相回路では、係数を変えてもこの位相差は特徴行列と係数の線形結合で表せる。小さい誤差領域ではsinが単調なので、全入力に対する最大位相誤差を抑える問題をminimax線形計画として解ける。今回の目的には、平均Frobenius距離をニューラル最適化するよりも直接的な制約である。計算過程の測定枝の正当性は別途維持する必要がある。

### 3.2 実行した探索

`score2_phase_parity_search.py`では、実回路の3つの切断点に存在するwireの1〜5本XORを位相特徴候補とした。これらはCXでパリティを計算して回転し、CXで戻せるため、追加Toffoliや追加量子ビットを必要としない。

LP双対から有望なパリティを選び、既存の小さい回転の削除あり・なしを含む30候補を、全3,133,452入力の分離制約で再評価した。この有限探索から費用が改善する候補は得られなかった。これはあらゆる位相多項式基底の最適性を意味しない。結果は`score2_phase_parity_search_result.json`に残してある。

ZX phase teleportationは離れた位相を統合でき、任意角の位相にも適用する理論がある。[2] 一方、PyZXの`phase_block_optimize` / TODD実装はClifford+Tを前提とし、より小さい一般回転や未展開Toffoliをそのまま入力することを公式APIが警告している。[3] 今回は任意角をTODDに無条件で渡すことを避け、一般回転の誤差・費用は上記の直接問題で検査した。

## 4. 分解前のAND/XOR構造を使う角度変更

別の重要な実装結果は、疎な整数角度の変更を既存ローダーに安く組み込む機構である。

最初の汎用方法では11bitアドレスの等価判定に10 CCXを要した。既存の特徴生成段を解析すると、下位4bitの全関数空間16次元が無料の線形結合で得られ、上位アドレス77通りの関数空間も76次元まで存在した。これを使うと、タグを保つ単点の差分は多くの場合、影響するローダーごとに1〜2 CCXで組める。複数出力への方向共有、HMR/CZ位相補正、追加補助ビットの復元を含めて実装・検査した。

上位アドレスの特定16行を一括反転する差分には、既存特徴のCX fanoutだけで実現できるものがある。この場合、追加CCXは0。rootの独立GF(2)計算は、元の特徴と既存積の全spanを使い、各16行ブロックにだけ支持を持つ関数空間を正確に求めた。隣接ローダー両方で実装できる462個のbatch/blockパターンがあり、この範囲では非ゼロの最小支持は16だった。

この出力先変更を伴う数値探索で最初に、16個の整数角度を変更し、H2_Iを再フィットして費用が下がる候補を得た。回路を組み、完全公式検証にも通った。ただし対照実験として角度を全て元に戻すと、同じ費用でerror_1がさらに下がった。この時点の低費用版は角度を戻して保存した。`score2_combined_full_verification.json`のlambda_eff=46.9064788348674、費用294,988,090.85952884がこの中間成果であり、その改善はH2_I再フィットの効果である。

続いて、上位アドレス0と76を組み合わせ、欠けている1次元のパリティを相殺する無料特徴を使った。これによりアドレス0〜15と1216〜1219の合計20行について、角度列19のLSBを一括反転できた。実変更は各wordの±1で、タグは不変。k3/k4の2ローダーだけにCX出力先を追加し、4033 Toffoliを維持した。

この候補でH2_Iを再フィットするとlambda_eff=46.906472675810164となった。同じW/H2_Iで20個のwordsを元に戻した対照はlambda_eff=46.906571024915195で、全ての数値条件は通るが費用が高かった。したがって、この最終候補では整数角度変更が良い評価値に寄与している。最初の16word候補と最終20word候補の帰属は区別している。

最終ゲート数408,788は、Clifford最小版408,394に、差分のClifford操作238と変更した2回路のSWAP展開156を加えたもの。変更しない13回路は元のSWAP表現をそのまま保持した。最終全回路は、shape(1220,75)・整数dtype・8bit値域を確認する修正版の独立検証器で再検証し、さらに公式78,080ケースも通った。

主要コードは`score2_angle_sparse_patch.py`、`score2_angle_feature_patch.py`、`score2_angle_free_mutations.py`。数値側の全結果と対照実験は別の`score2_chemistry_*`実験記録を参照する。

Toffoli/CCZの構造を分解前に扱うという点ではZH-calculusやXOR-AND表現が直接対応する。ZHとZXをFourier変換で結ぶ研究は、AND構造の縮約を先に行い、位相の縮約を後に行う構成を理論的に説明する。[4]

## 5. Cartan分解・L-BFGS・Adam・Muonの使い分け

### Cartan/KAK

2量子ビットの一般ユニタリーでは、局所回転を除いた非局所部分を3パラメータに整理でき、任意の2量子ビット演算は3 CNOTと1量子ビット回転で表現できる。[5] したがって2量子ビット区間の再合成には有効である。

今回の採点上の中心は、多入力Boolean関数のAND数、補助量子ビット、有限精度因子である。2量子ビットKAKから一般Rx/Ry/Hを出し、最終許可ゲートへ戻す時に元のToffoliより安くなるとは限らない。今回は2量子ビットKAKを実行したという主張はしない。実装できて成果が出た部分はGF(2)再合成とPyZXである。

### L-BFGSとAdam

固定ゲート構造の角度に対し、ユニタリー距離を最小化する方法には実装上の先例がある。IBMのApproximate Quantum CompilerはFrobenius内積に基づく目的と解析勾配を用い、実装の既定はL-BFGSである。[6]

DFTHCSOSでは、連続角度やWを小さく動かして目的が改善しても、8bit整数への丸めで同じwordsへ戻ることがある。したがって連続最適化だけで終了せず、整数wordsの実変更、実際の回路費用、公式誤差まで一つの候補として評価する。今回の離散探索、Wの最小二乗transport、H2_I再フィット、回路パッチはそのための実装である。

### Muon

Muonは行列勾配の直交化を用いるため、行列Wの更新候補としては検討できる。引用した研究が実証しているのは言語モデルの学習であり、この量子回路問題での優位や、量子ユニタリー制約の自動維持を示したものではない。[7] 勾配の直交化と、更新対象ユニタリーを多様体へ射影することは異なる。今回Muonによるスコア改善は未実証である。

## 6. 再現と記録

Python数値処理はNumPy 2.3.5 / SciPy 1.17.0、回路処理はKickmix 1.0.0、ZX処理はPyZX 0.10.8。PyZXは実行時にインストールしたパッケージを使用した。

主な順序:

1. `score2_clifford_affine_reduce.py`: 元ローダーのアフィン区間を削減。
2. `score2_pyzx_blocks.py`: 上位12区間、続いてその出力の上位32区間に適用。
3. `score2_clifford_validate.py`: SWAPを検証表現だけで3 CXへ展開し、全到達状態と位相を確認。
4. `score2_chemistry_identity_refit.py`と対照実験: H2_I更新候補を確定。
5. `score2_dfthcsos_candidate_verify.py`: 回路から復元した全91,500 wordsとNPZを明示比較し、実際のNPZと最終15回路を公式評価。

前の継続実験`score_continuation_report.md`に記録済みのDQI CNOT削減や失敗候補を、今回の新規成果に数え直していない。invsqrt追加探索の詳細は`score2_invsqrt_report.md`に記録する。

## 参考文献・公式資料

1. Duncan, Kissinger, Perdrix, van de Wetering, *Graph-theoretic Simplification of Quantum Circuits with the ZX-calculus*, Quantum 4,279 (2020). https://arxiv.org/abs/1902.03178
2. Kissinger, van de Wetering, *Reducing T-count with the ZX-calculus*. https://arxiv.org/abs/1903.10477
3. PyZX 0.10.8 official API, especially `phase_block_optimize`. https://pyzx.readthedocs.io/en/latest/api.html
4. Kuijpers, van de Wetering, Kissinger, *Graphical Fourier Theory and the Cost of Quantum Addition*. https://arxiv.org/abs/1904.07551
5. Vidal, Dawson, *A universal quantum circuit for two-qubit transformations with three CNOT gates*. https://arxiv.org/abs/quant-ph/0307177
6. IBM Quantum, *Approximate Quantum Compiler*. https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.synthesis.unitary.aqc
7. Liu et al., *Muon is Scalable for LLM Training*. https://arxiv.org/abs/2502.16982
