# NTT・富士通の論文と今回のコンペへの適用条件

調査日: 2026-11-14。論文本文に記載された所属で確認した。以下の適用案は本プロジェクト側の推論であり、論文がこのコンペでの改善を実証したものではない。

## 最優先: 富士通の QROM アドレス順序探索

[Database Reordering for Compact Grover Oracles with ESOP Minimization](https://arxiv.org/html/2604.06578v1)、Yusuke Kimura / Yutaka Takita、2026-04-08。両著者は Fujitsu Limited。

手法は、データ二件のアドレス交換、出力 bit ごとの ESOP 最小化、cube 内の指定 literal 数の合計による評価を繰り返す焼きなまし法。実装には [simanneal](https://github.com/perrygeo/simanneal) と [EXORCISM](https://github.com/boschmitt/exorcism) を使用し、標準探索予算は 1,000 手。単なる CNOT 深さの研究ではなく、非 Clifford コストを狙っている。ただし目的関数は AND/Toffoli の実数ではなく proxy であり、CNOT に対応する項も数える。論文内の分解後 T-count との相関検証は N=8 の小規模例である。

論文専用の公開再現コードは今回の調査では確認できなかった。上記二つは著者が明記した公開依存ライブラリ。EXORCISM は BSD-2-Clause、最大 32 入力、単一出力、PLA 入力、don't-care を無視する実装である。したがって複数出力の共有積を持つ既存 4033 ローダーより有利とは限らない。

### コンペへ移せる自由度

公式検証器の内部数式は

\[
X_{rc}=\sum_b w_{rbc}u_{rb}u_{rb}^{\mathsf T}.
\]

各 r の b を置換する際、次を同じ置換で移動すれば、実数演算上は X とハミルトニアン、lambda の式を保存できる。

- 提出 NPZ の `U[r,b,:]`
- 提出 NPZ の `W[r,b,:]`（検証器内部では小文字の w）
- 角度表の `76 + r*143 + b` 行、およびそれをロードする回路

この b 置換では `H2_I` はそのまま。先頭 76 行の一体項はそのまま保持する。r ブロック全体を置換する場合は `U`、`W`、`H2_I` の r 軸と角度表の該当ブロックを同時に移す。

これは局所連続最適化とは異なる探索軸である。浮動小数点の加算順は変わるため、最終候補は公式検証器でも確認する必要がある。単に既存ローダーの出力を読み替えるだけでは新しい指定関数を実装できず、回路の再合成が必要になる。

### 小さく始める実験

1. 元の並び順で既存生成器が 4033 コストを再現することを確認する。
2. 最初は r ブロック交換や各 r 内の少数の b 交換を候補にする。先頭 76 行は固定する。
3. proxy を使うなら共有積・補助量子ビットを反映する。最終順位は実際に再合成したローダーの Toffoli 数と量子ビット数で決める。
4. 元の並びを常に候補に残し、改善候補だけ公式の `lambda_eff * toffoli * qubits` で検証する。

全出力を独立に ESOP 化するだけでは共有積を壊しうる。論文の改善率を現在の 4033 ローダーに外挿しない。

## NTT: 補助量子ビットを使わない整数加算

[Quantum Addition Circuits and Unbounded Fan-Out](https://arxiv.org/pdf/0910.2530)、Yasuhiro Takahashi / Seiichiro Tani / Noboru Kunihiro、2009 年プレプリント。前二者の所属は NTT Communication Science Laboratories、三人目は東京大学。

補助量子ビットなしの線形サイズ整数加算と、深さ・補助量子ビットの交換関係を扱う。`7n-6` は総ゲートサイズであり、Toffoli 数ではない。今回なら `invsqrt` の固定小数点加算器を比較する参考になる。DQI の GF(2^12) の加算は XOR なので、整数の carry 加算器を移す用途ではない。古い基本構成であり、現行回路に対する優位性は別に測定する必要がある。

## NTT: 制御回転の Clifford+T 合成

[Multi-qubit controlled gate synthesis without T-count overhead in the small-error limit](https://arxiv.org/html/2603.14202v3)、Soichiro Yamazaki / Seiseki Akibue / Kaoru Sano、v3 は 2026-10-04。Yamazaki は東京大学、Akibue と Sano は NTT 所属。

制御 SU(2) ゲートを個別に近似・分解する負担を減らす研究。一制御の場合に、最も高価な分岐の近似 T-count に定数の上乗せで合成できる構成を示す。物理的な T-count 削減と、コンペが `Z_POW` に与える固定コストは別である。実際の許可命令数や回転数を減らせる場合に限って今回の採点へ結び付くため、直接移植の優先度は低い。

## 富士通: 化学ハミルトニアンの表現とコストを同時に最適化

[Enabling Chemically Accurate Quantum Phase Estimation in the Early Fault-Tolerant Regime](https://arxiv.org/html/2603.22778v1)、Shota Kanasugi / Riki Toshio / Kazunori Maruyama / Hirotaka Oshima、2026 年プレプリント。全著者の所属に Fujitsu Research を確認。

単一アンシラの Trotter 型 QPE と部分ランダム化を前提に、LCU 係数分布を変える unitary weight concentration を提案する。表現と実行コストを一緒に最適化する考え方は参考になるが、今回の DFTHC-SOS の採点方式とは異なる。公式検証器は対称性シフトを固定値に置き換えるため、同論文の BLISS や STAR の資源削減をそのまま提出に持ち込むことはできない。

## 調査上の区別

- 上記の T-count は物理的な T ゲート数を指す。コンペの Toffoli-equivalent や量子ビット積コストとは区別する。
- 今回確認できた NTT・富士通の論文に、現在の DQI の共有 Toffoli 乗算や measurement uncompute をそのまま置換できる実証済みの手順はなかった。
- `Classical variational optimization of PREPARE circuit ...` は QunaSys / 大阪大学 / 理研の論文で、富士通論文として分類しない。
- 暗号演算の論文に現れる NTT は number-theoretic transform の略称であることが多く、企業 NTT と混同しない。
