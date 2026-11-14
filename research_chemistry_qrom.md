# DF-THC-SOS と角度ローダー改善の研究対応表

調査日: 2026-11-14 UTC。対象: 公開4033-Toffoli angle loader、`R=8, B=143, C=44, N=76, brot=8, J=5`。

## 1. 現時点の判断

**論文をそのまま移植してスコアが改善する候補は、まだ確認できていない。** 最初に調べる価値があるのは、既存の符号化構造を保つ範囲での表の並べ替えと、複数出力間で積を共有する合成である。任意の行並べ替えは物理モデルを保てても、現4033の小さなローダーを支える符号を壊す可能性がある。

SelectCopyのゲート構成はKickmixの範囲に収まる。一方、現在の表全体に汎用費用式を適用した整数探索では、既存ローダーに勝つ見込みを示せなかった。dense encodingは、論文どおりに書くと未対応の単独`H`命令を必要とし、現在のKickmix 1.0.0ではパース段階で拒否される。これらの結果は、データ依存の新しい等価回路まで不可能とした証明ではない。

### 確認済みの基準

数値は既存の[chemistry_report.md](chemistry_report.md)と[chemistry_experiment_summary.json](chemistry_experiment_summary.json)に基づく。本メモ作成にあたり既存の数値報告や提出候補は変更していない。

| 項目 | 値・範囲 |
|---|---:|
| ローカルで公式検証を通した因子 | 公開4033 loader + Asterios refit |
| `lambda_eff` | 46.906589508623554 |
| 総Toffoli | 14,728 |
| 総量子ビット | 427 |
| 化学タスクの費用 | 294,988,786.8708443 |
| angle loader片道合計 | 4,033 Toffoli / 15回路 |
| angle loader往復合計 | 8,066 Toffoli、全体の約54.8% |
| `error_1` / `error_2` | 0.019999997999999 / 0.019999998499405272 Ha |
| 許容誤差 | それぞれ0.020 Ha |
| 各ANGLEの上限 | 128量子ビット |
| 現在の各ANGLE入出力 | 11 selection qubits + 40 word qubits |

ユーザーの別環境で報告された `lambda_eff=46.905894137` とは同一の重みを取得できていない。このメモの基準を、その値からの改善として扱わない。

化学タスクの公式費用は

\[
  S_{\mathrm{chem}}=\lambda_{\mathrm{eff}}\,T_{\mathrm{total}}\,Q_{\mathrm{total}},
  \qquad
  \lambda_{\mathrm{eff}}=\sqrt{E_{\mathrm{gap}}(2\Lambda-E_{\mathrm{gap}})}.
\]

`lambda_eff` と `Q_total` が同じなら、片道loaderから100 Toffoli削ると往復で200、化学タスク全体では約1.36%の費用削減になる。これはKaggle総合Public Scoreの上昇率ではない。

## 2. 主要6論文と実装判断

所属は原則として当該論文の公表時のもの。2026年のarXiv論文は、確認できた版をプレプリントとして扱う。

| 論文 | 公表時の著者・所属 | 今回に持ち込む部分 | 既存との差と条件 |
|---|---|---|---|
| **Database Reordering for Compact Grover Oracles with ESOP Minimization**、2026-04、arXiv:2604.06578v1 [F1] | Yusuke Kimura、Yutaka Takita。両者Fujitsu Limited | 行順序の探索とESOP最小化を組み合わせる | 本競技でも因子の内部ラベルを変えられる。ただし既存Reed–Muller符号を壊さない探索領域と、実際の多出力合成費用による比較が必要 |
| **Fast quantum simulation of electronic structure by spectrum amplification**、2025、arXiv:2502.15882 [G1] | Guang Hao Lowほか。Google Quantum AIを含む共同研究 | DF-THC、SOS、有限精度、因子・角度・重みの共同最適化 | DF-THCとスペクトル増幅は既にベースラインの枠組み。新規改善はパラメータと回路構造を実際に更新して初めて成立する |
| **Trading T gates for dirty qubits in state preparation and unitary synthesis**、Quantum 8, 1375 (2024)、初稿2018 [M1] | Guang Hao Low、Vadym Kliuchnikov、Luke Schaeffer。Microsoft Research / Azure Quantum等 | SelectSwapとdirty ancillaの幅・Toffoli交換条件 | 汎用表に対する費用の比較基準。未知の補助状態とその外部との絡み合いまで復元する必要がある |
| **Qubitization of Arbitrary Basis Quantum Chemistry Leveraging Sparsity and Low Rank Factorization**、Quantum 3, 208 (2019) [Q1] | Dominic BerryはMacquarie、Gidney/McClean/BabbushはGoogle、Mario MottaはCaltech | QROAM、clean ancilla、measurement uncomputeの費用 | forwardで残るjunkと、その消去を含めて数える。Mottaの後年のIBM所属をこの論文に遡って付けない |
| **Halving the cost of QROM**、2026-05、arXiv:2605.20334v1 [X1] | Danial Motlagh、Matthew Pocrnic。両者Xanadu | SelectCopy、sequential bit packets、連続する表ロードの共有 | 許可ゲートとの整合は取れるが、現在のサイズで汎用回路を丸ごと置換する費用上の根拠はない。節5参照 |
| **Halving the cost of QROM again via dense encoding**、2026-10、arXiv:2610.02321v1 [X2] | Danial Motlagh。Xanadu | dirty qubitのX/Z成分に2つの表値を符号化 | 論文構成のHadamardはKickmixで未対応。節4の具体的な拒否結果を参照 |

### 原論文と競技の精度基準は同一ではない

[G1]は`u,w`等を数値最適化し、有限bit精度も検討する。原研究で用いる化学的なエネルギー誤差評価を、競技の `error_1,error_2 <= 0.020 Ha` のFrobenius誤差検査に置き換える必要がある。また競技verifierは固定の対称性shiftを使い、提出された `H1_I` / `Hsym_lower` の変更を採用しない。原論文の自由度を全て使えるわけではない。

### 企業名の確認と関連研究

**NTT/NII:** Hanks、Estarellas、Munro、Nemotoの *Effective Compression of Quantum Braided Circuits Aided by ZX-Calculus*、PRX 10, 041030 (2020) [N1] は、誤り訂正されたtopological circuitの研究である。MunroにNTTの所属、他の主要所属にNIIが記載される。braidの時空間体積の削減率は、今回の論理Toffoli数や量子ビット数の削減率ではない。ZXの等価変形を使う場合も、許可ゲートへ戻し、論理費用を測る必要がある。

**IBM/QC Ware:** Cohn、Motta、Parrishの *Quantum Filter Diagonalization with Compressed Double-Factorized Hamiltonians*、PRX Quantum 2, 040352 (2021) [I1] は、Cohn/MottaがIBM Quantum、ParrishがQC Ware。数値的な因子再フィットの参考になるが、C-DFと今回のDF-THC-SOSは同一の形式ではない。この論文からC43候補の実現可能性や4033 loaderの削減は結論できない。

**Covestro/QC Ware:** *Accelerating Quantum Computations of Chemistry Through Regularized Compressed Double Factorization*、Quantum 8, 1371 (2024) [R1] は、誤差だけでなく正規化費用にも配慮する再フィットの参考。Oumarou/Scheurer/GogolinはCovestro、Parrish/HohensteinはQC Wareである。

**Fujitsu/Osaka STAR:** Akahoshiほかの *Partially Fault-tolerant Quantum Computing Architecture with Error-corrected Clifford Gates and Space-time Efficient Analog Rotations*、PRX Quantum 5, 010337 (2024) [F2] はearly-FTの物理アーキテクチャ研究であり、NISQ transpilerだけの話ではない。ただしanalog rotationの物理費用は本競技の固定費用に直接代入できない。今回のloaderには、同じFujitsuでも[F1]の方が直接関係する。

## 3. b/r行置換の正確な不変量

この節は論文の主張の転載ではなく、実際のverifier式からの導出である。ローカル参照は `official_sources/Inzainos/verifiers/dfthcsos/verify.py` の `optimizer_to_native` / `evaluate_words` と、同 `scoreinfra/dfthc_math.py`。追跡可能なmirrorは[S1]、実験receiptは `results/2026-11-14/chemistry_baseline_verify.json`。

記号の混同を避けるため、NPZの `W[r,b,c]` をここでは `w[r,b,c]`、`H2_I[r,c]` を `h[r,c]` と書く。verifierのnativeな定数係数は

\[
  \gamma_{rc}=h_{rc}-\sum_b w_{rbc},\qquad
  X_{rc}=\sum_b w_{rbc} u_{rb}u_{rb}^{T}
\]

となる。`u`は実際に回路が出力したinteger angle wordsをGivens treeで復号したベクトルを意味する。提出NPZの浮動小数点`U`だけを動かしても、回路の角度が動いたことにはならない。

### 各r内のb置換

各 `r` に独立な143要素の全単射 `pi_r` を選び、新しいindex `b` が旧index `pi_r(b)` を読むように

\[
  u'_{rb}=u_{r,\pi_r(b)},\quad
  w'_{rbc}=w_{r,\pi_r(b),c},\quad
  h'_{rc}=h_{rc}
\]

とする。integer angle tableの行 `76 + 143*r + b` を同じ置換で移し、NPZの `U` と `W` も整合させる。Givens treeと各行内部の角度は変えない。

このとき各 `(r,c)` について以下が不変となる。

- `X_rc`。
- `sum_b w_rbc`、従って `gamma_rc`。
- `sum_b abs(w_rbc)` と `h_rc`。
- したがって二体Hamiltonian、吸収後の一体Hamiltonian、`Lambda`、`E_SOS`、`E_gap`、`lambda_eff`。

量子ビット数や状態準備の所定費用の基になる `N,R,B,C,brot,J` も変わらない。**変えたいのは表のBoolean構造と、その合成Toffoli数である。** 旧addressへの変換回路を別途追加する必要はなく、因子表現そのものを再ラベルする。

### r全体の置換

8要素の全単射 `rho` で `r` を並べ替えるなら、`U[r,:,:]`、`W[r,:,:]`、`H2_I[r,:]`、対応する143行のangle blockを全て同時に移す。各`c`にわたる式と`r`の総和が保たれる。`H2_I`まで移す点が、r内b置換と異なる。

### 一体項76行の置換

verifierは、一体項の復号ベクトルを厳密な一体Hamiltonianの固有ベクトルに `|overlap|` の一対一対応で割り当てる。そのため一体項76行内の行順序も数学上は任意である。最初の実験ではこの76行を固定し、b置換だけに範囲を限定すると原因を追いやすい。

### 全ANGLEに同じ置換を適用する

各ANGLEは単独の値ではなく、前後のangle batchの差分

\[
  f_k(a)=g_{k-1}(a)\oplus g_k(a)
\]

を任意の出力 `z` にXORする（最初のbatchの前値は0）。同じ行置換を全15個の表に適用し、全15回路を整合的に再合成する。1回路だけaddressの意味を変えたり、浮動小数点`U`から再丸めして別のinteger tableを作ったりしない。

実数演算での不変性と、float64での最終PASSは区別する。現在は誤差の余裕が極小であり、加算順序、固有分解、対応付けの数値差を含め、変更後の公式再検証を要する。

### 4033の符号を壊さないことが追加条件

公開4033 notebook [K1] の説明は、batch 3〜14について次の構造を述べている。

- 各wordのbit 0が、address下位4bitのaffine関数。
- batch内の5wordをXORしたbit 1もaffine。
- 同じXORのbit 2は次数2以下。
- 全75角度列に関するtop-bit gaugeも使用。

任意の `b` 置換はこれらの構造を一般に保たない。従って「精度が不変だからランダムな行swapは有望」とは結論しない。元4033を再現できる合成器を確保し、実Toffoli数で比較することを先に置く。取得済み公開notebookは固定assetをコピーする版で、元の符号化ローダー合成器はまだ特定できていない。

同時に進めたsource担当のread-only ANF監査では、元4033 NPZの完全16行block 76個について、batch 3〜14の上記3条件の違反係数は全て0だった。affine係数はhigh-address blockごとに異なり、各wordで26〜32種類あるため、条件はblock-localである。再現コードは [audit_chemistry_4033_structure.py](audit_chemistry_4033_structure.py)、結果は [chemistry_4033_structure_audit.json](chemistry_4033_structure_audit.json)。このreceiptは元NPZのSHAと全15 KMBのSHA/static countも記録している。

絞り込んだ候補として、同一rに完全に含まれる16-address block内だけで下位4bitの**可逆affine変換**を行い、rや一体項との境界をまたぐblockと最後の不完全blockは固定する案がある。該当する完全blockは64個、移動可能な行は1024行、固定する行は196行。Boolean関数へのaffineな入力置換は次数を増やさず、同じ置換はword間XORとも可換なので、**確認した3つのlocal Reed–Muller条件は数学的に保存される**。ただしtop-bit gaugeや合成器の全構造まで同じ費用で保存されるとは示しておらず、**実合成費用の改善は未確認**。これは次の小規模調査案であり、実装済み削減ではない。最後の4行 `1216..1219` は不完全blockなので次数監査の主張に含めず、候補でも固定する。

## 4. Kickmixの許可ゲートとの整合

一次資料はQualtran公式の命令一覧[S2]、形式説明[S3]、binary opcode一覧[S4]。形式は、計算基底を混ぜる単独Hadamardなどを扱う一般量子回路形式ではなく、位相付き可逆Boolean演算とmeasurement uncomputeを扱う。

| 種類 | 関連する命令 |
|---|---|
| 可逆Boolean演算 | `X`, `CX`, `CCX`, `SWAP`, `CSWAP` |
| 位相 | `Z`, `CZ`, `CCZ`, `NEG` |
| 測定・初期化 | `HMR`, `R` |
| 一般Kickmixには存在するがANGLEでは拒否 | `Z_POW` |
| Kickmix 1.0.0に存在しない | 単独`H` |

測定結果に応じるclassical conditionも利用できる。ANGLE契約は任意 `z` に対する `|a>|z> -> |a>|z XOR f_k(a)>` であり、全workspaceを各回路の終端で0へ戻し、残留位相をなくす必要がある。`HMR`で測って捨てれば良いわけではなく、phase feedbackも必要。

### SelectCopy: ゲート集合としては実装可能

[X1]のtable load、条件付きcopy、restoreは `X/CX/CCX` と一時ANDから構成できる。一時ANDの消去は `HMR` と条件付き `CZ` で実現できるので、単独`H`を必要としない。

論文の定理は出力0からのloadを記述する。今回の任意`z`のXOR契約には、出力を使って条件を変えず、各outputへのXORとして実装することで拡張する必要がある。特にpacketのrestoreを含めて `z -> z XOR f(a)`、workspace復元、位相0を証明・検証する。出力0だけの成功を契約適合とみなさない。

別々のANGLE境界をまたいでdirty状態を保持してload/unloadを共有する案は、現競技のscratch契約にそのままでは合わない。40bitのpacket化を一つのANGLE内で行う場合は、この境界問題を回避できる。

### Dense encoding: 論文どおりの移植は具体的に拒否される

[X2]はdirty qubitに `P=X^a Z^z` を作用させ、controlled readとの交換子でoutputへ `Z^f` を作り、outputの前後にHadamardを置いて `HZ^fH=X^f` に変換する。

2026-11-14に、実験環境の **kickmix 1.0.0** で次の最小パース確認を行った。

```python
import kickmix as km
km.Circuit("H q0\n")
```

結果:

```text
ValueError: Failed to parse kmx line (unknown operation name): 'H q0'
```

公式opcode一覧にも`H`はない。`HMR`はX基底測定とresetを伴う非ユニタリ操作であり、これを`H`の代わりに使うことはできない。従って、**現在の競技ゲート集合で論文をそのまま提出する経路は不可**。

この結論はdense encodingという量子アルゴリズム一般の否定ではない。また、最終的なXOR写像を別のH-freeな可逆回路で実現できないという主張でもない。そのような再合成で論文の費用優位を保てることは、ここでは示していない。

## 5. SelectCopy / dense encodingの軽量費用確認

表の構造を無視した論文の整数費用式を、そのまま現在のサイズに適用した。回路生成、シミュレーション、大規模探索は実行していない。

共通条件:

- 行数 `n=76+8*143=1220`、出力幅 `b=5*8=40`。
- selection 11量子ビット、全体上限128量子ビット。
- packet幅 `mu=1..40`、block幅 `L` は2の冪。
- paperが指定するclean helperを追加し、`11+40+dirty+helper <=128` で絞る。

### SelectCopy: [X1] Appendix A, Eq. (9)

`m=ceil(b/mu)`、`q=ceil(n/L)` とすると

\[
\begin{aligned}
T_{\mathrm{copy}}&=(m+1)(q+L-3)\\
&\quad +(L-1)\bigl[\mu(\lfloor b/\mu\rfloor+1)+(b\bmod\mu)\bigr],\\
D_{\mathrm{copy}}&=\mu(L-1),\\
A_{\mathrm{copy}}&=\max(\lceil\log_2 q\rceil,\log_2 L).
\end{aligned}
\]

幅条件を満たす78設定のうち、この費用式の最小は **1098 Toffoli / ANGLE**。`mu=20,L=4`、dirty 60、clean helper 9、総量子ビット120。次点は1101、1104、1284、1291 Toffoliだった。

### Dense encoding: [X2] Eq. (9)

`m=ceil(b/mu)`、`q=ceil(n/(2L))` とすると

\[
\begin{aligned}
T_{\mathrm{dense}}&\le(m+1)(q+L-3)+2L(b+\mu),\\
D_{\mathrm{dense}}&=\mu L,\\
A_{\mathrm{dense}}&=\max(\lceil\log_2 q\rceil,\log_2(2L)).
\end{aligned}
\]

幅条件を満たす66設定のうち、掲載された**上界式**の最小値は **1048 Toffoli / ANGLE**。`mu=14,L=4`、dirty 56、clean helper 8、総量子ビット115。ただし節4の`H`不対応のため、これは実行可能なKickmix候補ではない。

### 判断の範囲

既存は15 ANGLE合計4033、平均 **268.8667 Toffoli / ANGLE**。上の汎用費用式だけからは、全表を丸ごと置換する理由は得られない。1098や1048は実際に生成した回路の計測値ではなく、論文の式の評価値である。特にdenseの値は上界の最小値であり、最小必要Toffoliの下界ではない。

定数bit、符号、word間共有積、データ依存圧縮を組み込んだ別構成の可能性は残る。論文の大きな表に対する「半減」「約4倍」を、そのまま4033へ掛けない。

## 6. 固定7/6bit丸め表に関する既存結果

基準表からの単純な丸め6通りについて、正確な参照Hamiltonianへ射影して求めた `error_2` の必要下限は次の通り。

| brot | 丸め | exact-reference relaxed error_2下限 (Ha) |
|---|---|---:|
| 7 | half-up | 0.20750110794685914 |
| 7 | nearest-even | 0.21487732418319824 |
| 7 | floor | 0.21143624827601598 |
| 6 | half-up | 0.3032545517751796 |
| 6 | nearest-even | 0.32196085510666 |
| 6 | floor | 0.5037432774122866 |

許容は0.020 Ha。この下限は、固定した復号ベクトルの張る空間で、実際の因子制約より広い自由度（r間結合、Cの制限緩和）を許しても残る誤差である。従って**この6表を固定したままW/H2_Iを再フィットしても許容誤差へ届かない**という強い数値的証拠になる。float64の射影計算であり、形式証明や区間演算証明とは区別する。

限定事項:

- 全ての7bit/6bit角度表を否定した結果ではない。角度の離散値そのものを再学習する候補は含まれない。
- Givens tree、R/B等も変えた全探索の最適性を示していない。
- 既存のC43候補がFAILだったことは、他の全てのC43因子の不可能性を意味しない。
- 固定角度に対するKKT点、局所探索の停止、限定gauge探索での無改善を、大域最適性の証明として扱わない。

詳細と再現スクリプトは既存の `chemistry_report.md`、`chemistry_experiment_summary.json`、`inverse_v2_chemistry_exact_projection.py` を参照。本調査で計算し直してはいない。

## 7. 次の最小実験と採否条件

1. **元4033を再現する合成器を探し、identity tableで同じ費用を再現する。** 固定assetのコピーだけでは新しい表を比較できない。見つからない場合、任意行swapの大規模SAを先に回さない。
2. **既存のRM監査を候補比較へつなげる。** 元表の完全16行blockでは3条件がblock-localに成立することが確認された。候補表でも同じ判定を使い、境界・不完全blockを固定する。符号条件のPASSと合成費用の改善を別々に記録する。
3. **合法な小さい置換集合だけを実合成で比較する。** identity、少数のb内swap、符号条件を保つと確認できたaffine変換を対照にする。Hamiltonian不変だけでなく、片道総Toffoliが4033未満であることを採用条件にする。
4. **SelectCopyは全面移植を優先しない。** 特定ANGLEの部分表でデータ依存の費用が既存を下回る見込みが出た場合のみ、小さなprimitiveを実装し、任意出力・scratch・位相を確認する。
5. **dense encodingのそのままの移植は停止する。** 新しいH-free構成と費用根拠が出るまでは、未対応ゲートを含む全回路の生成に計算を使わない。
6. **bitwidth削減を再開するなら角度自体を動かす。** 6個の固定丸め表に対するWだけの再フィットを繰り返さず、量子化を考慮した角度/重み共同最適化を、小さな予算と誤差の早期棄却条件で行う。

候補採用には、正しいinteger words、任意zへのXOR、各ANGLEのscratch0と位相0、公式誤差判定、実際の `lambda_eff*T*Q` 改善をそろえる。論文の改善率や代理目的の低下だけでスコア改善と報告しない。

## 8. 一次資料URL

### 論文

- **[F1] Fujitsu・database reordering:** https://arxiv.org/html/2604.06578v1 （抄録: https://arxiv.org/abs/2604.06578 ）
- **[G1] DF-THC/SOS/spectrum amplification:** https://arxiv.org/html/2502.15882v1 、Google公式: https://research.google/pubs/fast-electronic-structure-quantum-simulation-by-spectrum-amplification/ 、出版DOI: https://doi.org/10.1103/pb2g-j9cw
- **[M1] Microsoft・SelectSwap:** https://quantum-journal.org/papers/q-2024-06-17-1375/ 、https://arxiv.org/abs/1812.00954
- **[Q1] QROAM:** https://quantum-journal.org/papers/q-2019-12-02-208/ 、https://arxiv.org/abs/1902.02134 、公式実装説明: https://qualtran.readthedocs.io/en/latest/bloqs/data_loading/qroam_clean.html
- **[X1] Xanadu・SelectCopy / sequential packets:** https://arxiv.org/html/2605.20334v1 、著者側解説: https://pennylane.ai/blog/2026/05/halving-the-cost-of-qrom
- **[X2] Xanadu・dense encoding:** https://arxiv.org/html/2610.02321v1 、著者側解説: https://www.xanadu.ai/blog/halving-the-cost-of-qrom-again
- **[N1] NTT/NII・ZX braid compression:** https://journals.aps.org/prx/abstract/10.1103/PhysRevX.10.041030 、NTT公式: https://group.ntt/en/newsrelease/2020/11/12/201112a.html
- **[I1] IBM/QC Ware・C-DF:** https://journals.aps.org/prxquantum/abstract/10.1103/PRXQuantum.2.040352
- **[R1] Covestro/QC Ware・RC-DF:** https://quantum-journal.org/papers/q-2024-06-13-1371/ 、https://arxiv.org/abs/2212.07957
- **[F2] Fujitsu/Osaka・STAR:** https://arxiv.org/abs/2303.13181 、https://doi.org/10.1103/PRXQuantum.5.010337 、公式: https://info.archives.global.fujitsu/jp/news/2024/08/28.html

### 実装・競技の契約

- **[K1] 4033 coded-word chemistry notebook:** https://www.kaggle.com/code/maoxin123/qcc-v27-4033-toffoli-coded-word-chemistry 。取得済み内容は `official_sources/maoxin_4033_pull.json`。公開dataset: https://www.kaggle.com/datasets/maoxin123/qcc-chemistry-4033-toffoli-loaders
- **[S1] 使用した競技verifierのmirror:** https://github.com/Inzainos/quantum-circuit-compilation/tree/4277c767440df9efb8a90860ae2ce47028e46ba9/verifiers/dfthcsos 。固定commit `4277c767440df9efb8a90860ae2ce47028e46ba9`のローカル取得ファイルを参照。mirrorであり主催者自身のrepositoryと同一視しない。
- **[S2] Qualtran公式Kickmix命令一覧:** https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_instructions.md
- **[S3] Qualtran公式Kickmix形式・シミュレーション範囲:** https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_format.md
- **[S4] Qualtran公式Kickmix binary opcode一覧:** https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_binary_format.md

論文URLは上記版、Qualtranの`main`文書は調査日時点を確認したもの。runtimeでの拒否結果はkickmix 1.0.0に対する具体的な確認である。
