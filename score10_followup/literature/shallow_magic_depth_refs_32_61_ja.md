# Shallow Magic Depth v2の参考文献 [32]–[61]

番号は [Classical Simulability of Quantum Circuits with Shallow Magic Depth, arXiv:2409.13809v2](https://arxiv.org/html/2409.13809v2#bib) に対応。既存の読書台帳に全本文の確認記録がある場合は「既存の本文読了記録」、今回主要箇所を確認した場合は「主要箇所」と記載した。取得済みの本文全体を今回読み切ったとは扱わない。

[32]–[43] の詳細な既存台帳は `literature/refs26_43/reading_ledger_ja.md`。とくに[32]は著者版33頁のOCR本文を読んだ記録があるため、出版社の抄録しか取得できなかった以前の状態から更新した。[39]は今回Michiganの一次PDFの閲覧可能な公開索引を見つけ、本文の一部を確認した。

| 番号 | 確認範囲 | 内容とGVQCCへの関係 | 一次資料 |
|---|---|---|---|
| 32 Fenner–Fortnow–Kurtz | 既存の本文読了記録（著者版全33頁OCR、主要式は画像照合） | GapPは受理と拒否の経路数の差。量子干渉の符号付き和の記述に使える。小さい回路の合成手順や特定ローダーのToffoli下界を与えない。 | [著者版](https://www.cse.sc.edu/~fenner/papers/gaps.pdf) |
| 33 Ehrenfeucht–Karpinski | 既存の本文読了記録（全8頁） | 二次以下のXOR–AND式の解数はGF(2)二次形式の正規化で計算でき、三次では計数が#P完全。局所位相和の検算に使えるが、計数問題と回路最小化は別問題。 | [著者報告](https://theory.cs.uni-bonn.de/ftp/reports/cs-reports/1990/8543-CS.pdf) |
| 34 Fefferman | 既存の講義本文読了記録（63枚、別添問題未読） | 計数困難性、XEB、Pauli経路の打切り。標本分布、加法誤差、相対誤差を区別する。雑音を仮定した経路打切りを無雑音のoracle置換へ転用できない。 | [IAS講義](https://www.ias.edu/sites/default/files/billfefferman-lectures-pcmi-out.pdf) |
| 35 Selinger | 既存の本文読了記録（全5頁）と既存KMB実測 | 清浄な補助4本で7Tを1層にする。Fig.3のCCZ版は8入力で位相と補助線の復元を検査済み。単独のinvsqrt換算費用は1から1.75へ増える。 | [著者稿](https://arxiv.org/pdf/1210.0974) |
| 36 Dehaene–De Moor | 既存の本文読了記録（全9頁） | Clifford作用のGF(2)シンプレクティック表現、安定化子状態のアフィン支持集合と二次位相。HMRの位相補償を含む等価性検証や線形基底の整理に使える。 | [著者稿](https://arxiv.org/pdf/quant-ph/0304125) |
| 37 Knill | 既存の本文読了記録（全17頁） | 誤り検出符号とBell teleportationを使うポストセレクション型耐故障計算。条件付き成功の資源論であり、全分岐を補正するKMB回路への変換は別途必要。 | [著者稿](https://arxiv.org/pdf/quant-ph/0402171) |
| 38 Bravyi–Kitaev | 既存の本文読了記録（全15頁） | 雑音付きmagic ancillaからの蒸留。蒸留・符号化資源を必要とし、直接の採点換算にはならない。論文内T-type/H-typeの呼称は現代のTゲート名と異なる。 | [著者稿](https://arxiv.org/pdf/quant-ph/0403025) |
| 39 García-Ramírez | 今回、一次PDFの抄録とCh. V・VI・VIIIの該当箇所。全章未読 | 安定化子フレームの共通行列と位相情報により状態の重ね合わせを記述し、COALESCEで圧縮。Quipuの一部算術回路の効率は入力状態に依存し、任意入力oracleのゲート削減を保証しない。 | [Michigan学位論文](https://deepblue.lib.umich.edu/bitstream/handle/2027.42/107198/hjgarcia_1.pdf) |
| 40 Cui–Gottesman–Krishna | 既存の本文読了記録（全9頁） | 素数次元の対角ゲートを位相精度と多項式次数で階層分類。候補の表現・検算に使える。階層が等しいことから費用やゲート列の等価性は従わない。 | [著者稿](https://arxiv.org/pdf/1608.06596) |
| 41 Schuch–Siewert | 既存の本文読了記録 | Walsh–Hadamard変換とパリティ演算で対角ユニタリを合成。invsqrtの位相述語の置換候補を列挙できる。任意の対角演算では回転数と係数精度の費用が残る。 | [著者稿](https://arxiv.org/pdf/quant-ph/0303063) |
| 42 Gidney–Jones | 既存の本文読了記録（全1頁） | 二つのAND積を使い、相対位相と測定補正でCCCZを6Tにする。掲載回路はH等を含み、GVQCCへ持ち込むには使用可能命令で別の構成を示す必要がある。 | [著者稿](https://arxiv.org/pdf/2106.11513) |
| 43 Controlled-TのQ&A | 質問と3回答の本文を確認。一部画像は未確認 | ANDを計算し、Tを作用させてHMRで作業線を消し、CZで補償する構成を提案。invsqrtの局所費用は1 CCX + 1 Tの1.25、追加幅も算入。 | [原Q&A](https://quantumcomputing.stackexchange.com/questions/13132/how-can-we-implement-controlled-t-gate-using-cnot-and-h-s-and-t-gates) |
| 44 Raussendorf–Browne–Briegel | 抄録、序論、既存の本文該当箇所、結論 | Cluster stateと適応単一量子ビット測定による普遍計算。HMR分岐のbyproduct補償の考え方は対応するが、cluster state準備と測定基底の費用がある。 | [著者稿](https://arxiv.org/pdf/quant-ph/0301052) |
| 45 Aaronson | 抄録、§§1–4の定義・主要証明 | PostBQP=PPの結果は特定測定結果に条件づける仮定に依存。希な分岐を切り捨てる論拠としてGVQCCに適用できない。 | [著者稿](https://arxiv.org/pdf/quant-ph/0412187) |
| 46 Aruteら | 抄録、本文の実験・評価概要（技術付録の精査なし） | Sycamoreのランダム回路サンプリング実験とXEBの検証。2019年の古典時間の推定はこの競技の算術回路の最小コストを与えない。 | [掲載一次論文](https://www.nature.com/articles/s41586-019-1666-5) |
| 47 Yung–Cheng | 抄録、序論、議論 | IQP検証で秘密に対応する相関を計算する手法。ある観測量に関して可換部分を無視できても、完全なoracleを保存する変換にはならない。 | [著者稿](https://arxiv.org/html/2005.01510v2) |
| 48 Bravyi–Gosset–Liu | 抄録、主要アルゴリズムの概要と既存の該当箇所 | 全周辺分布を求めず、回路接頭辞の振幅を使って厳密標本化する。古典検算を高速化しうる手法で、採点ゲートの削減とは別。 | [著者稿](https://arxiv.org/html/2112.08499v2) |
| 49 Lai–Cheng | 抄録、§VI、既存のアルゴリズム該当箇所 | フルT-rankでT-depth 1の回路を学習する。効率的な保証の対象は計算基底入力で、任意入力への厳密記述には追加計算を要する。出力ビットの一致だけでは相対位相が一致しない。 | [著者稿](https://arxiv.org/html/2106.12524v3) |
| 50 Grewalら | 抄録、序論、既存の定理部分 | 安定化子忠実度の高い状態とHaarランダム状態を識別。擬似ランダム状態のT-count下界は、具体的なDQI・QROMの下界へ移らない。 | [著者稿](https://arxiv.org/html/2209.14530v1) |
| 51 Grewalら | 抄録、§1.2のアルゴリズム要約、既存の該当箇所 | Cliffordと少数非Cliffordゲートで作られる状態を、安定化子の部分群を求めて小さい場所に集中させ学習。既知状態の近似と任意入力への回路作用は区別が必要。 | [著者稿](https://arxiv.org/html/2305.13409v5) |
| 52 Grewalら | 抄録、主結果、§8 | Bell差分標本化、シンプレクティックFourier解析による忠実度推定。線形数のTが必要という結果は計算論的擬似ランダム性について。 | [著者稿](https://arxiv.org/html/2304.13915v3) |
| 53 Leone–Oliviero–Hamma | 抄録、序論、§7 | 有限個のTを混ぜて準備した離散的な状態のPauli表示を学習。論文は学習結果から状態準備回路を合成すること自体を将来課題に挙げる。 | [著者稿](https://arxiv.org/html/2305.15398v6) |
| 54 Hangleiter–Gullans | 抄録・序論・議論、既存の主結果箇所 | 2コピーの横断Bell測定から忠実度、深さの検定、T-count下界を推定。許可回路集合での合成や単一入力oracleの削減を保証しない。 | [著者稿](https://arxiv.org/html/2306.00083v5) |
| 55 Olivieroら | 抄録、主要な忠実度式・復号器・結論 | 非Clifford回路でも局所情報をCliffordで復号できる例。情報の取出しにはEPR資源と出力の射影を要し、元ユニタリ全体の逆回路との等価性を要求しない。DQIのReed–Solomon復号とは課題が違う。 | [著者稿](https://arxiv.org/html/2212.11337v5) |
| 56 Leoneら | 抄録、§V.2の圧縮定理、§VIと既存の該当箇所 | t個の非Cliffordゲートを含むユニタリを、左右のCliffordと高々t量子ビット上のユニタリへ正確に分離。これは状態準備だけでなく演算子の定理。内側の非Clifford数はt個のままで、外側の未知データ線は消えない。局所回路の非線形処理が依存する線を調べる手掛かり。 | [著者稿 §V.2](https://arxiv.org/html/2212.11338v4#S5.SS2) |
| 57 Niroulaら | 抄録、序論、§V | ランダム安定化子符号でコヒーレント誤差とsyndrome測定によるmagic相転移。符号の確率モデルを要し、HMRで任意の中間値を消せることは従わない。 | [著者稿](https://arxiv.org/html/2304.10481v2) |
| 58 Bejan–McLauchlan–Béri | 抄録、§II、§VIIと既存の該当箇所 | 監視Clifford+T回路で測定がmagicを分割する機構。小ブロック分離の発想はHMR依存解析の参考になるが、全測定結果の位相補償を改めて証明する必要がある。 | [著者稿](https://arxiv.org/html/2312.00132v3) |
| 59 Turkeshi–Tirrito–Sierant | 抄録、序論、§VI–VII | ランダムbrick-wall回路におけるmagic指標の飽和時間は系サイズの対数程度。ランダム系での平均的記述であり、構造化算術回路の幅やToffoli数への下界ではない。 | [著者稿](https://arxiv.org/html/2407.03929v2) |
| 60 Fuxら | 抄録、状態・標本化の圧縮節、結論 | 条件を満たすClifford＋位相回転で作る状態を、Cliffordとmagic productに分離。少ない量子ビットで標本化する手法は固定初期状態を利用し、公開DQI回路の任意入力チャネル圧縮とは異なる。 | [著者稿](https://arxiv.org/html/2410.09001v3) |
| 61 Liu–Clark | 抄録、§IIIのOFD定理、§VII、付録H冒頭 | 共役したPauli列のX/Y成分のGF(2)行列で、固定入力からの状態を表すMPSのbond dimension増大を評価。既知の非もつれた量子ビットが前提で、状態の表現サイズは回路の最大同時幅を表さない。 | [著者稿](https://arxiv.org/html/2412.17209v2) |

[56]からの具体的な検査候補。CCZと線形ゲートだけの測定を含まない区間では、CNOTの基底変換を片側へ移して、残る三次位相の依存方向をGF(2)で調べられる。位相が少数の線形形式に因数化できれば、その方向へ処理を集中できる。物理幅の削減には、無関係な座標の保存と測定補償を含む全区間の配置証明が必要。幅削減やスコア更新はこの文献調査から得ていない。
