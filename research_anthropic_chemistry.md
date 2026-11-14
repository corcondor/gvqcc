# Anthropicの量子回路研究と、4033 chemistry・e46 invsqrtへの適用判断

調査日: 2026-11-14 UTC。対象論文: Gu, Kemeny, Yelin, Lukin, *Discovering state-of-the-art quantum circuits with large language models*, arXiv:2610.22367v1、2026-10-15提出。[論文本文][paper]・[Anthropic解説][blog]・[著者の公開実装][repo]を照合した。

## 1. 結論

**今回の4033ローダーや46量子ビットの逆平方根回路に、そのまま置き換えられる改善は確認できなかった。** 論文の化学タスクはFe₂S₂の疎なPauli表を使うalias–SELECT回路であり、競技のFeMoco76軌道DF-THC-SOSとは入力・出力・評価対象が異なる。論文の逆平方根を含むタスクも、座標から計算した数値を整数レジスタへ加算するもので、競技の高精度な位相操作と同じ仕様ではない。

ただし、公開コードから持ち込める具体的な設計手法はある。優先度が高いのは、共通制御を持つ二次位相式の一括簡約、最終的な整数演算に合わせた係数フィット、複数の表出力にまたがる位相補正の共有である。いずれも、現在の回路に未適用かを調べてから候補化する必要がある。

論文の反復データ圧縮については、今回実データで小さな監査を1回実施した。4033の15本すべてで、1220行の40bit差分ワードが全て異なった。**純粋な行順変更だけで、同一の全出力ワードを繰り返す構造は作れない。** 部分ビットの共有やReed–Muller構造までは否定していない。スクリプトは[audit_anthropic_repeated_rows.py](audit_anthropic_repeated_rows.py)、結果は[anthropic_repeated_rows_audit.json](anthropic_repeated_rows_audit.json)。提出候補や既存の数値報告は変更していない。

## 2. 「15万倍」の対象と、今回の研究成果

[Anthropic解説][blog]の約15万倍という数字は、FeMocoの同じ54軌道モデルについて、2017年から2025年までの研究分野全体の進歩を説明するもの。推定Toffoli数がおよそ50兆から3.4億へ減ったという歴史的比較であり、Claudeが今回15万倍にしたという結果ではない。競技で使う76軌道の数値とも同一ではない。

今回の論文で化学の改善として比較しているのはFe₂S₂の部分回路である。著者リポジトリの[化学結果][chem-results]には、基準の55,473 Toffoli・139 peak qubitsに対して、発見回路14,978 Toffoli・126 peak qubitsが記録される。積は7,710,747から1,887,228、約4.09倍の改善。これらは著者の評価器での結果であり、Kaggleでの提出結果ではない。

## 3. 化学タスクの比較

| 項目 | 論文・公開実装 | 現在の競技基準 |
|---|---|---|
| 対象 | Fe₂S₂、30電子・20空間軌道 | FeMoco、113電子・76空間軌道 |
| 表現 | 41,052項の疎なPauli Hamiltonian | DF-THC-SOS、`R=8, B=143, C=44` |
| 提出・最適化対象 | alias lookup、選択Pauliの適用、lookupの消去 | 因子NPZと15本のANGLE回路 |
| 回路の入出力 | 16bitアドレス、16bit比較値、40bit系レジスタ。アドレスと比較値は復元し、選択した符号付きPauliを系へ適用 | 11bit選択レジスタに応じて5個の8bit角度差分を出力し、補助量子ビットを消去 |
| 精度条件 | `1e-4 Ha`未満の係数を事前に除いた固定Pauli表。16bit alias確率の固定表に対して回路の作用を一致させる | 固定参照とsymmetry shiftに対し`error_1,error_2 <= 0.020 Ha`などを満たす |
| 費用 | 著者評価器でのToffoli数 × peak live qubits | `lambda_eff × T_total × Q_total` |
| 現在値 | 14,978 × 126 = 1,887,228 | 46.906589508623554 × 14,728 × 427 = 294,988,786.8708443 |

左列の詳細は[task仕様][chem-task]と[契約データ][chem-contract]、右列はローカルで通した[chemistry_report.md](chemistry_report.md)・[結果JSON](chemistry_experiment_summary.json)による。ユーザーの別環境で報告された`lambda_eff=46.905894137`の配列は未取得なので、今回の基準をその値からの改善として扱わない。

論文SI IVは、連続角Givensを含む完全なDF-THC walkの検証が著者らの検証モデルの対象外であることを述べ、疎なPauli形式を選んでいる。[paper] したがって、Fe₂S₂の回路をそのままFeMocoのANGLEファイルへ置くことはできない。競技ではstate preparationの費用の一部が次元から所定の式で決まり、独自alias回路への差し替えを提出するインターフェースもない。

### 実際に何を最適化したか

[発見回路の実装説明][chem-design]では、二つの自由度を組み合わせている。

1. **選択演算の構造。** Pauli演算子を、共通のClifford変換で行き来できるグループにまとめる。係数が近いことを根拠に同一視するのではなく、演算子の関係を厳密に保ち、係数と符号はそれぞれ保持する。
2. **alias表の表現。** 同じ丸め済み確率分布を表す複数のalias表から、同じ値が連続して現れやすいものを選び、不要になったアドレス分岐を省く。

これに、同じアドレスに依存する複数の測定後位相をまとめて補正する方法と、途中値を保持する場所の探索を組み合わせている。表と回路を一緒に設計する発想は有効だが、競技の角度表は任意のalias割当表ではない。

現在の4033基準ではANGLE片道4,033、往復8,066 Toffoliが総14,728の約54.8%を占める。ただし、その小ささは既に符号化された角度表に依存している。[構造監査](chemistry_4033_structure_audit.json)では、batch 3〜14の低4アドレスbitに関するaffine/二次Reed–Muller条件を確認している。任意の行順変更はこの条件を壊し得る。bラベルの置換がHamiltonianを保つ条件と、完全16行ブロック内に制限する探索案は[既存の研究対応表](research_chemistry_qrom.md)を参照。

## 4. 実データで行った、反復ワード圧縮の限定監査

監査対象は元の4033 factorizationの`angle_words`。SHA-256は以下に固定した。

```text
3f864a7aeaa4d78984c8822761782b63be2d553b229f487e79640a73be147c44
```

各ANGLEの契約に合わせ、行`a`に対する40bitワードを

\[
f_k(a)=g_{k-1}(a)\mathbin{\oplus}g_k(a),\qquad g_{-1}(a)=0
\]

として計算した。`g_k`は当該batchの5個の8bit word。生の角度値だけの重複判定ではない。

| 監査項目 | 結果 |
|---|---:|
| 対象 | 15表 × 各1220有効行 |
| 表ごとの異なる40bit差分ワード数 | 全表で1220 |
| 重複ワードによる余剰行 | 0 |
| 全0の差分ワード | 0 |
| `(0,1), (2,3), …`の整列した隣接組で同じワード | 0 |
| 完全な整列済み2〜1024行ブロックで前半・後半が同じ | 0 |
| 実行時間 / peak RSS | 約0.072秒 / 23.80 MiB |

同一の行置換を全batchへ適用すると、各`f_k`もその置換を受けるだけなので、異なる値の個数は不変である。したがって、固定した現行テーブルを並べ替えるだけでは、論文の手法が利用した**全ワードの同一反復**を増やせない。

この結果は、部分出力の一致、線形変換で現れる関係、低次数Boolean構造、積の共有、新たな角度学習による表の変更を否定しない。回路を合成していないため、Toffoli数の下限でもない。有効領域外の行を使った自由度を仮定せず、最終4行を越える不完全ブロックは比較対象外とした。

再現コマンド（データはリポジトリ外に配置）:

```bash
python audit_anthropic_repeated_rows.py \
  ../dqi_inputs/chemistry_4033/submission.npz \
  --report anthropic_repeated_rows_audit.json
```

## 5. 逆平方根・Coulombの比較

論文のCoulombタスクは次の整数演算である。[task仕様][coulomb-task]・[契約データ][coulomb-contract]

\[
n_2=\sum_{c=1}^{3}(r_{i,c}-r_{j,c})^2,\qquad
k\longmapsto k+\operatorname{round}(2^{24}/\sqrt{n_2})\pmod{2^{25}}.
\]

| 項目 | 論文Coulomb | 競技invsqrt |
|---|---|---|
| 入力 | 2点×3座標×8bit = 48bit、任意初期値の25bit加算先 | 22bitの`x`。数値出力レジスタなし |
| 対象領域 | 8bit座標差の平方和として実現可能な139,637個の`n_2`、最大195,075 | 全整数`1 <= x <= 3,133,452` |
| 出力 | 逆距離の固定小数点値を加算 | `exp(2πi/sqrt(x))`の位相、入力とscratchは復元 |
| 許容誤差 | 丸め済み整数目標から±32 LSB、modular差の中心化後に判定 | `2^-24/sqrt(x)` turns以内、mod 1で比較 |
| 費用 | Toffoli数 × peak live Q | `Q × (平均Toffoli-like数 + 回転合成T数/4)` |
| 公開結果 | 6,355T・252Q → 1,140T・142Q | e46: 46Q、約1,711.294 Toffoli-equivalent、費用78,719.529 |

論文の±32 LSBは丸め済み目標に対して約`1.907e-6`。連続値との丸め差も含めれば最大`32.5 × 2^-24`で、約`1.94e-6`となる。対して競技の許容位相誤差は最大入力で約`3.37e-11` turnsまで小さくなる。論文の係数や省略bit数で競技の精度を満たすという根拠はない。

左列の資源数は著者の[結果記録][coulomb-results]、右列は取得したe46と一致するハッシュを持つ[上流検証証跡](results/2026-11-14/invsqrt_upstream_verification.json)に基づく。e46について今回新しく全200,540,928 shotsを実行したわけではない。

### 適用できる設計手法と、そのまま使えない部分

[Coulombの実装][coulomb-design]は、正規化後の局所一次式を、最終出力の丸め・切り捨て・桁移動を合成した整数写像に対してフィットする。理想実数多項式を先に求めて後から丸める方法より、実際の許容範囲を活用できる。これはe46の算術部分を再設計するときの参考になる。

ただし、同じ128区間・6bit局所座標が競技に十分とは限らない。競技では平方距離を作る部分は不要だが、領域が広く、全整数に対する相対精度が必要で、最後に位相適用と清掃を含めて評価する。論文全体の142Qや1140Tから、e46の46Qを下回る部分回路の費用は読み取れない。

さらに[競技verifier][invsqrt-verifier]は、一般角の`Z_POW`の合成誤差に、最悪入力で残った精度の余裕を割り当てる。1回の回転のT費用は`0.56 log2(1/eps) + 5.3`。近似誤差を許容値いっぱいまで使い切ると回転合成費用が増えるので、整数フィットだけでなく、残余精度と回転数の共同評価が必要になる。公開e46の証跡には33個の一般角回転、`rotation_eps ≈ 6.003e-13`が記録される。

ユーザーが報告した角度LPの停滞は、仮にその固定基底で確認できても、異なる算術構造の最適性まで証明しない。本調査ではそのLPコードを検証しておらず、大域最適との主張はしない。

## 6. 次に切り出せる具体的な実験

### A. 共通制御を持つ二次位相の一括簡約

著者の化学[生成コード][chem-code]には、`symplectic_pairs`・`min_form_net`という実装がある。共通量子制御`g`の下で、二次Boolean式`q(x)`が作る位相`(-1)^(g q(x))`を、線形な座標変換でまとめて簡約する。

定数項を除いた`q`のpolar行列を`B`とし、GF(2)上のrankが`2r`なら、二次部分を`r`個の積へ変換できる。CNOTで座標変換し、`r`個のCCZと一次項用のCZ、必要なら定数項用のZを適用して座標を戻す。これは二つのCCZだけの置換より広い範囲の共有を扱える。ここでの最小性は、この二次形式を線形変換で実装する枠組みに限定して扱う。

既存の[dqi_ccz_pair_scan.md](dqi_ccz_pair_scan.md)で合法な単純ペアが0だったことは、こうした一括変換まで否定しない。新しい探索では、同じ量子制御と古典条件を持つ区間を抽出し、中間のCNOTを式に吸収できるか、測定・reset・古典条件の更新を跨がないかを先に確認する。入力の線形写像と位相多項式の係数一致を独立に検証してから、元回路との全体検証へ進める。**本調査では対象DQI区間への適用・削減数は未確認。**

### B. 競技仕様による逆平方根の整数フィット

まず可逆回路を大量生成せず、正規化、区間分割、局所bit幅、固定係数に対し、全3,133,452入力で最終位相の誤差と残余精度を計算する小さなモデルを作る。既存のBoolean基底の回転角調整とは別の探索になる。精度を満たした組合せだけを回路化し、46Qを含む実際の幅と合成回転費用で比較する。

これは新しい算術候補を作る方向であり、論文の数字を競技スコアへ読み替える方法ではない。今回の調査では新たな数値フィットを実行していない。

### C. 4033の符号を保った部分出力共有

全ワード反復の経路は上の監査で除外した。残るのは、複数bit間の積・位相補正の共有、既存の完全16行ブロック内の可逆affine写像、物理モデルを保つgauge等である。最初に現行4033を再現する生成器が必要で、実際の合成費用を比較せずに代理のESOPサイズだけで有望と判断しない。

測定後の位相補正やReed–Muller基底そのものは、現在の公開ローダーやGF回路でも既に利用されている系統の方法である。名称が同じ手法を追加しただけでは新規改善にならない。また[既存の射影実験](chemistry_report.md)で、8bit角度を単純に7bit/6bitへ丸めて固定する6通りは、`W/H2_I`の変更だけでは精度条件に届かないと分かった。論文のテーブル最適化を根拠に、この失敗経路を長時間回し直す理由はない。

## 7. ゲート・検証器・公開資源

著者のモデルは可逆な古典ゲートと符号位相、X基底測定による消去を扱う。[公開リポジトリ][repo]にはPython生成器、task契約、独立grader、保存済みop stream、占有量の記録などがある。一般角の連続位相を必要とする競技invsqrtとは、表現する位相の範囲も異なる。論文のClifford frameを使う際も、何でもよいCliffordを競技へ持ち込めるという意味ではなく、実際のCNOT/CZ/CCZ等の構成を確認する。

公開ライセンスはApache-2.0。今回読んだコードは次のcommitに固定し、16ファイルのURL・サイズ・SHA-256を取得記録に残した。外部コードの生成器・評価器は実行していない。

```text
64b5a13aa249f1360846657392e6c66817b26d0f
```

| 資源 | 用途 |
|---|---|
| [著者リポジトリ][repo] / [プロジェクトページ][project] | 全体、論文との対応、公開ライセンス |
| [chemistry task][chem-task] / [contract][chem-contract] / [results][chem-results] | 物理モデル、入出力、精度、正確な費用 |
| [化学生成器][chem-code] / [説明][chem-design] | 共通制御位相の簡約、lookup、共有unlookup |
| [alias_sched.py][alias-code] / [gen_constants.py][constants-code] | 同じ分布を保つ表の再構成、符号gaugeの探索 |
| [Coulomb task][coulomb-task] / [contract][coulomb-contract] / [results][coulomb-results] | 整数出力の仕様と正確な費用 |
| [Coulomb生成器][coulomb-code] / [説明][coulomb-design] | 最終整数演算を踏まえた係数探索 |
| [競技invsqrt verifierの固定ミラー][invsqrt-verifier] | 位相精度・回転合成費用・Qの数え方 |

著者の`.ops.xz`は競技の`.kmb`とは別形式で、builderとgraderも別実装である。移植時はゲート名だけでなく、測定結果の寿命、条件付き操作、reset、入出力レジスタ、量子ビットの数え方を合わせる必要がある。論文のgraderが通ることを、競技verifierのPASSと同一視しない。

今回作成・更新したリポジトリ内の成果物は、この調査メモ、[監査スクリプト](audit_anthropic_repeated_rows.py)、[監査JSON](anthropic_repeated_rows_audit.json)の3点。**この調査による新たなスコア改善、Kaggle提出、提出候補の変更はない。**

[paper]: https://arxiv.org/html/2610.22367v1
[blog]: https://www.anthropic.com/research/designing-efficient-quantum-circuits
[repo]: https://github.com/andigu/uncompute
[project]: https://andigu.github.io/projects/uncompute/
[chem-task]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/chemistry-fe2s2/README.md
[chem-contract]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/chemistry-fe2s2/contract.json
[chem-results]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/chemistry-fe2s2/results.jsonl
[chem-design]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/chemistry-fe2s2/circuits/discovered/README.md
[chem-code]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/chemistry-fe2s2/circuits/discovered/circuit.py
[alias-code]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/chemistry-fe2s2/alias_sched.py
[constants-code]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/chemistry-fe2s2/circuits/discovered/gen_constants.py
[coulomb-task]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/coulomb-potential/README.md
[coulomb-contract]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/coulomb-potential/contract.json
[coulomb-results]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/coulomb-potential/results.jsonl
[coulomb-code]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/coulomb-potential/circuits/discovered/circuit.py
[coulomb-design]: https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/coulomb-potential/circuits/discovered/README.md
[invsqrt-verifier]: https://github.com/Inzainos/quantum-circuit-compilation/blob/4277c767440df9efb8a90860ae2ce47028e46ba9/verifiers/invsqrt/verify_submission_invsqrt.py
