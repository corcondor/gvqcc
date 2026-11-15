# 「Notation used throughout」の出典と参考文献53件

表の出典はJiachen Shen・Hui Zhongの『The resource cost of magic in a code block』v2。主本文§§1–5、付録A–C、図表キャプション、参考文献を扱う既存の通読記録に加え、今回Table 1、式(4)–(7)、Condition 4、Theorems 1–3、§4.1–4.2を一次本文で照合した。ResearchGateの表示は52件で、正式な番号は[1]–[53]。 [一次本文](https://arxiv.org/html/2608.29438v2)

定理1は、選別された1論理量子ビットの測定効果について、受理確率とstabilizer-effect八面体までの距離の積を、測定結果の旗を含む各セルのdiamond距離の和で上から抑える。定理2は互換なdilation、固定した回復構造、分岐ごとの因子化を仮定し、閾値以上の連結な挿入集合の重みで抑える。定理3は弱いZ回転を論理ストリングに載せた例で漸近指数を達成する。符号距離や選別確率は大会のQ・Tとは別の量であり、この結果からローダーのToffoli下限や削減は導けない。

[15]の4 T状態によるCCZ合成は、invsqrtの単純なT/4換算でも1相当でnative CCZと同額。競技で使える補助状態の準備、命令への変換、全体の幅と回転精度も別に確認する必要がある。[27]と[44]の考え方は、HMRで消した値を位相として追跡し、すべての分岐で同じ作用を持つか証明するために使える。

たとえば基底入力 x が消去直前に |f(x)⟩|g(x)⟩ へ写り、保持する f が入力を一意に定める場合、k本をHMRした測定結果 m に対応するKraus作用は 2^(-k/2)(-1)^(m·g(x))|f(x)⟩。補正後にmに依存する差が入力非依存の位相だけなら、全分岐が同じ量子チャネルを実現する。fの単射性と測定結果の後続用途を検査する。さらに大会invsqrtの検証器は各shotの記録位相を目標値と直接比較するため、入力非依存の分岐位相であっても検証器の誤差許容内に収める。

以下は参照番号単位の台帳。全53件の一次本文の抽出を取得済み。45件は以前の通読記録との合算で本文・付録の全範囲を確認し、8件は今回部分確認。全図の画像照合および実験・全証明の独立再現は行っていない。取得した本文をそのまま転記せず、下には用途と読んだ範囲を記載した。

| No. | 一次資料 | 読んだ範囲 | 確認した内容 |
|---:|---|---|---|
| 1 | [Universal quantum computation with ideal Clifford gates and noisy ancillas](https://arxiv.org/pdf/quant-ph/0403025) | 全範囲（既存の実読記録） | 理想Cliffordと独立なノイズ付き補助状態から魔法状態を蒸留。原論文のT型状態と、現在のπ/4回転に使うH型のClifford軌道を区別。 |
| 2 | [Surface codes: Towards practical large-scale quantum computation](https://arxiv.org/pdf/1208.0928) | 部分確認。§VII冒頭、§XV–XVI導入、§XVII | surface codeのsyndrome検出、論理H、注入による論理Tと補正を解説。費用は物理誤り率、code distance、サイクルに依存。 |
| 3 | [UNIQ: Communication-efficient distributed quantum computing via unified nonlinear integer programming](https://arxiv.org/pdf/2512.00401) | 全範囲（既存の実読記録） | 分散プロセッサの配置、EPRペア在庫、通信スケジュールを同時最適化。局所CCX数の合成問題とは目的関数が異なる。 |
| 4 | [Differential privacy preserving distributed quantum computing](https://arxiv.org/pdf/2412.12387) | 全範囲（既存の実読記録） | 測定出力分布に対するRényi差分プライバシー。観測された古典分布の近さからコヒーレント回路の等価性は出ない。 |
| 5 | [Tuning quantum computing privacy through quantum error correction](https://arxiv.org/pdf/2312.14521) | 全範囲（既存の実読記録） | Steane符号による誤り訂正の配置で、ノイズとプライバシーを調整。 |
| 6 | [Differential privacy preserving quantum computing via projection operator measurements](https://arxiv.org/pdf/2312.08210) | 全範囲（既存の実読記録） | 測定標本ノイズによる差分プライバシー。有限標本の正規近似と厳密な誤差保証を区別。 |
| 7 | [Bridging quantum computing and differential privacy: Insights into quantum computing privacy](https://arxiv.org/pdf/2403.09173) | 全範囲（既存の実読記録） | 量子差分プライバシーの調査。ノイズ、測定、隣接性の定義が主題。 |
| 8 | [Harnessing inherent noises for privacy preservation in quantum machine learning](https://arxiv.org/pdf/2312.11126) | 全範囲（既存の実読記録） | QML勾配の標本分散、ノイズと誤り緩和を比較。 |
| 9 | [Magic-state distillation with low overhead](https://arxiv.org/pdf/1209.2426) | 全範囲（既存の実読記録） | 三直交行列が生むtransversal Tと魔法状態蒸留。GF(2)の三重積条件は位相検算の参考になる。 |
| 10 | [Magic-state distillation with the four-qubit code](https://arxiv.org/pdf/1204.4221) | 全範囲（既存の実読記録） | 4量子ビット符号による10-to-2蒸留。出力同士の誤り相関が次段の設計を制約。 |
| 11 | [Multilevel distillation of magic states for quantum computing](https://arxiv.org/pdf/1210.3388) | 全範囲（既存の実読記録） | 品質の異なる魔法状態を使う多段蒸留。異なるブロックの出力を選び相関を抑える。 |
| 12 | [Roads towards fault-tolerant universal quantum computation](https://arxiv.org/pdf/1612.07330) | 全範囲（既存の実読記録） | 蒸留、色符号、gauge fixing等の耐故障方式を比較。物理時空間と論理ゲート数は別の資源。 |
| 13 | [The resource theory of stabilizer quantum computation](https://arxiv.org/pdf/1307.7171) | 全範囲（既存の実読記録） | stabilizer資源理論、相対エントロピーやmanaによる変換の限界。monotoneの仮定と対象次元に注意。 |
| 14 | [Contextuality supplies the “magic” for quantum computation](https://arxiv.org/pdf/1401.4174) | 全範囲（既存の実読記録） | 文脈性と蒸留の関係。奇素数次元のWigner表現・exclusivity graphの結果はその次元の仮定付き。 |
| 15 | [Application of a resource theory for magic states to fault-tolerant quantum computing](https://arxiv.org/pdf/1609.07488) | 全範囲（既存の実読記録） | robustnessをLPに落とし、測定付きCCZを4 T状態で合成。大会invsqrtのT/4換算ではこれだけで1、native CCZと同額。 |
| 16 | [Quantifying magic for multi-qubit operations](https://arxiv.org/pdf/1901.03322) | 全範囲（既存の実読記録） | Choi状態のrobustnessと合成に適したchannel robustnessを区別。channel robustnessで近似サンプリング費用を評価。 |
| 17 | [Improved classical simulation of quantum circuits dominated by clifford gates](https://arxiv.org/pdf/1601.07601) | 全範囲（既存の主本文I–V＋今回付録A–Fと参考文献） | Clifford+Tの出力確率・標本の古典計算。付録A–Eでアフィン台とmod 8二次形式を扱い、FでJonesの測定付き4T Toffoli（補助2本のうち1本を共用）を使う。T/4換算では1相当で、近似シミュレーションは等価変形とは別。 |
| 18 | [Robustness of magic and symmetries of the stabiliser polytope](https://arxiv.org/pdf/1807.10296) | 全範囲（既存の実読記録） | 対象とstabilizer polytopeの対称性でrobustnessのLPを縮約。軌道代表の生成費用は別に残る。 |
| 19 | [Magic state cultivation: growing T states as cheap as CNOT gates](https://arxiv.org/pdf/2409.17595) | 全範囲（既存の実読記録） | 注入、低距離でのcultivation、符号拡大で物理T状態の製造費用を減らす。大距離評価はClifford proxyを含む。 |
| 20 | [Efficient magic state cultivation for $\sqrt{T}$ gates](https://arxiv.org/pdf/2606.10430) | 全範囲（既存の実読記録） | doubled color codeで√T状態のcultivation。物理準備の論文で、Z_POWの採点を変更する材料はない。 |
| 21 | [Cultivating T states on the surface code with only two-qubit gates](https://arxiv.org/pdf/2509.05232) | 全範囲（既存の実読記録） | 2量子ビットゲートとfold-dual変形だけでsurface-code cultivation。注入と選別を含む。 |
| 22 | [Fold-transversal surface code cultivation](https://arxiv.org/pdf/2509.05212) | 全範囲（既存の実読記録） | fold-transversal cultivationと直接物理CCZ。Pauliノイズ下のシミュレータ切替も証明。 |
| 23 | [High rate magic state cultivation on the surface code](https://arxiv.org/pdf/2502.01743) | 全範囲（既存の実読記録） | surface codeでの高率cultivation。非局所fold、物理3量子ビットゲートのノイズ、選別を含む。 |
| 24 | [A continuity theorem for Stinespring’s dilation](https://arxiv.org/pdf/0710.2495) | 全範囲（既存の実読記録） | 近いchannelに対し近いStinespring dilationを選べる。固定の測定記録を保つ環境ゲージまで自動で保証しない。 |
| 25 | [Stabilizer codes and quantum error correction](https://arxiv.org/pdf/quant-ph/9705052) | 部分確認。§§5.4、5.7、5.8の測定補正・状態注入。既存台帳には目次と§§5.3–5.4、5.7 | 測定で生じる分岐を補正し、Toffoli用の特殊補助状態でテレポートする構成。補助状態の製造と測定型を含めて評価する必要あり。 |
| 26 | [Improved simulation of stabilizer circuits](https://arxiv.org/pdf/quant-ph/0406196) | 全範囲（既存記録＋今回の補読） | destabilizerも保持するTableauにより決定的・確率的測定をO(n²)更新。§VIのClifford正準形はユニタリを対象とし、初期状態の準備とは区別。 |
| 27 | [The clifford group, stabilizer states, and linear and quadratic operations over GF(2)](https://arxiv.org/pdf/quant-ph/0304125) | 全範囲（既存の実読記録） | CliffordをGF(2)のシンプレクティック写像と二次位相で記述。HMRの補正が既存の生存ワイヤの二次位相で表せるか検算するのに有用。 |
| 28 | [Fault-tolerant quantum computation by anyons](https://arxiv.org/pdf/quant-ph/9707021) | 全範囲（既存の実読記録） | toric codeと量子二重、編み込み・融合。§7はS5モデルでの普遍計算を概説し、詳証は別の場所に譲る。 |
| 29 | [Models for gapped boundaries and domain walls](https://arxiv.org/pdf/1104.5047) | 全範囲（既存の実読記録） | gapped boundaryとdomain wallをmodule/bimodule圏で記述。foldingで相間の壁を二重系の境界に移す。 |
| 30 | [The quantum double model with boundary: Condensations and symmetries](https://arxiv.org/pdf/1006.5479) | 全範囲（既存の実読記録） | 有限群量子二重で部分群と2-cocycleが境界を指定。foldingと凝縮を使い壁を横切るanyonを分類。 |
| 31 | [Symmetry fractionalization, defects, and gauging of topological phases](https://arxiv.org/pdf/1410.4540) | 部分確認。§I.Aと§XI.Iのtoric-code例の冒頭 | 対称性分数化、G-crossed braided圏、欠陥とgauging。H³のobstructionとH²のtorsorを分ける。 |
| 32 | [Topological quantum memory](https://arxiv.org/pdf/quant-ph/0110143) | 部分確認。§XI結論 | 局所syndrome測定付き量子メモリの閾値。3次元格子ゲージ理論の臨界点への写像であり、DQIのReed–Solomon性能式とは別。 |
| 33 | [Fast decoders for topological quantum codes](https://arxiv.org/pdf/0911.0581) | 全範囲（既存の実読記録） | トポロジカル符号の近似RG decoder。誤り鎖の重みと同値類の確率・縮退を区別。 |
| 34 | [Almost-linear time decoding algorithm for topological codes](https://arxiv.org/pdf/1709.06218) | 全範囲（既存の実読記録） | Union-Findで奇数クラスタを育て、peelingで訂正。消失とPauli誤りのモデルであり、Reed–Solomon復号器には直接転用できない。 |
| 35 | [Surface code quantum computing by lattice surgery](https://arxiv.org/pdf/1111.4022) | 全範囲（既存の実読記録） | planar patchのmerge/splitと条件付き補正で局所的な論理操作を作る。物理配置の改善が採点上の論理幅削減を示すわけではない。 |
| 36 | [Topological fault-tolerance in cluster state quantum computation](https://arxiv.org/pdf/quant-ph/0703143) | 全範囲（既存の実読記録） | 3次元cluster-stateを空間2次元＋時間で実装する耐故障測定型量子計算。非CSSゲートには状態注入・蒸留を使う。 |
| 37 | [Lattice surgery with a twist: Simplifying clifford gates of surface codes](https://arxiv.org/pdf/1709.02318) | 全範囲（既存の実読記録） | CliffordのPauli frameを古典追跡し、twistによるlattice surgeryで遠距離CNOT。物理距離のO(log s)とCCX費用は別。 |
| 38 | [A game of surface codes: Large-scale quantum computing with lattice surgery](https://arxiv.org/pdf/1808.02892) | 部分確認。§4導入と実例、§7冒頭 | data blockとdistillation blockを分け、T count、T depth、物理誤り率から物理面積と時間を見積もる。 |
| 39 | [Dynamically generated logical qubits](https://arxiv.org/pdf/2107.02194) | 全範囲（既存の実読記録） | 2体Pauli測定の順序で瞬間的なstabilizer群と論理量子ビットを作る。測定を全て同時に扱うsubsystem codeとは異なる。 |
| 40 | [Planar floquet codes](https://arxiv.org/pdf/2110.05348) | 全範囲（既存の実読記録） | 3価ラティスでFloquet測定順序を一般化。有色境界と時間で変わる論理演算子を扱う。 |
| 41 | [Quantum computation from dynamic automorphism codes](https://arxiv.org/pdf/2307.10353) | 部分確認。§§5.4、6の移行箇所、§8の課題 | dynamic automorphism color codeの測定順序で論理Cliffordを実現。3次元拡張で非Cliffordを導入する構成の出発点。 |
| 42 | [Quantum codes on a lattice with boundary](https://arxiv.org/pdf/quant-ph/9811052) | 全範囲（既存の実読記録） | 交互の境界を持つplanar stabilizer code。相対homologyから論理演算子と距離を求める。 |
| 43 | [Optimal resources for topological 2D stabilizer codes: Comparative study](https://arxiv.org/pdf/quant-ph/0703272) | 全範囲（既存の実読記録） | surface/color codeをn/d²で比較。符号の物理量子ビット効率は大会KMBの幅とは別。 |
| 44 | [Theory and architecture of syndrome-resolved logical gates](https://arxiv.org/pdf/2510.08290) | 全範囲（既存の実読記録） | syndromeごとにK_s†K_s=p_s Iを確かめ、入力に依存しない確率と条件付き論理作用を分けて証明。HMR補正の監査にも応用できる。 |
| 45 | [A robust phase of continuous transversal gates in quantum stabilizer codes](https://arxiv.org/pdf/2510.01319) | 全範囲（既存の実読記録） | 弱い横断回転後のsyndrome別論理角とdephasingを数値評価。小角度、符号、誤りモデルと適応方策を含む。 |
| 46 | [Classification of topologically protected gates for local stabilizer codes](https://arxiv.org/pdf/1206.1609) | 全範囲（既存の実読記録） | 幾何的局所性と定数深さの下でD次元符号の論理ユニタリをClifford階層の第D層に制約。測定付きKMBのToffoli下限にはならない。 |
| 47 | [Protected gates for topological quantum field theories](https://arxiv.org/pdf/1409.3898) | 全範囲（既存の実読記録） | TQFTのVerlinde代数と異なる基底の整合性で局所性保存ユニタリを制約。Fibonacci/Isingの結果は曲面と荷電ラベルに依存。 |
| 48 | [Measurement quantum cellular automata and anomalies in floquet codes](https://arxiv.org/pdf/2304.01277) | 部分確認。§7のLRMC/MQCA指数と境界例 | locally reversible measurement cycleとMQCA指数。2D Floquet測定の境界に1D単独で出ない半整数の指数が生じる。 |
| 49 | [Locality-preserving logical operators in topological stabiliser codes](https://arxiv.org/pdf/1709.00020) | 全範囲（既存の実読記録） | domain wallから局所性保存ゲートを分類。3D surface-code stackにCCZが存在する結論は、KMBで1 CCZ未満の代替を与えない。 |
| 50 | [Adaptive constant-depth circuits for manipulating non-abelian anyons](https://arxiv.org/pdf/2205.01933) | 部分確認。§1とTheorems 3.1、7.1、§§4.3、5.1の導入 | 可解群の量子二重状態準備とanyon操作に適応定数深さ回路を構成。特定の非適応局所回路の深さ下界と、採点のゲート数を区別。 |
| 51 | [Quantifying multiqubit magic channels with completely stabilizer-preserving operations](https://arxiv.org/pdf/2202.07867) | 全範囲（既存の実読記録） | 完全stabilizer保存superchannelで動的magic変換を解析。広い自由操作集合での上界は、許可命令での実装を与えない。 |
| 52 | [The axiomatic and the operational approaches to resource theories of magic do not coincide](https://arxiv.org/pdf/2011.11651) | 全範囲（既存の実読記録） | 複数量子ビットでは操作的stabilizer operationが公理的CSPの真部分集合。親論文の出版情報に食い違いがあり、著者・題名で原文を同定。 |
| 53 | [Cross-cap defects and fault-tolerant logical gates in the surface code and the honeycomb floquet code](https://arxiv.org/pdf/2310.06917) | 全範囲（既存の実読記録） | cross-cap欠陥付きsurface code/Floquet codeでCliffordゲートを実現。向き付け不可能な幾何またはbilayerを要する。 |
