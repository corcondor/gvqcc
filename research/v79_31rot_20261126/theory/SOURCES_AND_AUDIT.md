# V79・31回転移植の理論と独立監査

調査日: 2026-11-26。以下は文献の主張、今回導出した恒等式、実回路で測った事実を区別する。公式採点の実行証跡ではない。

## 1. 実際のV79の位置づけ

`recovered/V79/runs/tree36.kmb` の SHA-256 は
`e81cbe79c7b6ac2aef27ff5539d458ff2726e3b0c9bb01f26e17fdcae4cd347c`。

|量|V79 tree36|
|---|---:|
|量子ビット|36|
|CCX|1,267|
|命令|53,942|
|一般角回転|7,747|
|HMR|1,267|
|最小余裕（2^-64 turns単位）|138,112,178|
|独立再計算された費用式|2,298,148.0759806475|

これらは保存された `.receipt.json` と `.cost.json` の数値である。CCX 1,267 と31回転を同時に達成した回路という意味ではない。31回転側への移植で保持する対象は、位相を与えるBoolean関数と角度の組である。

今回 `audit_v79.py` で全 2^22 = 4,194,304 入力をビット並列に再生した。7,747回転の対象Boolean関数を補関数まで同一視しても、すべて異なる。定数関数への回転もない。したがって、単に同じ関数の角度をまとめる処理では回転数は減らない。この事実は、別の位相基底による再合成の限界を示さない。

同じスクリプトは、各CCXの制御積を、現在ある他の線の0、1、1本の線、補数、2本のXORで表せるかを全入力で調べる。`--span` は定数と他の全線が張るGF(2)空間で厳密に判定する。対象線自身は候補から除く。結果は同ディレクトリのJSONに記録する。変換は元と同じ入力状態からの意味を保存する。量子実機の実験ではなく、実際のシリアライズ済みKMBを使う厳密検証である。

追加実験では、V79全立方体の全1,267 CCXが現在の他の線のアフィン空間の外にあった。一方、最終のexchange系回路を合法入力域に制限すると、12個の制御積がアフィンになる。これは「全立方体での置換失敗」と「合法域での置換成功」の違いを実測したものだ。`care/README.md`、監査JSON、および `verify_domain.py` がその証跡を保存する。CCX最小案は36Q・1,218 CCX・48,866命令となるが、入力域外には測定位相が相殺されない反例がある。全立方体等価と呼ばない。

## 2. 費用式を正しく移植する

固定ミラーの公式verifier:

https://github.com/Inzainos/quantum-circuit-compilation/blob/4277c767440df9efb8a90860ae2ce47028e46ba9/verifiers/invsqrt/verify_submission_invsqrt.py

`margin` を64-bit固定小数の最小余裕、`R` を一般角回転の平均実行数、`P` をCCX/CCZ/CSWAPの平均実行数、`T_base` をT角回転などのT費用とすると、一般角回転がある場合の費用は

\[
\epsilon=\frac{\pi\,\mathrm{margin}}{2^{64}R},\qquad
C=Q\left(P+\frac{T_{\mathrm{base}}}{4}
+\frac R4\left[0.56\log_2\frac1\epsilon+5.3\right]\right).
\]

公式ソースの `reference_values` とV79 `cost.py` の整数参照値・丸め・余裕計算は、今回のbeta=1、precision_bits=24について一致する。ただしV79 `cost.py` はCCXだけを数え、`T_base` を明示的には加えない。このV79は全回転が一般角なので問題にならないが、別回路へ無条件に流用できない。条件付き有料ゲートがあると、静的命令数と平均実行数も区別が必要になる。

V79の費用の98.0153%は回転合成に由来する。同じ余裕を保ってCCXを1減らすと費用は36減り、一般角回転を1減らすと約298.033減る。この比較も31回転側の合成成功を示す数値ではない。

## 3. 高次残差を落とさない座標輸送

以下は今回の代数的導出であり、論文からの引用定理ではない。Boolean環で

\[
(u\oplus\delta u)(v\oplus\delta v)\oplus uv
=u\,\delta v\oplus v\,\delta u\oplus\delta u\,\delta v
=u\,\delta v\oplus\delta u\,(v\oplus\delta v).
\]

右端の形なら、更新後の `v` を使うことで交差残差を明示的な3項目として追加せず、正確な2項で扱える。削減になる条件はデルタ関数と更新後の制御値が実際に利用できることであり、恒等式だけでCCX削減は保証しない。

任意角の位相に対してはGF(2)の式を整数加算と混同できない。`f'=f XOR g` のとき、整数値として

\[
f=f'+g-2f'g,
\qquad \theta f=\theta f'+\theta g-2\theta f'g\pmod{2\pi}.
\]

したがって回転を跨いで非線形座標を取り替えると、制御位相の補正が必要になることがある。31回転の上限を守るには、まず回転を挟まないBoolean部分を最適化するか、補正角まで含めた完全な位相多項式を評価する。

## 4. V79から移植できる有限の構造

V79の主構造は、共通制御 `f` と線形形式 `l_i` の積 `f l_i` を複数の作業線に持つことである。

\[
f(l_1\oplus l_2)=fl_1\oplus fl_2
\]

により、同じ `f` の下では線形基底をCNOTで変更できる。旧基底空間と新基底空間の共通部分は保持し、補空間だけをHMRで消去・再計算する。現在の実装は `global_transport.py` の `intersection` と `basis_xors`、`treewidth.py` の `leaf_basis` にある。この操作を31回転側の計算部分に適用すれば、回転の対象関数を変えずに算術費用を下げる余地がある。ただし異なる共通制御の間で同じ恒等式をそのまま使えない。

`treewidth.py` のDPは主にCCX数を最小化する。明示的なWalsh展開には固定ペナルティを課すが、全候補の実際の一般角回転数と誤差余裕を直接最適化しているわけではない。候補採否にはシリアライズ後の費用を使う必要がある。

## 5. 「9/4則」の出典と適用範囲

ユーザーのいう9/4に一致する一次資料は、行列乗算指数の結果である。

1. OpenAI, **An Upper Bound of 9/4 for the Matrix Multiplication Exponent**, 2026-10-02.
   https://github.com/openai/math/tree/main/preprints/Matrix-Multiplication-Nine-Fourths-October-2-2026
   複素数上の算術演算量について、任意の正のepsilonで O(n^(9/4+epsilon)) の上界を主張する。有限サイズの可逆回路のCCX数を9/4倍や4/9倍にする規則ではない。

2. M. Levent Doğan, Vladimir Lysikov, Keiya Sakabe, Michael Walter, **Tensor value and the 9/4 bound for matrix multiplication**, 2026-11-06.
   https://arxiv.org/abs/2611.09716
   https://arxiv.org/html/2611.09716v1
   一つのテンソル因子を共有する部分直和を扱い、分数化・対称化したtensor valueの超加法性から全ての体で同じ上界を導く。対応するLean実装へのリンクは https://github.com/qit-lmu/omega 。この監査ではLeanビルドはしていない。

3. Alimzhan Amanov, Maxim van den Berg, Jeroen Zuiddam, **Multiplying matrices via polynomials: exposition and barriers**, 2026-10-21.
   https://arxiv.org/abs/2610.30054
   https://arxiv.org/html/2610.30054v1
   多項式乗算テンソルの退化と共有因子の組合せを解説する。論文で扱う構成部品に対する障壁を、GVQCCの有限回路全体の下限として流用してはいけない。

4. OpenAI, **The matrix multiplication exponent is nine fourths**, 2026-11-24.
   https://github.com/openai/math/blob/main/preprints/The-matrix-multiplication-exponent-is-nine-fourths-November-24-2026/README.md
   新しい原稿は一致する下界も主張し、Lean範囲をdivision-freeな形式的多項式恒等式の回路として説明する。今回、その下界の証明やLeanを独立再検証していない。GVQCC最適化に必要な仮定として採用しない。

実装に引き継ぐ考え方は、複数出力を別々に処理せず共有因子を持つ係数テンソル全体で合成することである。有限体上で
`F_o(x,y) = XOR_l a_l(x) b_l(y) c_(l,o)`
という厳密分解を得た後も、制御側のCNOT、出力側のCNOT、作業線、HMR補正を数える必要がある。漸近rankだけから31回転・36Qの実装を得たことにはならない。

## 6. 量子回路へ直接関係する一次論文

- Ruiz et al., **Quantum Circuit Optimization with AlphaTensor**, https://arxiv.org/abs/2402.14396 . T-count最適化をテンソル分解とガジェット探索へ結び付ける。GVQCCではそのT-count目的をそのまま使わず、実際の許可命令と費用を評価する。
- Craig Gidney, **Halving the cost of quantum addition**, https://arxiv.org/abs/1709.06648 . Temporary logical-ANDの計算と測定を用いた消去。V79ではHMR後の制御Z/CZが測定位相を正確に消すことを各入力で検証する。
- Tanuj Khattar and Craig Gidney, **Rise of conditionally clean ancillae for efficient quantum circuit constructions**, https://quantum-journal.org/papers/q-2025-05-21-1752/ . 条件付きで値が既知な作業線の借用は、幅制約とゲート数の同時改善に直接関係する。
- Iggy van Hoof, **Space-efficient quantum multiplication of polynomials for binary finite fields with sub-quadratic Toffoli gate count**, https://arxiv.org/abs/1910.02849 . Karatsuba型の構成で追加ancillaなしのToffoli削減を扱うが、CNOT数との交換条件がある。
- Niels Kornerup, Jonathan Sadun, David Soloveichik, **Tight Bounds on the Spooky Pebble Game: Recycling Qubits with Measurements**, https://arxiv.org/abs/2110.08973 . 測定後の位相負債を保持・後で訂正する計算順序と、量子空間・時間の交換条件を扱う。
- Mingyu Lee, Sanghyun Lee, Kabgyun Jeong, **Optimal (Parallel) Spooky Pebbling on Binary Trees**, https://arxiv.org/abs/2610.09434 . ブロック単位のcleanupで同じ中間値の再計算を抑える。木構造以外の任意DAGへ性能保証をそのまま拡張しない。

## 7. 検証器の適用範囲

V79 `verify_echo.py` はX/CX/CCX/HMR/条件付きZ/CZ/Z_POWを全入力で再生し、回転対象の関数をタグと比較する。さらに独立C++のuint128 Walsh変換で実位相と目標位相を比較する。HMRの各負債は、現在の制御関数と完全一致する必要がある。これは単なるランダム入力テストより強い。

ただし、この検証器は単一の即時HMR負債を仮定する専用実装であり、他の命令、一般的な条件付きデータ操作、遅延した複数負債を含む31回転回路へそのまま適用できない。公式KickMixのパーサと実行器を走らせた証拠にもならない。新しい回路の命令集合・測定構造に対応した独立検証と、公式実行結果を分けて記録する。
