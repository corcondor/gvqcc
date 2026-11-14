# DQIの作業領域縮約：寿命解析、部分積、可逆な入力置換

2026-11-15. 対象は検証済み `e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7`、Q=889、平均Toffoli相当数382115.5671582031。

**この調査では、新しい量子ビット削減候補は採用していない。** 量子ビットの番号付けだけを変える案と、24bit積の前半だけを計算して元の入力を測定する案を実回路から検証した。後者には可逆性の問題があり、単に積の出力ランクが24であるという指摘より強い、任意の固定分割についての反例を導いた。部分出力の具体的な演算数も抽出した。

## 1. 文献と今回への対応

| 一次資料 | 読んだ内容 | 現行回路に対する判断 |
|---|---|---|
| Parent–Roetteler–Svore, [Reversible circuit compilation with space constraints](https://arxiv.org/abs/1510.00377) | インプレース化、依存関係、消去・再計算による空間時間交換 | 原理として適合する。ただし現回路はすでに840本のsyndrome線を作業データとして再利用し、単純な計算履歴保存ではない。 |
| Paradis–Bichsel–Vechev, [Reqomp](https://quantum-journal.org/papers/q-2024-02-19-1258/) / [全文](https://quantum-journal.org/papers/q-2024-02-19-1258/pdf/) | Ancilla依存グラフを連結成分に分け、再計算を含む消去順序を選択。§4、Fig.8のトレードオフ | 同時に必要な中間値の境界を特定する用途に有効。論文の削減率をすでに再利用済みのQ889に乗じることはできない。 |
| Su–Zhou–Feng–Ying, [Borrowing Dirty Qubits in Quantum Programs](https://arxiv.org/html/2508.17190v1) | Theorems5.3/5.4の安全性、§6の検証。借用線は未知状態と参照系への絡み合いを含めて復元する | `compute→SWAP→HMR`で使うclean積出力を、単にidleなsyndrome線に置き換えることはできない。 |
| Liu–Zhou–Meng, [Quantum Uncomputation of Clean and Dirty Ancilla Qubits](https://arxiv.org/html/2608.09578v2) | §5の構文規則、§6の正規形、依存サイクルやHadamardに関する適用制約。2026-10-11版 | 生きた入力との相互依存を含む変換を検証する方向として関連。ただし測定を含む現在の全KMBをそのまま受ける保証はない。 |
| Xuほか, [Bona](https://arxiv.org/html/2608.08765v1) | §3の安全な借用条件、structured borrow区間とidle線のスケジューリング | 先に `U=I_borrowed ⊗ V` を満たす部品を作る必要がある。現在の測定消去出力はこの契約を満たしていない。 |
| Vandaele, [Quantum binary field multiplication with subquadratic Toffoli gate count and low space-time cost](https://arxiv.org/html/2501.16136v1) | §2.2のCCZ多項式、§3のKaratsuba型分解と空間時間交換 | 双線形写像の再合成に関連する。対象の99-Toffoli GF(2^24)核に対しては、論文の漸近量だけで改善は判断できない。 |

上表は今回の実装選択との対応であり、文献のベンチマーク結果を今回の成果として記載していない。

## 2. 完全な命令列に対する寿命監査

`theory_ancilla_lifetimes.cpp` はKMBを読み取り専用mmapで走査する。無条件のR/HMRでのみscratch線の区間を終了し、明示的な条件付きR/HMRおよびPUSH条件内のR/HMRでは終了しない。q0〜q839はABIの入力・出力として固定する。

| 項目 | 実測 |
|---|---:|
| 全命令数 | 59,378,866 |
| 量子演算を含む命令 | 32,869,043 |
| resetで分けたscratch区間 | 29,627 |
| 無条件R/HMR | 35,360 |
| 解放と扱わなかった条件付きR/HMR | 84,220 |
| 最大条件スタック深さ | 2 |
| 最大同時区間数 | 49 |
| この区間モデルでの最小Q | 840+49=889 |
| 最初の49区間同時点 | KMB index17,630,651 |
| 最大区間数が続く区間の個数 | 1,570 |

区間グラフでは最大クリーク数と彩色数が一致する。したがって、**この保守的な区間分割を維持し、線番号だけを再割当てする方法ではQを減らせない**。証拠となる49区間を `theory_ancilla_lifetimes_result.json` に保存した。

これは「量子的に独立な49状態が必須」という下限証明ではない。既知ゼロの制御線や代数的な相殺まで追跡していないため、意味を解析して区間を縮める、演算順序を変える、再計算する、新しい回路に合成する余地は残る。1,570個を独立した乗算回数と数えることもできない。

無条件reset、明示条件reset、PUSH内reset、二重PUSH内resetの6つの小回路を独立に確認した。`theory_ancilla_check_result.json` に結果と入力hashを保存した。

## 3. 実際の99-CCX積を、出力部分ごとに分けると何個か

以前に認証した実KMBブロックの操作は

\[
z\leftarrow z\oplus \overline{u}v,
\qquad u,v\in K=\mathbf F_{2^{24}},
\]

である。共通の表示は

\[
K=\mathbf F_{2^{12}}[\theta]/(\theta^2+\theta+2048),
\quad \overline{a+b\theta}=(a+b)+b\theta.
\]

`theory_ancilla_tiling.py` は元のCX/CCX列から入力の線形形式と最終出力の係数を取り出す。すべての24×24=576個の基底入力対で有限体乗算との一致を確認した。元の99項が独立した積の和としてどの出力に寄与するかを確定した上で、射影後に不要な項だけを省いた数は次の通り。

| 出力の分割 | 既存99項を射影した個数 | 合計 | 99との差 |
|---|---:|---:|---:|
| 先頭1bit / 残り23bit | 50 / 99 | 149 | +50 |
| 先頭2bit / 残り22bit | 75 / 99 | 174 | +75 |
| 先頭6bit / 残り18bit | 96 / 99 | 195 | +96 |
| 下位12bit / 上位12bit | 99 / 90 | 189 | +90 |

出力bitを選び直した1bit射影では、既存分解の最小は36項。24本の各出力bitの双線形行列はいずれもrank24だった。1出力bitを左右の線形形式の積として直接再合成する場合は24積で実現できるが、これは入力を維持したままの出力計算についての数である。

12bitずつに分ける場合、より簡単な別の分解もある。

\[
\begin{aligned}
\operatorname{low}(\overline{u}v)&=(a+b)x+2048\,by,\\
\operatorname{high}(\overline{u}v)&=bx+ay.
\end{aligned}
\]

各行をrank42のGF(2^12)積2個で実装すると、84+84=168 CCXで両半分を計算できる。**189は最適値ではなく、既存分解を射影した特定方式の数である。** 168も一般的な最適性を主張していない。

## 4. 部分出力を計算した後、古い入力を捨てられるか

ここに追加の条件がある。出力12bitを作っても、入力48bitと新しい出力をすべて維持すれば、24出力の同時保存を単純に12へ縮められない。新しい部分出力を入力の代わりに使うなら、その交換が可逆である必要がある。

### 固定した部分入力・部分出力では必ず特異な乗数がある

Kを24次元の二元線形空間とする。捨てたいk次元の入力部分空間をV、保持するkbitの出力射影をPとし、0<k<24とする。任意に

\[
0\ne v\in V,\qquad 0\ne w\in\ker P
\]

を選び、乗数をa=w/vとすれば、aは非零なのにP(av)=0となる。したがって、0とvは同じ部分出力を持ち、残りの元入力も同じである。**固定されたkbit出力だけでkbit入力を置換する写像は、全ての非零乗数について可逆にはならない。** 実ブロックが共役乗算ならu=conjugate(a)を選べば同じ議論が成り立つ。

具体例として、u=0x1001=1+thetaの場合、conjugate(u)=thetaである。v=0とv=1はどちらも下位12bitの積が0だが、上位12bitは0と1となる。先に下位12bitのvを捨てれば、後半を区別する情報がなくなる。

自然な12+12分割において、最初のブロック係数はa+bであり、a=b≠0の4,095個のsourceで特異になる。全非零sourceのうちの割合は厳密に1/4097である。これは一様な非零field要素を仮定した割合で、**現在のdecoderでの実際の発生確率ではない**。既存の到達状態がこの集合を避けるという証明も得ていない。

`theory_ancilla_tiling_result.json` にはk=1〜23それぞれの具体的な衝突を保存した。これは固定部分出力による早い測定消去を退けるもので、入力依存のpivotを持つ方式を否定しない。

### 次に設計するなら、pivotと位相の管理が必要

乗数a+b thetaのbが非零なら、r=a/b、d=r²+r+2048と置くと、dも非零である。target(x,y)に対し

1. x←x+(r+1)y
2. y←dy
3. y←y+rx
4. x,yを交換し、両方をb倍

で正しい乗算になる。これは24bit同時出力を避けるための具体的な代数分解である。ただしrの可逆生成、b=0の場合のpivot、sourceの復元、消費型scalar積のHMR位相を含めて初めて正しい部品になる。

現行のrank42 scalar積、66T deferred scalar inverseをそのまま組み合わせると、rの生成・source復元に複数の逆元や積が加わる。これらを省いた168Tの出力計算だけを、新しい実行費用として扱うことはできない。今回、このpivot付き部品のnative回路は生成していない。

## 5. 全体のQ²Tに対する採用条件

Rと他のタスクを固定し、Qをdだけ減らす場合、許される追加平均Toffoliは

\[
\Delta T<T\left[\left(\dfrac{889}{889-d}\right)^2-1\right].
\]

| 削減Q | 新Q | 許される追加平均Toffoli（厳密にこの値未満） |
|---|---:|---:|
| 1 | 888 | 861.1052 |
| 2 | 887 | 1,725.1245 |
| 6 | 883 | 5,210.6067 |
| 11 | 878 | 9,634.6276 |
| 12 | 877 | 10,528.5240 |

仮に12bitずつの再合成が99→168へ変わり、他の追加費用がないなら1回につき69増えるため、152回までがQを12減らした利益の範囲に入る。153回では超える。しかしpivot処理と位相清算はまだ含まれておらず、全体でQが本当に877以下になることも別途必要である。既存99項を射影する189方式なら追加90なので116回まで。この回数は設計上の予算であり、今回のKMBに存在すると測定した対象回数ではない。

また実ソースには24-helperを要する積だけでなく、12bit normを保持したまま12-helper inverseを使う箇所、24-helper inverse/phase、別構造のphase部品がある。一つの積だけを細くしても最大Qは変わらない。

幅削減の別段階では、既存の `after_v3/blocks/quotient_phase63.py` が63T/18helpersを実装しており、現行 `v5_cubic_phase20/quotient_phase62.py` の62T/22helpersと比べて、1Tを払って4helpersを減らす交換が可能である。これは公開ソースに元からある部品で、今回新しく得た削減ではない。24-helperピークを解消できた後に初めて全体の幅に効く。

## 6. 再現

```bash
python theory_ancilla_check.py
g++ -O3 -std=c++17 theory_ancilla_lifetimes.cpp -o /tmp/theory_ancilla_lifetimes
/tmp/theory_ancilla_lifetimes ../dqi_inputs/821_ccx480_gauge128.kmb 840 > theory_ancilla_lifetimes_result.json
python theory_ancilla_tiling.py
```

元KMB、既存の回路生成器、検証器、既存の結果は変更していない。この結果は縮約案の適用条件と費用を明確にするためのもので、全回路の追加公式検証や新Public Scoreを意味しない。
