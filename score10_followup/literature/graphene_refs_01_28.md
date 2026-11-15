# グラフェン本論文・引用文献1–28の内容監査

対象は *Atomic-Scale Imaging of Lattice Relaxation and Topological Flat Bands in Helical Trilayer Graphene* の引用番号1–28です。本論文の参考文献は56件であり、このファイルは前半28件の分担台帳です。

## 読了の意味

取得したページと論文本体を区別しています。Natureの一部ページは長くても要旨・参考文献・推薦記事だけでした。`main_text_complete` は主本文を最後まで読んだ意味で、未読の補足・付録を含みません。`full_extracted_text_complete` でも、図の全ピクセルや数式OCRを独立検証したとは主張しません。取得した原文は内部確認用で、配布資料はこの分析と一次資料へのリンクです。

## 回路最適化への結論

この範囲の文献から、現在の固定語表ローダーの実Toffoli数を削減する実装済み候補は得ていません。材料のmagic angle、Chern数、低エネルギーbandのrankを、非Clifford magic、Tゲート数、GF(2)乗法複雑度と同一視してはいけません。

構造上もっとも参考になるのは、[7]のWannier構成、[11]の鏡映セクター分解、[17]の零モード生成元、[18]の位置依存shift、[23]のchiral分解、[28]の基底変換です。ただし全て物理模型の対称性や射影条件を持ちます。[23]ではAA hoppingをゼロにして低エネルギー部分空間へ落とし、[28]では高いpseudo-Landau levelを除いています。[21]は候補比較で変換後の真空エネルギー定数を残す必要を明示しています。これらは任意ターゲットに作用する厳密XOR oracleと同じ要件ではありません。各項目の一次資料に条件と確認箇所を記載しました。

有限語表への有効な移し方は、まず実際の1232×75表で入力順列・出力基底・共通部分の恒等式を確認し、任意32ターゲットへのXORとして構成し、補助bitの準備・復元と全HMR測定枝の相対位相を含めて実ゲート数を測ることです。物理系の近似対称性を、語表の厳密対称性として仮定しません。

公式費用比較では検証済み基準27.32784222を維持し、J=4の片道ローダー合計4170以下という既存の判定条件を使います。この文献調査から数値改善を報告するものではありません。

## 個別台帳


読了区分の件数: `{"main_text_complete": 23, "full_extracted_text_complete": 5}`。

### [1] Moiré bands in twisted double-layer graphene (2011)

**著者:** Rafi Bistritzer; Allan H. MacDonald  
**一次資料:** [https://www.pnas.org/doi/10.1073/pnas.1108174108](https://www.pnas.org/doi/10.1073/pnas.1108174108)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Abstract–Discussion, extracted characters 2416–23556; numerical figures not independently digitized.

**結果と根拠:** 連続体Diracモデルと三つの層間結合で、微視的に非整合な二層でも小角度の低エネルギーを周期的moiréバンドとして扱う。約1.05度でDirac速度が消失し、狭いバンドと大きい状態密度が現れる。Model/Resultsは計算行列の縮小、層間平行移動を基底位相で除く方法を説明する。

**適用条件・残る確認:** 相互作用は扱わない。取得HTMLでは表示数式に欠落があるため、全数式を独立検算したとはしない。

**今回への適用:** 基底と対称性によるモデル縮小の例。固定された75語の厳密XOR表を近似連続体へ置換する根拠にはならない。magic angleは非Clifford magic量と無関係。

### [2] Correlated insulator behaviour at half-filling in magic-angle graphene superlattices (2018)

**著者:** Yuan Cao et al.  
**一次資料:** [https://arxiv.org/pdf/1802.00553](https://arxiv.org/pdf/1802.00553)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main article through Methods, characters 0–21500; supplementary material not read.

**結果と根拠:** 約1.1度の二層で半充填の絶縁的輸送を測り、容量測定・量子振動・磁場依存と、狭いバンドで相互作用が優勢になる説明を組み合わせる。Mott-likeな解釈を支持するが、本文は競合する秩序や歪みの可能性も議論する。

**適用条件・残る確認:** 観測と単純な三角格子Hubbard解釈を同一視できない。補足の全解析は未読。

**今回への適用:** 物理的モデル選択の資料。ローダーの全アドレス同値性、任意ターゲットXOR、測定枝の位相補正を与えない。

### [3] Unconventional superconductivity in magic-angle graphene superlattices (2018)

**著者:** Yuan Cao; Valla Fatemi; Shiang Fang; Kenji Watanabe; Takashi Taniguchi; Efthimios Kaxiras; Pablo Jarillo-Herrero  
**一次資料:** [https://arxiv.org/pdf/1803.02342v2](https://arxiv.org/pdf/1803.02342v2)  
**取得/確認範囲:** `full_text` / `full_extracted_text_complete`。All extracted preprint text, characters 0–72946, including Methods, Extended Data captions and bibliography; arXiv v2 (2018-05-20). Supplementary animation not viewed.

**結果と根拠:** 約1.1度の二層を半充填相関絶縁状態からドープすると最大1.7 Kのゼロ抵抗、臨界電流、磁場抑制が現れる。量子振動とHall密度は小さいFermi面を支持する。Methodsは位相干渉をJosephson経路で説明するが電流分布を一意決定できないと明記し、厳密な原子整合性と連続体近似も区別する。

**適用条件・残る確認:** 公刊題名と著者公開稿題名が異なる。強結合の解釈と特定のpairing symmetryの実証は同じでなく、本文は追加実験を必要とする。数式OCRの乱れと図・動画未検証がある。

**今回への適用:** 近似的に滑らかな物性を、離散語表の全入力で成立する恒等式へ変換できない。単一の観測量や位相干渉の署名を、任意ターゲットXORの全演算子検証の代用にしない。

### [4] Fractional Chern insulators in magic-angle twisted bilayer graphene (2021)

**著者:** Yonglong Xie et al.  
**一次資料:** [https://arxiv.org/pdf/2107.10854](https://arxiv.org/pdf/2107.10854)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text characters 0–19931; final paragraph re-read at 18800–20550; Methods/supplement not read.

**結果と根拠:** 局所圧縮率とStreda関係から八つのFCI状態を同定する。最初の状態は5 Tで出現し、隣接CDWの消失を伴う。磁場が既存ChernバンドのBerry曲率を均一化するという数値・幾何学的説明を提示する。

**適用条件・残る確認:** ゼロ磁場FCIはこの実験の観測結果ではなく将来の提案。スピン構造や準粒子の直接同定も残る。

**今回への適用:** 位相幾何と材料の設計条件。任意の真理値表を低ランク化する定理、ゲート恒等式、anyon braiding回路を提供しない。

### [5] Correlated insulating and superconducting states in twisted bilayer graphene below the magic angle (2019)

**著者:** Emilio Codecido et al.  
**一次資料:** [https://arxiv.org/pdf/1902.05151](https://arxiv.org/pdf/1902.05151)  
**取得/確認範囲:** `full_text` / `full_extracted_text_complete`。All extracted preprint text, characters 0–20138; opening re-read to repair truncated combined output.

**結果と根拠:** 0.93度の試料で半充填の相関絶縁状態と近傍の超伝導、さらに±5電子/単位胞の抵抗ピークを報告する。改良連続体計算は主magic angle以下でも狭いバンドと高エネルギー側の平坦領域を示す。

**適用条件・残る確認:** ±5の新しい絶縁状態の解釈は暫定的。二段階転移や不均一性の代替説明があり、図を独立数値化してはいない。

**今回への適用:** 探索を単一パラメータ点に限定しない発想は参考になるが、物理角度範囲をJ幅の改善境界へ換算する根拠はない。

### [6] Emergent ferromagnetism near three-quarters filling in twisted bilayer graphene (2019)

**著者:** Aaron L. Sharpe; Eli J. Fox; Arthur W. Barnard; Joe Finney; Kenji Watanabe; Takashi Taniguchi; Marc A. Kastner; David Goldhaber-Gordon  
**一次資料:** [https://arxiv.org/html/1901.03520](https://arxiv.org/html/1901.03520)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text characters 0–21558; supplement not read.

**結果と根拠:** 3/4充填近傍で大きい異常Hall応答、磁場履歴依存、非局所輸送、微小DC電流での磁化反転を観測する。論文はincipient Chern insulatorという解釈を提示する。

**適用条件・残る確認:** Hall抵抗は量子化せず散逸が残る。非局所信号も理想的QAHの実証ではなく、バルクや磁区の寄与を考慮する。

**今回への適用:** 物理実験での不完全な署名の扱いが参考になる。出力の一部一致や統計一致を厳密な量子oracle同値と見なす根拠にはならない。

### [7] Twisted bilayer graphene aligned with hexagonal boron nitride: Anomalous Hall effect and a lattice model (2019)

**著者:** Ya-Hui Zhang; Dan Mao; T. Senthil  
**一次資料:** [https://arxiv.org/html/1901.08209](https://arxiv.org/html/1901.08209)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text characters 0–23823; supplemental derivations not read.

**結果と根拠:** hBN整列によるC2対称性破れがDirac交差を開き、谷ごとに±1のChernバンドを生む。C2T保護が外れると伝導・価電子帯を合わせたWannier構成が可能で、拡張Hubbard/Haldane格子モデルを得る。3/4充填のChern絶縁体と圧縮可能なcomposite Fermi liquidを区別して提案する。

**適用条件・残る確認:** 最初の解析ではhBNの非整合moiré項を弱いとして落とす。単一伝導帯射影の極限と実験のU~W>gapは違うことを明示する。

**今回への適用:** 基底変換を使える条件を先に確定するという具体的教訓。GF(2)出力変換に使うなら固定語表で可逆性・再構成を別証明する必要があり、本論文だけでは費用減は出ない。

### [8] Signatures of tunable superconductivity in a trilayer graphene moiré superlattice (2019)

**著者:** Guorui Chen et al.  
**一次資料:** [https://arxiv.org/pdf/1901.04621](https://arxiv.org/pdf/1901.04621)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text 0–18552 and Methods 23952–27000; separate supplement not read.

**結果と根拠:** ABC三層/hBNで変位場により狭い孤立バンドを調整し、1/4充填Mott状態の近傍に超伝導の署名を報告する。温度・電流・磁場依存と、金属/絶縁体/候補超伝導間の変化を調べる。

**適用条件・残る確認:** 本文はcandidate/signaturesと表現し、残留抵抗や不均一性、未説明の磁場挙動も記載する。

**今回への適用:** 可調整の物性モデル。量子回路の測定後位相消去や表読み出しの構成法はない。

### [9] Imaging inter-valley coherent order in magic-angle twisted trilayer graphene (2023)

**著者:** Hyunjin Kim et al.  
**一次資料:** [https://arxiv.org/html/2304.10586](https://arxiv.org/html/2304.10586)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text and Methods characters 0–34551; long supplementary theory not read.

**結果と根拠:** STMで低歪み三層のKekulé格子三倍化とmoiré尺度の変調を測る。Fourierフィルタと原子位置を整列した自己相関で変調波数を抽出し、ドープ依存のincommensurate Kekulé spiralに整合する結果を得る。ゼロ磁場の信号から少なくともKramers-IVC候補を排除する。

**適用条件・残る確認:** 理論比較は歪み・Hartree変形等に依存する。画像のパターン同定は量子状態全体のトモグラフィーではない。

**今回への適用:** 有限語表の相関を調べる探索の着想にはなるが、Fourierピークの近似的一致をbit単位の恒等式と置換できない。

### [10] Evidence for unconventional superconductivity in twisted trilayer graphene (2022)

**著者:** Hyunjin Kim; Youngjoon Choi; Cyprian Lewandowski; Alex Thomson; Yiran Zhang; Robert Polski; Kenji Watanabe; Takashi Taniguchi; Jason Alicea; Stevan Nadj-Perge  
**一次資料:** [https://arxiv.org/html/2109.12127](https://arxiv.org/html/2109.12127)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Preprint main text characters 0–23603; supplementary Methods not read.

**結果と根拠:** STM/STSで鏡映対称領域、flat/Diracバンド、充填依存のHartree変形と超伝導的coherence peakを観測する。U形からV形のトンネルスペクトルを、単一nodal秩序のBEC–BCS転移などと比較する。

**適用条件・残る確認:** ペアリング機構は確定しない。低エネルギーphononや複数秩序の代替説明を残す。公開プレプリント題名はSpectroscopic Signatures...。

**今回への適用:** 弱く結合したsectorの存在を物理的に検証する例。任意入力での出力sector分離を保証せず、ローダー回路削減は導かない。

### [11] Tunable strongly coupled superconductivity in magic-angle twisted trilayer graphene (2021)

**著者:** Jeong Min Park; Yuan Cao; Kenji Watanabe; Takashi Taniguchi; Pablo Jarillo-Herrero  
**一次資料:** [https://arxiv.org/html/2012.01434v1](https://arxiv.org/html/2012.01434v1)  
**取得/確認範囲:** `full_text` / `full_extracted_text_complete`。Scientific text characters 0–61570 (all main text, Methods 1–8, Extended Data captions and acknowledgements). Site feedback footer excluded. arXiv v1 (2020-12-02); references render as unresolved citation keys.

**結果と根拠:** 鏡映対称な三層のflat bandとDirac bandの共存を利用し、変位場で混成・超伝導を調整する。zero-D連続体モデルは鏡映セクターに分解し、一方を有効角度が1/√2の二層へ写す。二キャリア/単位胞由来の超伝導、van Hove境界、GL長が粒子間隔に近づくこと、TBKT/TFが0.1以上になることを報告する。

**適用条件・残る確認:** Methodsのモデルは外側二層間の直接結合等を捨て、電場screeningの完全な自己無撞着計算は範囲外。弱い超伝導境界には例外も記載される。抽出HTMLの引用文献リストは欠落し、数式や単位の変換乱れが残る。

**今回への適用:** 対称性によるブロック分解の条件を明示する好例。ただし実数/複素数の層基底と√2を用いる変換はCNOTによるGF(2)出力基底ではなく、対称性を破る項を任意に省けない。

### [12] Unconventional non-local relaxation dynamics in a twisted trilayer graphene moiré superlattice (2022)

**著者:** Dorri Halbertal et al.  
**一次資料:** [https://www.nature.com/articles/s41467-022-35213-5](https://www.nature.com/articles/s41467-022-35213-5)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Abstract–Methods/Data availability characters 2986–42259; page recommendations excluded; supplementary material not read.

**結果と根拠:** 実際の対象はtwisted double trilayer。近接場・STMとDFTを照合し、一層の全体滑りによってABABAB/BCBACA領域が形成される説明を得る。一部の局所エネルギー増を、別領域の拡大と全体の弾性/積層エネルギー減が補う。Methodsは32積層候補と連続体緩和を説明する。

**適用条件・残る確認:** 数値最適化は特定の力学モデルによる。GSFEの一部は近い関数への制約付きフィットで近似する。

**今回への適用:** 局所コスト増も全体で評価する原則は共同合成に整合する。ただしエネルギー最小化と公式λQTは別目的で、準備・復元・全バッチを含む実ゲート集計が必要。

### [13] Local atomic stacking and symmetry in twisted graphene trilayers (2024)

**著者:** Isaac M. Craig; Madeline Van Winkle; Catherine Groschner; Kaidi Zhang; Nikita Dowlatshahi; Ziyan Zhu; Takashi Taniguchi; Kenji Watanabe; Sinéad M. Griffin; D. Kwabena Bediako  
**一次資料:** [https://arxiv.org/html/2303.09662](https://arxiv.org/html/2303.09662)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text 0–22916 and Methods/Data/Code 25252–31655; supplement not read.

**結果と根拠:** 干渉4D-STEMで層界面を選択的に調べ、AAAの縮小やAtA/AtBの面積比を直接測定する。わずかな非整列でAtBがほぼ消えるという従来像に対し、かなりのAtB領域が残る結果を示す。Methodsはマスク、強度閾値、平滑化、角度/歪み推定を説明する。

**適用条件・残る確認:** 空間分解能やGaussian平滑化、強度の混入、運動学的緩和不足の限界を記す。

**今回への適用:** 見かけの対称性を別の測定法で監査する教訓。全アドレスと全ターゲットの厳密照合の代わりにはならない。

### [14] Dirac spectroscopy of strongly correlated phases in twisted trilayer graphene (2023)

**著者:** Cheng Shen; Patrick J. Ledwith; Kenji Watanabe; Takashi Taniguchi; Eslam Khalaf; Ashvin Vishwanath; Dmitri K. Efetov  
**一次資料:** [https://arxiv.org/pdf/2204.07244](https://arxiv.org/pdf/2204.07244)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text characters 0–21320; supplementary theory/Methods not read.

**結果と根拠:** Dirac coneのLandau準位とflat-band gapの交差を用いて、隠れた相関gapの大きさとChern数を推定する。整数充填のC=0状態、分数充填CDW候補、変位場によるhybridization/相転移を解析する。

**適用条件・残る確認:** 強くhybridizeすると測定手法の前提が失われることを本文が明示する。抽出数式には添字欠落があり式の再実装には原PDF確認が必要。

**今回への適用:** 補助sectorで本体を診断する考え方は検証設計に類似するが、可逆補助レジスタの準備とcleanupを省ける定理ではない。

### [15] Evidence of a gate-tunable Mott insulator in a trilayer graphene moiré superlattice (2019)

**著者:** Guorui Chen et al.  
**一次資料:** [https://arxiv.org/pdf/1803.01985](https://arxiv.org/pdf/1803.01985)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main article characters 0–18812; remaining figure captions and separate SI not read.

**結果と根拠:** ABC三層/hBNで1/4・1/2充填の絶縁的輸送が変位場で強化される結果を報告する。低エネルギー二成分Hamiltonianとmoiré potentialを対角化し、帯域幅とCoulomb反発の競合で説明する。

**適用条件・残る確認:** 輸送gapとU−Wの推定は定性的対応である。取得PDFテキストの数式には欠落が多い。

**今回への適用:** 固定物理問題を別の有効模型に置換するなら誤差評価が必要。厳密ローダーのbit出力を変更する許可は与えない。

### [16] Four Moiré materials at One Magic Angle in Helical Quadrilayer Graphene (2025)

**著者:** Manato Fujimoto; Naoto Nakatsuji; Ashvin Vishwanath; Patrick Ledwith  
**一次資料:** [https://arxiv.org/html/2510.02444](https://arxiv.org/html/2510.02444)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text characters 0–30440; Appendices A–E not read.

**結果と根拠:** 四層の同方向twistを理論解析し、緩和後の四種の領域がほぼ共通の約2.3度で狭いバンドを持つと予測する。Type-Iでは±2 Chern基底、Type-IIでは別の量子幾何とdomain-wall networkを論じる。

**適用条件・残る確認:** 局所周期モデルと緩和計算に基づく予測。正確なvortexabilityはchiral limitで、実材料のFCIや超伝導を実証したものではない。

**今回への適用:** 共通パラメータで複数sectorを整理する発想のみ。本文のTは量子幾何のtrace-condition deviationであり、Tゲート数ではない。

### [17] Nature of even and odd magic angles in helical twisted trilayer graphene (2023)

**著者:** Daniele Guerci; Yuncheng Mao; Christophe Mora  
**一次資料:** [https://arxiv.org/html/2308.02638](https://arxiv.org/html/2308.02638)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Sections I–V and acknowledgments, characters 0–52946; appendices not read.

**結果と根拠:** chiral連続体模型の零モードを解析的に構成する。奇数magic angleではChern 2と−1の二平坦帯、偶数では四平坦帯とDirac coneが現れる。直交性、Wronskianの消失、零点の次数から生成元の数を説明し、C3z/C2yTと粒子正孔対称性の役割を分離する。

**適用条件・残る確認:** rankは複素波動関数の位置依存layer空間での次元。AA結合を戻すと有限帯域が生じ、粒子正孔対称性破れ等も別途解析される。

**今回への適用:** 核/商空間の証明方法は参考になるが、GF(2)多出力テンソルrankや乗法複雑度への移植定理はない。低ランクの発見だけで実CCXが減るともいえない。

### [18] Multi-moiré trilayer graphene: Lattice relaxation, electronic structure, and magic angles (2024)

**著者:** Charles Yang; Julian May-Mann; Ziyan Zhu; Trithep Devakul  
**一次資料:** [https://arxiv.org/html/2310.12961](https://arxiv.org/html/2310.12961)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Sections I–IV, characters 0–44951; appendices not read.

**結果と根拠:** 二角度の三層を緩和と局所連続体で系統探索する。最初のmagic angle近傍では比±1、+1/2で周期的domain、それ以外の調べた単純比では主に準結晶となる。相対shiftを固定した局所Hamiltonianやshift平均DOSでmagic lineを推定する。

**適用条件・残る確認:** 整合近似を作る微小strainは必ずしも実在しない。超moiré coherenceによる小gapを捨て、粒子正孔非対称も近似する。

**今回への適用:** 高側アドレスに応じた低側shift探索に形式的な類似はある。ただし各shiftの順列作用を厳密に戻し、出力tagも含める必要があり、物理近似は使えない。

### [19] Electronic Correlations in Rhombohedral Graphene at Atomic Scale (2025)

**著者:** Yufeng Liu et al.  
**一次資料:** [https://arxiv.org/pdf/2412.06476v1](https://arxiv.org/pdf/2412.06476v1)  
**取得/確認範囲:** `full_text` / `full_extracted_text_complete`。All extracted preprint text, characters 0–46277, including main, Methods, Extended Data captions and references. arXiv v1 (2024-12-09); arXiv metadata explicitly links published DOI.

**結果と根拠:** 著者公開稿は四層rhombohedral grapheneの電荷中性点で最大17 meVの相関gapを報告し、磁場・dopingによる抑制、intervalley干渉の不在、欠陥散乱をLAF解釈と結びつける。三層のCu tip測定はgapを示さず、Au tipによる外因的電場で大きいgapが生じ得ると比較する。欠陥近傍の三回対称束縛状態の解釈には追加のspin-sensitive検証を求める。

**適用条件・残る確認:** 公刊版題名はこの項目名、読んだ稿の題名はReal-space study of zero-field correlation in tetralayer rhombohedral graphene。公刊要旨の最大gapは19 meVで、公開稿の17 meVと版差がある。公刊本文そのものは取得できず、全図の独立検査もしていない。

**今回への適用:** 測定・モデルの外因と固有効果を切り分ける実例。LAFやSSHの物理的類推は固定語表の可逆乗法回路の恒等式ではない。実CCX削減は導いていない。

### [20] Fractional quantum anomalous Hall effect in multilayer graphene (2024)

**著者:** Zhengguang Lu; Tonghang Han; Yuxuan Yao; Aidan P. Reddy; Jixiang Yang; Junseok Seo; Kenji Watanabe; Takashi Taniguchi; Liang Fu; Long Ju  
**一次資料:** [https://arxiv.org/pdf/2309.17436](https://arxiv.org/pdf/2309.17436)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Entire fetched 35117-character preprint, including main text, captions, references and acknowledgements; separately cited Methods and Extended Data were not included or read.

**結果と根拠:** rhombohedral五層/hBNで整数および六つの分数充填にHall plateauと縦抵抗dipを観測し、磁気履歴がゼロ磁場を囲むことやStreda傾斜を併せてFQAHEを示す。1/2充填では抵抗dipがなく連続的Hall応答が残り、CFLに類似する挙動と解釈する。変位場で金属・絶縁相へ遷移する。

**適用条件・残る確認:** 概観の相図は±0.1 Tで対称化しており、ゼロ磁場の主張には別途hysteresis測定を用いる。CFL/相転移の詳細検証と非Abelian braidingは将来課題。Methods/Extended Data全体は未読、式のOCRに欠落がある。

**今回への適用:** トポロジカル計算の候補物理系であり、braidingを実装・検証した論文ではない。今回のゲート集合で任意XOR oracleを安価に合成する手法やToffoli数の改善を与えない。

### [21] Fractional Chern insulator states in multilayer graphene moiré superlattices (2024)

**著者:** Zhongqing Guo; Xin Lu; Bo Xie; Jianpeng Liu  
**一次資料:** [https://arxiv.org/html/2311.14368v2](https://arxiv.org/html/2311.14368v2)  
**取得/確認範囲:** `full_text` / `main_text_complete`。All main text and Methods, characters 0–59285; Supplementary Information S1–S6 and bibliography after it not read. arXiv v2 (2023-12-12).

**結果と根拠:** 高エネルギーのCoulomb相互作用を摂動RGで繰り込み、低エネルギー24バンドのHFを解き、ν=1の二つの競合HF状態から孤立帯を作り、hole doping後のED結果を比較する。3分の2と5分の3でFCI候補を得る。粒子・正孔変換後に異なるHF真空のエネルギー定数を保存しないと、候補間比較が誤ることをMethodsと式(6)–(7)で説明する。

**適用条件・残る確認:** EDは有限20/24/27サイトかつHF孤立帯への射影後の厳密解で、全元模型の厳密解ではない。12充填価電子帯を凍結する根拠は80–100 meV gapと約20 meV相互作用の分離。FCI判定のgap/spread閾値や有限サイズcross-overを明記する。公刊題名は多層、読んだv2題名はpentalayer。

**今回への適用:** 比較の基準状態と定数項を揃える手順は費用監査に参考となる。ただしエネルギー窓の射影やHF平均場で語表を近似することは許されず、32ターゲット全体・HMR枝の相対位相を保つ実装証明は別途必要。

### [22] Anomalous Hall Crystals in Rhombohedral Multilayer Graphene. I. Interaction-Driven Chern Bands and Fractional Quantum Hall States at Zero Magnetic Field (2024)

**著者:** Junkai Dong; Taige Wang; Tianle Wang; Tomohiro Soejima; Michael P. Zaletel; Ashvin Vishwanath; Daniel E. Parker  
**一次資料:** [https://arxiv.org/html/2311.05568](https://arxiv.org/html/2311.05568)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text characters 0–25165; long appendices not read.

**結果と根拠:** 自己無撞着Hartree–Fockで相互作用起源のChern bandとanomalous Hall crystalを得て、射影したbandのED/DMRGで2/3 FQAHを支持する。moiré potentialを消してもSCHFで秩序が残るため、相互作用が周期性と時間反転を同時に破る機構を提案する。

**適用条件・残る確認:** 7伝導帯への射影、spin/valley偏極を仮定。分数量子状態の計算はν=1のSCHF最低bandに制限し、著者自身がFCIを有利にするbiasとHartree–Fockの結晶化過大評価を記す。

**今回への適用:** モデルと対照計算を分ける良い例。EDのexactは射影済み模型の有限系内であり、全語表の厳密性や汎用oracleの証明にはならない。

### [23] Chiral Decomposition of Twisted Graphene Multilayers with Arbitrary Stacking (2023)

**著者:** ShengNan Zhang; Bo Xie; QuanSheng Wu; Jianpeng Liu; Oleg V. Yazyev  
**一次資料:** [https://arxiv.org/html/2012.11964](https://arxiv.org/html/2012.11964)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text characters 0–25037; separate supplementary material not read; 2020 preprint of 2023 publication.

**結果と根拠:** 任意積層N+Mをmoiré部分と残りのchirality-J doubletへ分ける規則を示す。chiral limitの低エネルギーHamiltonianを直和として扱い、A-ABAとA-ABACの一次/二次摂動でDirac/二次doubletを具体的に導く。変位場で平坦帯を分離しChern数を定義できる場合も解析する。

**適用条件・残る確認:** AA hoppingゼロ、nearest-neighbor層間結合、magic angleおよび低エネルギー射影という条件付き。全Hilbert空間の任意ユニタリの直和分解ではない。

**今回への適用:** 今回最も形式的に近いのは構造を基に分割して再構成する点。回路へ使うには有限語表の依存グラフで厳密な不変部分を証明する必要がある。論文中のJはchiralityで、バッチ幅Jとは別。

### [24] Topological flat bands in rhombohedral tetralayer and multilayer graphene on hexagonal boron nitride moiré superlattices (2023)

**著者:** Youngju Park; Yeonju Kim; Bheema Lingam Chittari; Jeil Jung  
**一次資料:** [https://arxiv.org/html/2304.12874](https://arxiv.org/html/2304.12874)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Sections I–V characters 0–49791; appendices not read.

**結果と根拠:** 四層/hBNから八層までの連続体模型で帯域、gap、valley Chern数、局所密度を探索する。電場・twist・基板配向で局在と帯域が変わり、狭いbandでも実空間に広がる場合がある。band overlapによるscreeningを加えると相関有望領域も変わる。

**適用条件・残る確認:** Ueff/Wは相関相の候補指標で、相関基底状態を全て解いたものではない。抽出本文には添字等の誤植があり数値式を移植していない。

**今回への適用:** 帯域の平坦さ、位相指標、波動関数の局在はそれぞれ異なる尺度。どれも二値表の低ランクやゲート数と同一視しない。

### [25] Superconductivity near spin and valley orders in graphene multilayers (2023)

**著者:** Zhiyu Dong; Leonid Levitov; Andrey V. Chubukov  
**一次資料:** [https://arxiv.org/html/2306.11005](https://arxiv.org/html/2306.11005)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Sections I–VI and acknowledgments, characters 0–59130; bibliography not read as separate full texts.

**結果と根拠:** 二谷のU1/U2/U3相互作用からspin/valley秩序近傍のpairing vertexをdiagram級数で求める。FM+/FM−ではそれぞれtriplet/singletの引力、CDWではsinglet引力等を得る。小さいU3でも有限次数で打ち切ると発散形を誤り、無限級数の和が必要であると示す。

**適用条件・残る確認:** 相互作用とpolarization bubbleを運動量に対して定数とする近似。SDWの非引力結論もその一定gap仮定に限定され、運動量依存を戻すと変わり得る。

**今回への適用:** 共通中間式の解析的因数化という一般的着想はあるが、実数/複素数のdiagram和をGF(2)可逆演算へ置換する規則は与えない。

### [26] Promotion of superconductivity in magic-angle graphene multilayers (2022)

**著者:** Yiran Zhang et al.  
**一次資料:** [https://arxiv.org/html/2112.09270](https://arxiv.org/html/2112.09270)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text and Methods characters 0–25247; extensive supplement not read.

**結果と根拠:** WSe2上の交互twist三・四・五層で相関相と超伝導を測定し、層数増加で超伝導の充填範囲が広がる。五層ではflat bandだけの単純な充填像を超え、Hartree shiftや分散bandとのhybridizationの役割を議論する。

**適用条件・残る確認:** 非相互作用でのTBG sector分離が実際の高充填まで有効とは限らない。層依存のchargeや遠方層結合で、鏡映対称でもmixingする。公開題名はAscendance...。

**今回への適用:** 単純なブロック分解の適用範囲を調べる教訓。材料層の追加が有利でも、公式λQTで量子ビット追加が有利になるとは限らない。

### [27] Spin-Polarized Nematic Order, Quantum Valley Hall States, and Field-Tunable Topological Transitions in Twisted Multilayer Graphene Systems (2022)

**著者:** Shihao Zhang; Xi Dai; Jianpeng Liu  
**一次資料:** [https://arxiv.org/html/2101.04711](https://arxiv.org/html/2101.04711)  
**取得/確認範囲:** `full_text` / `main_text_complete`。Main text characters 0–24195; supplementary analysis not read.

**結果と根拠:** 二層–一層および二層–二層をHartree–Fockで解析し、半充填でspin偏極nematic絶縁相を予測する。intra-valley Coulombのみで近接するvalley偏極との縮退をon-site Hubbard項が分裂させ、弱い磁場のorbital Zeeman/密度補正がQAH相へ競合する。

**適用条件・残る確認:** 模型の基底状態はHF近似下での結果。谷間の長距離相互作用と弱磁場Landau量子化を省くなど適用条件を持つ。

**今回への適用:** 一見小さな項でも縮退を解く例。ローダーのtag、復元、HMR位相など小コスト項を省略しない動機にはなるが、直接の合成法ではない。

### [28] Quantum Valley Hall Effect, Orbital Magnetism, and Anomalous Hall Effect in Twisted Multilayer Graphene Systems (2019)

**著者:** Jianpeng Liu; Zhen Ma; Jinhua Gao; Xi Dai  
**一次資料:** [https://journals.aps.org/prx/pdf/10.1103/PhysRevX.9.031021](https://journals.aps.org/prx/pdf/10.1103/PhysRevX.9.031021)  
**取得/確認範囲:** `full_text` / `full_extracted_text_complete`。Entire 14-page extracted paper, characters 0–64533, including Appendices A–C and references; equations have substantial PDF extraction damage.

**結果と根拠:** chiral積層M+Nの二平坦帯とChern-number hierarchyを提案し、より現実的なtight-bindingとの比較を行う。Appendix Aは基底変更と零pseudo-Landau-level射影、Bはchiralityに応じたChern和、Cは局所電流の計算法を与える。

**適用条件・残る確認:** Appendix Aは高いpseudo-Landau levelを捨て、連続体結合も線形化する。遠方hoppingでchiral対称性が破れ、hierarchyは全積層で厳密には残らないことを本文が明示する。数式OCRは独立検算不能箇所あり。

**今回への適用:** 正確な基底変換と部分空間への射影を区別する資料。全ターゲットXOR oracleでは射影やgarbageの廃棄を認められないため、同じ縮小は適用できない。
