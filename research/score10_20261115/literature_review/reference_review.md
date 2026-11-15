# 指定論文と参考文献全171項目の調査台帳

全項目に出典・読解範囲・内容・今回の回路への適用判断を付けた。全文通読、本文全体の読解、該当節の読解、公開previewだけの確認を区別する。

本文取得を読了と数えない。全件を同じ深さで通読したという主張ではない。図画像・全証明・全実験の独立検算ではない。

番号は shallow=主論文の公刊版/v2、magic=記号表の出典、graphene=グラフェン論文。主論文v1のみの55は独立行で保持する。

| 系統 | 項目数 | 抽出テキスト全読 | 本文全節 | 本文文章・表数式欠落 | 主要結果・選択節 | preview等 |
|---|---:|---:|---:|---:|---:|---:|
| 主論文（旧版差分込み） | 62 | 34 | 26 | 0 | 0 | 2 |
| 記号表の出典 | 53 | 53 | 0 | 0 | 0 | 0 |
| グラフェン論文 | 56 | 5 | 48 | 3 | 0 | 0 |

主論文[14] Kitaev 1997 は8頁のうち公開preview2頁のみ。主論文[43]は質問と全回答テキストを読了したが回路画像4枚は未取得。

graphene[31]はTable 1の表セル、[32]は画像化された数式、[47]はHTMLで欠けた数式に未取得箇所がある。文章の全節読解と区別した。

同一原著の5組の重複は読解情報を共有するが、文献欄上の項目数には両方を含める。

## shallow:1 — S. Aaronson and A. Arkhipov, The computational complexity of linear optics, in Proceedings of the forty-third annual ACM symposium on Theory of computing (2011) pp. 333–342.

**一次資料:** https://arxiv.org/pdf/1011.3245

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加で§1後半（1.3–1.4を含む）から§§2–11までの連続186,238文字を通読。前担当の冒頭約28,000文字に1,000文字以上重ね、主本文全節・本文内の全証明・実験手順・open problems・謝辞を確認した。取得版は arXiv:1011.3245v1 (2010-11-14)、STOC2011の長編著者版。

**内容:** 非相互作用 boson の物理定義・多項式/Fock内積・永久行列式を用いる定義の同値を構成し、標準入力からの非適応 photon-number sampling を扱う。厳密 classical sampling ⇒ P^#P⊆BPP^NP を、signed permanent の乗法近似困難性＋Stockmeyer と postselected KLM の二通りで導く。近似 sampling からは Gaussian 行列の |Per(X)|² の ε n! 加法推定をBPP^NP内へ帰着し、PH collapse には Gaussian permanent の平均時乗法近似困難性および anti-concentration の追加予想が必要。Haar truncation と Gaussian の近さは m≥n^5 δ^-1 log²(n/δ) の証明範囲で、m=O(n²)への改善はこの版では未証明。§7 は小さい複素平行移動と triangulation で位相を回収し、oracle 精度と失敗確率を制御。§8は determinant の反集中と permanent の弱い確率下界を証明するが PACC を証明しない。§9はGaussian permanent の exact/指数高精度平均時困難性を示し、通常の低次数補間だけでは多項式相対精度へ進めない障壁を説明。

**今回の実装への判断:** 適用上は、sampling・単一出力確率・任意入力 coherent oracle を区別するための基礎。§6.3 の O(mn) optical elements / O(n log m) depth 構成は既知の標準入力、最初のn列、追加n modes を使う state preparation で、未知の任意入力に同じunitaryを実装する定理ではない。J=4 loader の4170という改善境界やToffoli最適下界を与えず、postselection を無料操作としてKMBへ持ち込めない。加法精度が指数的に小さい出力確率の相対精度を保証しないという区別は公式一致判定や誤差予算に関係する。

**留保:** Appendix12 は前担当が冒頭約5,000文字のみ確認済みで、残りとAppendix13は未読。本追加台帳は主本文完了であり93頁全体の全文読了ではない。図は本文・キャプションで読解し全画像の個別確認はしていない。理論の証明読解と独立再証明・現在の実験性能検証を区別する。2010版の機器性能・実験未実施の記述・予想の状態を2026年の事実として扱わない。近似 sampling のinputは誤差逆数をunaryで与えるFPTAS型であり、任意の固定誤差での困難性までこの本文から主張しない。

## shallow:2 — S. Aaronson and A. Arkhipov, Bosonsampling is far from uniform, arXiv preprint arXiv:1309.7460 (2013).

**一次資料:** https://arxiv.org/pdf/1309.7460 / https://arxiv.org/abs/1309.7460

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加で §§5–8（§7.1・§8.1、全補題・定理の証明を含む）および謝辞を通読。既読の Abstract・§§1–4 と §9 を合わせ、主本文の全節を確認。本文は arXiv:1309.7460v2 (2013-10-01)。

**内容:** 一般の検証と、出力ラベルを捨てる symmetric verifier を区別。Haar 行列・m≥n^5.1/δ・十分大きな n の範囲で BosonSampling の衝突なし分布と一様分布の定数全変動距離を示す。行ノルム積 R*=Π_i||row_i(X)||²/n^n は O(n²) 計算で一様との定数バイアス識別を可能にする。証明は複素 Gaussian の行方向とノルムの独立性、P=Q R*、log χ² の累積量と Berry–Esseen、Haar 部分行列近似に依存。m≈n² は予想で、証明された範囲と区別。情報理論的サンプル数と計算時間は別問題。

**今回の実装への判断:** 特定の偽分布を排除する統計と、回路の全入力・位相を検証することは別の保証。R* は永久行列式の高精度近似器ではなく、KMB oracle を合成する方法にもならない。GVQCC の全アドレス一致やコヒーレント入力の位相検証を、少数の統計量一致へ置き換える根拠にはならない。

**留保:** Appendices 11–13 は今回通読していない。本文自身、R* だけでは distinguishable-particle の mockup M_A、FermionSampling、独立行サンプリング B_A を排除できず、量子干渉さえ証明しないと明記。§8.1 のこれら別分布の他の統計での排除については future work の未証明部分を含む。過去の実験規模・計算時間見積りを現在値と扱わない。

## shallow:3 — A. M. Childs, D. Gosset, and Z. Webb, Universal computation by multiparticle quantum walk, Science 339 , 791 (2013).

**一次資料:** https://arxiv.org/pdf/1205.3782

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 主本文の冒頭から Discussion 末尾まで（約29,200文字）を読了。付録の散乱・誤差証明は未読。

**内容:** 相互作用する多粒子の量子歩行を用い、静的 Hamiltonian と最大次数4の疎な平面グラフで普遍計算を構成する。厳密構成では波束長・実行時間・グラフ規模に大きい多項式 overhead がある。

**今回の実装への判断:** アナログな散乱ゲートを許可ゲートへ再コンパイルした費用は別に必要。普遍性だけから、128量子ビット以内で低 Toffoli のローダーが得られるとは判断できない。

## shallow:4 — S. Aaronson and L. Chen, Complexity-theoretic foundations of quantum supremacy experiments, arXiv preprint arXiv:1612.05903 (2016).

**一次資料:** https://arxiv.org/pdf/1612.05903 / https://arxiv.org/pdf/1612.05903v2

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 先行読解のAbstract・序論冒頭と§4に、rootの残る序論、§§2–3・5–9、謝辞・参考文献、Appendices A–Eの全抽出テキストを統合。取得テキスト0–203939文字を共同で全読した。図は抽出説明を読み、全画像の独立確認は行っていない。

**内容:** HOG（高確率出力の生成）の困難性をQUATH仮定から導き、検査を通過する出力の生成と分布全体の近似サンプリングを区別する。一般回路の振幅を多項式空間・d^{O(n)}時間で評価する再帰と時間・空間交換、格子局所性を使う改善を示す。近似サンプリングとPH崩壊を結ぶ強い一般定理には非相対化が必要と示し、Fourier Samplingの1量子問い合わせ対Ω(2^n)古典問い合わせの分離を十分小さい固定誤差で証明する。P/polyオラクルの分離にはone-way function等の計算量仮定を明示する。

**今回の実装への判断:** 回路検証のメモリ削減には深さ分割・小さい切断を持つ窓の収縮が候補になるが、実量子回路のCCX数を減らす定理ではない。HOGを通過することは任意入力・位相・作業領域が一致する証明にはならない。オラクルへのアクセスを1回と数える問い合わせ下界や近似置換を、既知の1220アドレス表の合成費用4170の境界へ流用しない。

**補完読解で確認した点:** §3の主たる困難性はQUATHを仮定し、ランダム回路の出力非一様性を高確率で保証するConjecture 1は本文では予想のまま。Appendix Eの有限サイズ数値実験はその証明ではない。 / §§5・8のオラクル置換は初期状態と到達分布に関する誤差評価であり、全入力の厳密な演算子恒等式ではない。 / Appendix Aの古典/量子one-way functionの仮定、Appendices B–Dの補助証明、Appendix Eの実験設定まで確認した。2016年の実験規模・計算機見積りは現時点の性能情報として用いない。

**留保:** 抽出テキストには数式の改行・上付き下付きの崩れがある。図の全画素確認、全証明の独立再導出、Appendix Eのシミュレーション再実行は行っていない。参考文献の再帰的な全原著調査には広げていない。

## shallow:5 — D. Deutsch and R. Jozsa, Rapid solution of problems by quantum computation, Proceedings of the Royal Society of London. Series A: Mathematical and Physical Sciences 439 , 553 (1992).

**一次資料:** https://www.isical.ac.in/~rcbose/internship/lectures2016/rt08deutschjozsa.pdf

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 6頁の抽出本文を参考文献まで読了。図の独立した画素検査は行っていない。

**内容:** constant/balanced の promise を用いる。1992年の原構成は Uf S Uf と oracle を2回呼び出す。任意の第二レジスタ j に対する可逆 oracle を定義し、計算・位相操作・逆計算で作業レジスタを戻す。

**今回の実装への判断:** ゼロターゲットだけでなく任意 y に |a,y>→|a,y XOR f(a)> を満たすという契約を支持する。現代の1-query版と原論文を混同しない。Toffoli 削減手法は提示しない。

## shallow:6 — P. W. Shor, Algorithms for quantum computation: discrete logarithms and factoring, in Proceedings 35th annual symposium on foundations of computer science (Ieee, 1994) pp. 124–134.

**一次資料:** https://math.mit.edu/~shor/papers/algsfqc-dlf.pdf

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** cost_auditの本文テキスト読解に、rootの著者公開PDF全11頁の実画像読解を統合。PDF自体の頁順が逆なので物理頁10→0（0始まり）で論理頁1→11を読んだ。Abstract、§§1–7、式(2.1)–(7.41)、Figure 1、謝辞、全33参考文献を確認し、数式OCR欠損を元画像で補完した。

**内容:** 因数分解を位数発見へ帰着し、可逆なmodular exponentiation、Fourier変換、測定、連分数による周期回復を組み合わせる。離散対数はp−1がsmoothな場合から一般の場合へ拡張し、確率解析と再試行・古典検算を含む。初期稿のsmooth q構成とCoppersmithの2^k Fourier変換への言及、有限精度で成功確率を保つ議論を区別して確認した。

**今回の実装への判断:** §2のFact 1は、入力を残してfを計算できることと、入力を消してfへ置き換えられることを分ける。後者には単射性とf^{-1}の効率的実装が必要で、前バッチの語を破壊的に上書きしてよい根拠にはならない。位数・Fourier構造を持たない固定75語lookupへそのまま適用できるゲート削減は示されていない。

**補完読解で確認した点:** §2の式(2.2)–(2.5)は、同じ基底測定確率を持つ状態でも相対位相によって後続ユニタリの結果が異なる例。全アドレスの出力値だけでなくHMR位相を追う今回の検証方針に直接関係する。 / Figure 1はq=240、r=13の出力確率で、240/13の整数倍付近にピークがある。例示図を1220アドレスの厳密ローダー検証へ置き換えるものではない。 / 有限精度のFourier変換で成功確率を保つ議論は、今回のBoolean語写像の完全一致要件を緩める許可ではない。

**留保:** 著者サイトはこのPDFに小修正と図の追加があると明記している。1994年会議録の版そのものと完全同一とはしない。本文・数式・図は読んだが、全数論証明の独立再導出や実機再現は行っていない。

## shallow:7 — D. R. Simon, On the power of quantum computation, SIAM journal on computing 26 , 1474 (1997).

**一次資料:** https://www.cs.miami.edu/home/burt/learning/csc595.251/s0097539796298637.pdf

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 10頁の抽出本文・証明・参考文献を読了。

**内容:** 一対一または共通 XOR period を持つ二対一という promise の下で、Fourier sampling から period に直交する線形方程式を得る。oracle 相対の指数的隔たりを示す。

**今回の実装への判断:** 固定真理値表に共通 period があるかは古典的に全行検査できる。ただし一般の75語表に promise はなく、Simon を組み込むこと自体はローダー削減にならない。

## shallow:8 — P. W. Shor, Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum computer, SIAM review 41 , 303 (1999).

**一次資料:** https://arxiv.org/pdf/quant-ph/9508027 / https://arxiv.org/pdf/quant-ph/9508027v2

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 補完担当が28頁の全83,822文字、§§1–7・すべての数論的証明・参考文献表を実読。図のキャプションと抽出テキストは確認したが全図画像を個別に視認したものではない。実読したのは1996年arXiv v2であり、参考文献表に挙げられた1999年SIAM Review版そのものではない。

**内容:** 素因数分解を位数発見に帰着し、n²≤q<2n²の2冪qに対するQFT後のc/qから連分数でd/rを復元する。gcd(d,r)=1となる割合からO(log log r)回の試行で成功し、少数の倍数探索・複数試行のLCMなど古典後処理も論じる。離散対数ではg^a x^{-b}の計算と二つのQFTを用い、qがp−1でなく2冪である誤差も解析し、良好な標本の定数確率下界を示す。§3の可逆論理では入力を保持してFと作業ビットを計算し、結果を新しいレジスターへコピー後に計算を逆転して作業領域を消す。元の入力まで消してFのみを残すにはFの可逆性と効率的な逆計算を要する。固定x,nについてx^(2^i) mod nを古典前計算し、可逆な固定定数乗算を反復して剰余指数を計算する。乗数cがnと互いに素である場合はc^{-1}を使って古いレジスターを消去できる。学校式乗算ではl桁にO(l³)時間・O(l)空間の構成を説明し、一般的な可逆化の時間・空間交換も扱う。回路とゲートの情報を効率的に記述・計算できる一様性条件を明記し、振幅や回路記述に難しい答えを埋め込むことを排除する。

**今回の実装への判断:** 固定定数の前計算、compute–copy–uncompute、既知の逆演算によるレジスター再利用は、ローダーやinvsqrtの再計算・消去設計を評価するための具体的原則になる。ただし可逆化が増やす実Toffoli数と最大同時量子ビット数を実KMBで両方測る必要がある。固定定数乗算の逆演算は、任意の未知ビットを無料リセットする手法ではない。学校式乗算と高速乗算の漸近的差や古典のword演算数から、現在の固定精度KMBにおける費用改善を直接導けない。chemistryの提出回路については公式の到達可能部分空間とcoherentな消去の条件を個別に満たすか確認する。

**留保:** 古典的素因数分解が超多項式時間を要するという証明ではない。QFTの微小角を落とす近似は素因数分解の成功確率に関する許容誤差であり、正確なBoolean oracleの同一性を保証しない。Hや一般の制御位相を含むため、そのまま現在のKMB許可ゲートへ移せるとは限らない。理想的には0と証明された補助レジスターの測定による誤り検出・Zeno効果の議論は、未消去の未知情報を測定してよいという意味ではない。ハードウェア・デコヒーレンス・高速乗算についての記述は1996年の知見であり最新状況の断定に用いない。全証明を独立に再実装したという意味ではない。

## shallow:9 — R. P. Feynman, Simulating physics with computers, in Feynman and computation (cRc Press, 2018) pp. 133–153.

**一次資料:** https://www.ccsl.carleton.ca/~saran/other-papers/Feynman_SimulatingPhysicsWithComputers.pdf

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 原著1982年版の全54,572文字（§§1–9および質疑応答全文）を実読。shared既読部と合わせるだけでなく、補完担当自身も全テキストを確認した。図は本文の説明・抽出ラベルを確認し、全画像を個別に視認したものではない。2018年の再録版そのものは未確認。

**内容:** 有限の空間時間体積に比例する資源で物理を模擬したいという問題設定。確率分布全体の明示的保存と、その分布から実験と同じ統計を標本抽出することを区別する。局所確率更新モデルを検討すると、量子の密度行列/Wigner類似表現では負の係数が必要になる。光子対相関の例では局所・正の隠れ変数モデルの30度一致率上限2/3と量子予測3/4を比較する。量子格子による量子系の模擬を提案するが、相互模擬可能なクラスやFermi粒子の扱いは当時の未解決問題として提示する。時間方向の局所更新と時空境界値条件の違い、離散化と量子化の違いも説明する。

**今回の実装への判断:** 背景と検証の仕様整理に使う。全分布・期待値・標本・coherent oracleは別の要求であり、古典的標本抽出の可能性から未知入力を保持する量子ローダー実装を導けない。局所隠れ変数の不可能性は任意の非局所古典計算法の時間下界を証明しない。Toffoli最小数、J4の4,170境界、KMB幅・費用への直接の改善手段を与える論文ではない。

**留保:** 現代のBQP対BPPや一般強/弱シミュレーションの厳密計算量分類をこの講演から主張しない。物理の時空離散化についての発言は著者の探索的問題提起であり、実証済み結論と扱わない。

## shallow:10 — A. M. Childs, D. Maslov, Y. Nam, N. J. Ross, and Y. Su, Toward the first quantum simulation with quantum speedup, Proceedings of the National Academy of Sciences 115 , 9456 (2018).

**一次資料:** https://arxiv.org/pdf/1711.10980

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 主論文全文、Appendix E全文、Appendix G.3 と G.4 の制御生成・最適化の証明および費用集計を確認。他の長い付録は未読。

**内容:** Hamiltonian simulation の複数方式を具体回路で比較する。SELECT の二進木巡回で共通制御を使い回し、Toffoli対の恒等式・極性変更を使う。NCT制御生成構成は ≤1.5·2^w−4 Toffoli、w−1 clean ancilla。Clifford+T分解では別の相殺も行う。

**今回の実装への判断:** アドレス変数順序とprefix DAGを候補にする。既存共有bankの節約を二重計上せず、128Q以内で追加制御の準備・消去まで実測する。G.6は限定NCT制御生成モデルの下界であり、一般の多出力ローダー下界ではない。H/T/Phaseの最適化は化学の許可集合で再実装が必要。

## shallow:11 — A. J. Daley, I. Bloch, C. Kokail, S. Flannigan, N. Pearson, M. Troyer, and P. Zoller, Practical quantum advantage in quantum simulation, Nature 607 , 667 (2022).

**一次資料:** https://pure.strath.ac.uk/ws/portalfiles/portal/139863900/Daley_etal_2022_Practical_quantum_advantage_in_quantum_simulation.pdf

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、I–VIの全本文、Boxes 1–3、Figures 1–2の抽出説明、Table I、謝辞・著者貢献・利益相反まで読解。参考文献の途中まで含む0–105000文字の範囲を確認した。Box 3等に混入した20個のLaTeXiTシリアライズ文字列は非本文メタデータとして出力から除外した。別ファイルSupplementary Informationと残る参考文献欄は未読。

**内容:** 多体系の動力学について、古典計算の圧縮・サンプリング限界と、アナログ、誤り訂正デジタル、両者を併用する量子シミュレーションを比較する。Hubbard模型の例で較正誤差、Trotter誤差、論理ゲート合成、物理誤り訂正の費用を分ける。検証として異なる装置の比較と局所Hamiltonian learningを説明し、後者は多項式個の局所項からなるモデルAnsatzを前提とする。

**今回の実装への判断:** 資源評価では目標精度と実装層を固定して比較する、という点が今回に有用。Hamiltonianの少数パラメータを学習できても、任意入力のローダーの位相を含む全作用が一致したことにはならない。アナログ装置の一括時間発展を今回の許可ゲート1個として換算できず、T-depthや物理量子ビットの改善をnative Toffoli数の改善とはしない。

**補完読解で確認した点:** §IV BとBox 3は、全量子状態のtomographyと局所Hamiltonianのパラメータ推定を明確に分けている。未知の非局所項を無条件に排除する証明にはならない。 / 本文・Table Iの「today」「next 2–3 years」は2022年の状況・展望。現在の装置規模や計算能力についての記述として流用しない。 / 近似数値計算が難しい科学問題を解く有用性と、固定Boolean oracleのゲート最小化は異なる課題である。

**留保:** 図・Box内の数式は抽出されたテキストと説明を読んだ範囲で、画像全体の独立確認は行っていない。別ファイル補足にある詳細な誤差予算・ゲートカウント計算は未読で、再現済みとはしない。

## shallow:12 — E. Knill, D. Leibfried, R. Reichle, J. Britton, R. B. Blakestad, J. D. Jost, C. Langer, R. Ozeri, S. Seidelin, and D. J. Wineland, Randomized benchmarking of quantum gates, Physical Review A—Atomic, Molecular, and Optical Physics 77 , 012307 (2008).

**一次資料:** https://arxiv.org/pdf/0707.0963

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** §§I–VI、Appendix A、図のcaptionと参考文献を含む抽出本文を全読。

**内容:** 既知の最終測定を持つランダム Clifford 列の減衰から平均的ゲート誤差を推定し、SPAMと分離する。解釈には定常性・記憶なし等の仮定がある。

**今回の実装への判断:** ハードウェア誤差の評価法であり、コンパイラの厳密等価性を証明する検査ではない。統計的fidelityを全アドレス・任意入力・位相検証の代わりにしない。

## shallow:13 — D. Gottesman, Stabilizer codes and quantum error correction (California Institute of Technology, 1997).

**一次資料:** https://arxiv.org/pdf/quant-ph/9705052

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 同一文献を記号表論文の参考文献として全文補完。Complete primary extracted thesis text read: front matter, Chapters 1–8, Appendices A–B and bibliography [1]–[65]. Captions and extracted code tables read; not every circuit figure pixel or formula transcription independently audited.

**内容:** Pauliの共役と符号空間の論理演算子で演算を追跡する。測定の負の分岐を正の分岐へ直すには、既知の安定化子と反可換性が必要。Toffoli注入は非Clifford ancillaの作製費を必要とする。

**今回の実装への判断:** HMR後の補正と任意ターゲットを論理X/Zまで追う検証に直接役立つ。Toffoliを注入回路に書き換えても、magic ancillaの準備を無料にはできない。

同一文献: magic:25

## shallow:14 — A. Y. Kitaev, Quantum error correction with imperfect gates, in Quantum communication, computing, and measurement (Springer, 1997) pp. 181–188.

**一次資料:** https://link.springer.com/chapter/10.1007/978-1-4615-5923-8_19

**読解状態:** 公開previewのみ読解

**実読範囲:** 出版社のabstractとpp.181–182の2頁previewを全読。pp.183–188の6頁は取得不可。別題のKitaev論文で代用していない。

**内容:** 不完全ゲートの下の誤り訂正を扱い、低い一定decoherence率での耐故障保存を導入する。previewではsymplectic check operatorによる符号を説明する。全証明は確認できない。

**今回の実装への判断:** 物理的QEC overheadと今回の論理ゲート採点を区別するための背景。未取得の6頁について回路恒等式・閾値証明を検証済みとはしない。

## shallow:15 — D. Gottesman, The heisenberg representation of quantum computers, arXiv preprint quant-ph/9807006 (1998).

**一次資料:** https://arxiv.org/pdf/quant-ph/9807006

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 20頁の抽出本文、examples、測定節、結論・参考文献まで読了。PDF再生成日を出版年に使っていない。

**内容:** Clifford演算・Pauli測定・古典条件付きCliffordをPauli生成元で追跡する。測定Aと反可換な既知安定化子Mにより分岐を補正する。任意入力は論理X/Zを保持して扱う。

**今回の実装への判断:** 局所HMR cleanupの位相込み証明に適する。ゼロ入力の状態一致のみでは未知32ビットの写像を証明できない。Toffoli部分は非Cliffordなので純粋tableauだけでは処理できない。

## shallow:16 — S. Aaronson and D. Gottesman, Improved simulation of stabilizer circuits, Physical Review A—Atomic, Molecular, and Optical Physics 70 , 052328 (2004).

**一次資料:** https://arxiv.org/pdf/quant-ph/0406196

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 同一文献を記号表論文の参考文献として全文補完。Complete cached primary manuscript text actually read; image pixels not inspected. Reading does not independently certify every proof.

**内容:** stabilizer/destabilizerの二重tableauで測定をO(n²)時間にし、Clifford回路のcanonical formを構成する。少数非Cliffordへの拡張はその個数に指数依存する。ユニタリの等価性は2n個のPauli像で判定する。

**今回の実装への判断:** Clifford区間の独立等価性チェックに利用できる。CNOT総数の削減だけではToffoli採点は改善せず、canonical formのH/Pをそのまま化学へ出力できない。

同一文献: magic:26

## shallow:17 — H. J. Garcia, I. L. Markov, and A. W. Cross, Efficient inner-product algorithm for stabilizer states, arXiv preprint arXiv:1210.6646 (2012).

**一次資料:** https://arxiv.org/pdf/1210.6646

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** §§I–VIIの主本文を読了。Appendix Aの1080個の3-qubit state一覧は全読していない。

**内容:** canonical stabilizer matrix、H-C-CZ-P-Hのstate-normalization回路、O(n³)内積計算を構成する。stabilizer frameでは各成分の位相も必要。state synthesisと任意入力unitary synthesisは異なる。

**今回の実装への判断:** 小規模Clifford候補の状態比較・重複除去に使える。内積の絶対値だけでは相対位相は消えるため、複素係数を含む検証では位相を追跡する[18]の説明を併用する。

## shallow:18 — H. J. García, I. L. Markov, and A. W. Cross, On the geometry of stabilizer states, Quantum Information & Computation 14 , 683 (2014).

**一次資料:** https://www.rintonpress.com/xxqic14/qic-14-78/0683-0720.pdf

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加で §2（stabilizer formalism・canonical form・simulation・cofactor・quadratic form）、§3（全小節、計数・極限・bivector・線形依存の証明）、§§6–7 と謝辞を通読。既読の Abstract・§1・§§4–5 と合算し、主本文全節の結果・アルゴリズム・証明を確認。

**内容:** n独立 commuting Pauli generators による状態表現、Gaussian elimination の canonical generator 形、Clifford conjugation と測定を説明。異なる非直交 stabilizer の overlap は2^(-k/2)、nearest neighbors は4(2^n−1)、k-neighbor の計数とほぼ直交への集中を導く。状態を基底状態へ移す5ブロックの Clifford 正規化回路は O(n²) gates、内積計算は一般 O(n³)、構造化入力では O(n²) の実験傾向。実験は20–500qubit、βceil(n log2 n) の random Clifford gate 生成で entanglement を変化させる。最寄 stabilizer の local search が一般に保証されないこと、poly-size stabilizer 重ね合わせで近似できない unbiased 状態族を示す。

**今回の実装への判断:** Clifford 部分の位相付き正規化・内積・cofactor 処理は回路の独立検証や表現改善に使える。状態 preparation を canonical 化して得る Clifford gate 削減は、非線形 Boolean loader の CCX 削減と同一ではない。stabilizer の線形結合を短く表現できることも、その和を低コストのコヒーレント oracle として実装する保証ではない。KMB の入力領域・測定分岐・相対位相を含む同値性は別途必要。

**留保:** Appendix A の全1080個の3qubit stabilizer 列挙表は未読。本文中の表と図キャプションは抽出で読んだが、全図のピクセル確認・各証明の独立再証明や実験再実行はしていない。global phase を正規化した幾何の議論を、制御された回路や coherent branches の相対位相を無視する許可として扱わない。

## shallow:19 — S. Bravyi and D. Gosset, Improved classical simulation of quantum circuits dominated by clifford gates, Physical review letters 116 , 250501 (2016).

**一次資料:** https://arxiv.org/pdf/1601.07601

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 同一文献を記号表論文の参考文献として全文補完。Complete cached primary manuscript text actually read; all captions but not image pixels. Full reading is distinct from independent proof or implementation verification.

**内容:** exact stabilizer decompositionで出力確率を相対誤差推定し、approximate decompositionで分布を小さいL1誤差でsampleする。postselection確率の正規化を明示し、norm estimationをrankの二乗から線形へ改善する。

**今回の実装への判断:** 少数CCXを含む局所検証の候補。全回路5197 CCXへ指数アルゴリズムを適用する実益は未確認。近似samplingと相対確率推定を、厳密なoracle等価性に取り替えない。

同一文献: magic:17

## shallow:20 — S. Bravyi, G. Smith, and J. A. Smolin, Trading classical and quantum computational resources, Physical Review X 6 , 021043 (2016).

**一次資料:** https://arxiv.org/pdf/1506.01396

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 14頁の主本文、Appendices A–Cの証明、参考文献を含む抽出本文を全読。

**内容:** sparse circuit/PBCにvirtual qubitを足す代わりに2^O(k)回の反復と古典処理を使う。Pauli測定のPBCと低stabilizer rankを構成し、6-copy magic stateの7項分解を与える。出力は古典確率の加法近似である。

**今回の実装への判断:** 128Q制限を古典的なquasi-probability和で回避しても、coherentなローダー置換にはならない。7項最適という当時の予想は[23]で改良されており、探索上界を下界として扱わない。

## shallow:21 — S. Bravyi, D. Browne, P. Calpin, E. Campbell, D. Gosset, and M. Howard, Simulation of quantum circuits by low-rank stabilizer decompositions, Quantum 3 , 181 (2019).

**一次資料:** https://arxiv.org/pdf/1808.00128 / https://arxiv.org/pdf/1808.00128v2

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 補完担当が§4.3 Fast norm estimation 全文から末尾まで、文字区間[82866,172410)の89,544文字を実読。§§5.1–5.4、6.1–6.4の全証明、§7、60件の参考文献表を含む。shared_synthesisの§§1–3・4.1–4.2全文の実読と合わせて、主資料48頁の全文テキストをカバーする。各参考文献60件の原著を再帰的に全読したという意味ではない。

**内容:** §4.3: ランダムなequatorial stabilizer state φ_Aに対しη_A=2^n|<φ_A|ψ>|²が||ψ||²の不偏推定量、分散≤||ψ||⁴。k項の既知CH-form分解なら相対誤差ε・失敗確率δでO(k n³ ε^-2 log(1/δ))。二次形式のGF(2)/Z4指数和を変数2個ずつ消去しO(n³)で計算する。全n出力の条件付きsamplingを逐次ノルム推定すると精度蓄積のためO(k n^6)に達し、Metropolisは混合時間一般保証なし。§5: exact rankはt≤5の対称部分空間のstabilizer spanningによりχ(ψ^⊗t)≤binom(2^n+t−1,t)。sparsificationは係数ℓ1ノルムからχ_δ(ψ)≤δ^-2 ξ(ψ)を与え、正規化前の近似ベクトルの状態ノルム誤差を制御する。Clifford magic statesではξ=1/F。CCZはF=9/16、ξ=16/9、独立なt個の近似rank上界はδ^-2(16/9)^tで、4Tへ分解した上界より小さい。§5.4のrank下界は|0>,|+>テンソル積という限定された候補族に対するもの。§6: extentのSOCP双対とfidelity witness、stabilizer alignmentの定義とテンソル積閉性を証明。1–3量子ビット状態のtensor productsでfidelity/extentの乗法性を証明し、大きな一般状態では非乗法性を示す。

**今回の実装への判断:** CCZを直接扱う位相つき古典検証・独立シミュレーションの候補。ランダム化を使わない二次形式指数和サブルーチンは主論文のClifford-overlap計算とも整合する。Cliffordの線形結合は1本の無料Clifford回路ではなく、分解項の共有やrank指数の低下を実Toffoli削減として採点できない。現在の大量のCCXを単純にCCZ magic statesへ置換するrank上界は指数的で、全アドレス＋ANF/HMR位相証明の置き換えを当然に速めるとは限らない。

**留保:** 既知のk項分解のノルム相対推定は、任意回路の確率を多項式時間で相対推定する主張ではない。近似rankによる状態誤差は、稀な出力確率の相対誤差や任意入力に一様なoracle誤差を保証しない。extentはapproximate rankの上界であり常にtightとは限らず、§6.4で小角状態の反例を明示する。§5.4の限定族の下界を任意stabilizer decompositionやBoolean乗算回数へ外挿しない。§5.1の数値探索は非網羅的で一般最適性の証明ではない。全図画像を個別視認・全証明を独立再現したわけではない。

## shallow:22 — L. Kocia, Improved strong simulation of universal quantum circuits, arXiv preprint arXiv:2012.11739 (2020).

**一次資料:** https://arxiv.org/pdf/2012.11739

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 主本文§§I–VIIと参考文献を読了。Appendices A–Fの詳細式は未読。

**内容:** 12-copy magic stateで49項を47項へまとめる構成を示す。single-Pauliの制限されたGauss-sum表現では42項が得られるが、multi-Pauliへの同じ改善は未証明と明記する。これらは構成上界で最小性の証明ではない。

**今回の実装への判断:** 同一項・符号項を構成後にまとめる発想は参考になるが、量子stabilizer和とGF(2)積回路は異なる。0.449を普遍的simulation exponentやJ4回路の下界にしない。[23]の後続改善とも区別する。

## shallow:23 — H. Qassim, H. Pashayan, and D. Gosset, Improved upper bounds on the stabilizer rank of magic states, Quantum 5 , 606 (2021).

**一次資料:** https://arxiv.org/pdf/2106.07740

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 12頁の抽出本文、全証明とAppendix Aを読了。

**内容:** cat-stateの接続でexact stabilizer-rank上界をO(2^{log2(3)m/4})へ改善し、6-copyの6項分解を与える。Clifford/postselectionによる数学的構成で、既存7項の最適性予想を覆す。

**今回の実装への判断:** 局所的な古典検証の表現を減らす可能性がある。postselectionを無料のmagic-state準備として実装費から除外しない。stabilizer rankの改善だけでは実回路Toffoli数を更新できない。

## shallow:24 — Y. Shi, Quantum and classical tradeoffs, Theoretical computer science 344 , 335 (2005).

**一次資料:** https://arxiv.org/pdf/quant-ph/0312213

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 11頁の抽出本文・証明・参考文献を全読。

**内容:** basis-changing gateをquantumnessの尺度として、state-preparationのentropyと必要ゲート数、Grover queryとbasis-changing層の交換を扱う。Toffoliはこの論文ではbasis-preserving演算に含まれる。

**今回の実装への判断:** 多くのToffoliを持つ古典的XOR回路でも基底入力の古典模擬は容易になり得る。Hadamard深さ・entropy下界は今回のToffoli数下界と異なる。浅いmagic深さを直接cost低下とみなさない。

## shallow:25 — A. Y. Kitaev, Quantum measurements and the abelian stabilizer problem, arXiv preprint quant-ph/9511026 (1995).

**一次資料:** https://arxiv.org/pdf/quant-ph/9511026

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 22頁の抽出本文、全章・証明・結論・参考文献まで読了。

**内容:** Abelian stabilizerは群作用の安定化群問題で、stabilizer stateのrankとは別概念。Lemma1は任意ターゲットへのXOR可逆化をcompute-copy-uncomputeで構成し、入力依存garbageがcoherenceを壊す点を説明する。

**今回の実装への判断:** 全32ターゲットビット、scratch消去、測定後位相まで検査する契約に直結する。近似copy/uncompute定理の誤差と、U|0>=|0>を仮定するcontrolled-U構成を、条件確認なしにローダーへ適用しない。

## shallow:26 — D. Gottesman and I. L. Chuang, Demonstrating the viability of universal quantum computation using teleportation and single-qubit operations, Nature 402 , 390 (1999).

**一次資料:** https://arxiv.org/pdf/quant-ph/9908010

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 著者 arXiv quant-ph/9908010v1 全6頁。本文、回路図の説明、Appendix A（cat状態を用いる資源準備）、参考文献。

**内容:** ゲートをBell資源 (I⊗U)|Bell〉へ移し、Bell測定のPauli誤りを U R U† で補正する。Clifford階層の第3層では補正がCliffordになり、資源状態の準備を本体から分けられる。

**今回の実装への判断:** 測定分岐ごとの補正を含めた証明の設計に有用。GVQCCには任意Bell/magic資源の無料供給はなく、資源準備・補助量子ビット・実際の許可演算まで算入しなければ採点改善にならない。

**留保:** arXiv題名 Quantum Teleportation is a Universal Computational Primitive と掲載誌題名は異なる。Appendix Aのfault-tolerant準備を無料の処理としては扱わない。

## shallow:27 — D. Shepherd and M. J. Bremner, Temporally unstructured quantum computation, Proceedings of the Royal Society A: Mathematical, Physical and Engineering Sciences 465 , 1413 (2009).

**一次資料:** https://arxiv.org/pdf/0809.0847

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** arXiv:0809.0847v3全27頁。本文1–5、すべての定理/lemmaと証明、AppendixのTheorem1証明、参考文献。

**内容:** IQPをX積Hamiltonianの可換和で定義し、線形符号/二項matroidの重み列挙から方向バイアスを計算する。Zネットワーク（CNOT/X/対角回転）との変換、graph-state非適応測定への変換を与える。位相関数の方向差分を繰り返すと次数が下がることを利用する古典samplerも提案。

**今回の実装への判断:** CNOTでの可逆な基底変更は、パリティ位相表現や高位/低位アドレス分割の整理に役立つ。可換性で順序を変えられることと、各演算の個数を減らせることは別。Graph変換には|+〉準備・測定・補助線が必要で、現在のKMBへ無費用で移せない。

**留保:** arXiv題名Instantaneous Quantum Computation、掲載題名Temporally unstructured quantum computation。hidden-code検証と古典手法の最適性は当時のconjectureであり、ここで現在も成立と主張しない。

## shallow:28 — M. J. Bremner, R. Jozsa, and D. J. Shepherd, Classical simulation of commuting quantum computations implies collapse of the polynomial hierarchy, Proceedings of the Royal Society A: Mathematical, Physical and Engineering Sciences 467 , 459 (2011).

**一次資料:** https://arxiv.org/pdf/1005.1407

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** arXiv:1005.1407v1全13頁。本文1–4、Theorems1–3と証明、Hadamard gadget、参考文献。

**内容:** post-IQP = post-BQP = PP。IQPの全出力確率を点ごとに1/c〜c、1≤c<√2で古典samplingできればPHが第3層へ崩壊する。postselectionで比を取ると誤差はc²になり、加法誤差では小さい分母が問題になる。O(log n)出力bitだけなら残りを一様に固定して小状態を直接計算し、exact weak samplingが可能。

**今回の実装への判断:** 主論文の少数Pauli/少数出力と全分布の区別の一次根拠。Hadamardを1ancilla+CZ+postselectionへ移すのは複雑性理論の構成で、全測定結果で成功するoracleの合成ではない。

**留保:** PH非崩壊は仮定。1/c≤比≤cの乗法誤差と|estimate−value|≤epsilon|value|の定義は数値範囲が違うので同じ定数として引用しない。

## shallow:29 — M. J. Bremner, A. Montanaro, and D. J. Shepherd, Average-case complexity versus approximate simulation of commuting quantum computations, Physical review letters 117 , 080501 (2016).

**一次資料:** https://arxiv.org/pdf/1504.07999

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** arXiv:1504.07999v2全10頁。本文全体、Appendices A–F（Ising対応、三次gap対応、Hadamard gadget、相対誤差困難性、Stockmeyer、反集中）と全参考文献。

**内容:** ランダムな三次GF(2)多項式gap²または複素温度Ising分配関数の平均時相対近似が#P困難という仮定の下で、IQP分布をl1誤差1/192以内にsamplingできればPH崩壊。反集中は証明し、必要な平均時困難性は仮定として残す。Appendix Dはshiftと反復で相対近似からgapの厳密値を回収する。

**今回の実装への判断:** 加法精度のPauli期待値計算を全分布samplingの容易性と混同しない根拠。三次位相関数の識別や厳密検証の数学的背景にはなるが、特定75語ローダーのToffoli下界・上界を与えるものではない。

**留保:** 1/192は論文が定義したl1ノルム（標準TV距離の1/2係数を付けたものと同じ数値ではない）。平均時困難性を無条件定理としない。

## shallow:30 — D. Bluvstein, S. J. Evered, A. A. Geim, S. H. Li, H. Zhou, T. Manovitz, S. Ebadi, M. Cain, M. Kalinowski, D. Hangleiter, et al. , Logical quantum processor based on reconfigurable atom arrays, Nature 626 , 58 (2024).

**一次資料:** https://arxiv.org/pdf/2312.03982

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** arXiv:2312.03982v1 のPDF全32頁。主本文1–8頁、全参考文献9–11頁、Methods12–22頁、謝辞・著者情報23頁、Extended Data Fig.1–9と全キャプション24–32頁を通読。論理CCZの符号・ゲート図であるFig.5（6頁）は原画像も確認。

**内容:** 中性原子の移動可能な符号ブロックと保存・ゲート・読出し領域を用い、transversal CNOTと相関復号を実験。[[8,3,2]]符号では8物理量子ビットに3論理量子ビットを保持し、8個のT/T†による論理CCZ、S/S†によるCZ、物理置換によるブロック内CNOTを実装。48論理量子ビット・48 CCZのIQP型回路、誤り検出によるXEB改善、2コピーBell測定による純度・Pauli期待値絶対値・magic推定を提示。Methodsはstate preparationの非fault-tolerantな箇所と、postselection・simulation costの仮定を明示する。

**今回の実装への判断:** 符号内の位相式、共有CNOTや置換の扱い、相関復号は構造理解・検証に有用。しかしGVQCCは符号化後の論理ゲートと生存幅を直接数えるため、8物理Tによる論理CCZやエラー検出の採用だけではnative CCZ=1 Toffoli相当を安くしない。サンプリングとPauli推定の精度・postselectionは、任意入力に作用するcoherentなローダーの契約を置き換えない。[31]は本論文の回路に対する改善された古典シミュレーションなので、ここでの将来runtime予測を普遍的下界と解釈しない。

**留保:** 取得したarXiv本文・Methods・追加図は全読。別ファイルのSupplementary Movieは未取得・未視聴。実験数値、全ゲート較正、誤りモデルを独立再現した意味ではない。

## shallow:31 — D. Maslov, S. Bravyi, F. Tripier, A. Maksymov, and J. Latone, Fast classical simulation of harvard/quera iqp circuits, arXiv preprint arXiv:2402.03211 (2024).

**一次資料:** https://arxiv.org/pdf/2402.03211

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** arXiv:2402.03211v1全9頁。本文I–V、Lemmas1–2、Eq.(1)–(4)の導出、実装・性能・限界の議論、参考文献。

**内容:** 三次位相多項式の各項を覆う変数集合Sを固定すると残りは二次式。対象の3色構造では|S|=n/3なので2^{n/3}回のClifford振幅計算に分解できる。固定した赤変数に対して緑青の式はxG·ΓxB+δG·xG+δB·xB。行/列空間条件とGF(2) rank/線形方程式で各項を厳密計算。Gray順序でΓをXOR更新する。

**今回の実装への判断:** 高位アドレスを固定して低位二次構造を整理する手法、および厳密検証の高速化の参考になる。古典的に2^{|S|}個のスライスを列挙できても、coherent loaderでその制御付き回路を安く実装できるとは限らない。既存のbranch差分と基底共有探索と重なる。

**留保:** 48/96量子ビットの性能値は著者の報告で、こちらで再現していない。192量子ビットについては実測ではなく資源見積り。一般の三次多項式に同じn/3の被覆構造があるわけではない。

## shallow:32 — S. A. Fenner, L. J. Fortnow, and S. A. Kurtz, Gap-definable counting classes, Journal of Computer and System Sciences 48 , 116 (1994).

**一次資料:** https://www.cse.sc.edu/~fenner/papers/gaps.pdf

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 著者公開版全33頁。通常のPDF文字抽出が崩れるため全頁をOCRし、その全テキスト（Sections1–10、Appendix A、参考文献）を読んだ。GapP定義と#P−#P等価性の原画像も確認。

**内容:** GapPを非決定性機械の受理経路数−拒否経路数として定義し、GapP=#P−#P=#P−FP=FP−#Pを証明。加減乗算、指数個の和、poly個の積などに閉じる。PP等のgapによる定義、SPPの最小性/lowness、gap-definableクラスの格子構造も扱う。

**今回の実装への判断:** 量子干渉の符号付き和を#Pの非負計数と区別して扱うための複雑性理論の基礎。GapPの閉包性は数値の安価な計算法や小Toffoli回路の構成法ではないため、直接の採点改善策には数えない。

**留保:** 1992年著者原稿にJCSS1994掲載情報が付く。OCRの一部数式には認識誤りが残るため、全式を厳密転写/独立検証したとはしない。根拠として使う定義・主要等価式は原画像で確認。

## shallow:33 — A. Ehrenfeucht and M. Karpinski, The computational complexity of (XOR, AND) counting problems (International Computer Science Inst., 1990).

**一次資料:** https://theory.cs.uni-bonn.de/ftp/reports/cs-reports/1990/8543-CS.pdf

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Bonn著者報告8543-CS、全8頁の本文・定理証明・参考文献をweb全文とPDF抽出で確認。

**内容:** GF(2)上のXOR/AND多項式の解数計算。2次以下では変数変換で対積と線形項に正規化でき、3次では#P完全となる境界を与える。

**今回の実装への判断:** 二次位相和を厳密に計算する根拠として有用。既存のGF(2)二次形式の整理と重なる。位相和の計算容易性から、75語の多出力ローダーの乗算回数やToffoli下界は導けない。

**留保:** 古いPDFの数式抽出には崩れがある。記載定理と証明全体は読んだが、全式の独立再導出はしていない。

## shallow:34 — B. Fefferman, Lecture notes for the 2023 ias/pcmi graduate summer school (2013).

**一次資料:** https://www.ias.edu/sites/default/files/billfefferman-lectures-pcmi-out.pdf / https://www.ias.edu/pcmi/pcmi-2023-gss-lecture-notes-and-problem-sets / https://www.ias.edu/sites/default/files/billfefferman-lectures-pcmi-out_1.pdf

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** IAS/PCMI 2023一次配布スライド On the theory of near-term quantum advantage 全63枚。全文テキストを読み、抽出欠落の34–36枚目は再取得、14枚目の符号付き和の議論は図版も確認。 IAS公式PCMI 2023講義一覧がLecture 1を当該63頁PDF、Lecture 2–5を同内容の別名PDFへ結ぶことも一次ページで照合。

**内容:** 量子回路出力確率の#P困難性、Stockmeyer近似計数とPH崩壊、最悪時から平均時への多項式補間、XEB/QUATH/XQUATH、Pauli経路表現、depolarizing雑音下の高重み経路切捨てを扱う。

**今回の実装への判断:** 加法誤差・相対誤差・全分布の距離・benchmark値が異なる要求であることを整理する一次講義資料。量子samplingを古典的に近似できることやnoise下の切捨ては、無雑音で全入力のoracle一致を要求するKMBのゲート削減根拠にはならない。

**留保:** 主論文の参考文献中の「2023 ... (2013)」には年の不一致がある。IAS公式一覧に掲載されたPCMI 2023資料を読んだ。別添の4頁problem setは本文読了範囲に含めない。

## shallow:35 — P. Selinger, Quantum circuits of t-depth one, Physical Review A—Atomic, Molecular, and Optical Physics 87 , 042302 (2013).

**一次資料:** https://www.mathstat.dal.ca/~selinger/papers/toffoli.pdf / https://arxiv.org/abs/1210.0974

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 著者公開PDF全5頁。本文全体、ToffoliのT-depth 1構成、Theorem 4.1のほぼ古典ゲート集合に関する構成と証明、Theorem 5.1のHTHTHTに対する不可能性、参考文献。

**内容:** 7TのToffoliを4個のclean ancillaでT-depth 1にする。一般には計算基底のBooleanラベルを補助線へ計算し、T位相を並列適用してuncomputeする。任意Clifford+T回路が同様にT-depth 1になるという定理ではない。

**今回の実装への判断:** 主論文Fig3と同じ7T/4ancillaのCCZを実KMBとして独立合成し、8入力すべて位相・ancilla一致を確認。Invsqrt式ではnative CCZ 1に対して7T/4=1.75。Chemistry/DQIの禁止Z_POWにも適合しない。

**留保:** 主論文v1では[34]、v2/掲載版では[35]。T-depthとT-countとToffoli換算費用を混同しない。

## shallow:36 — J. Dehaene and B. De Moor, Clifford group, stabilizer states, and linear and quadratic operations over gf (2), Physical Review A 68 , 042318 (2003).

**一次資料:** https://arxiv.org/pdf/quant-ph/0304125

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** arXiv quant-ph/0304125v1 全9頁。本文I–VI、Theorems 1–6と証明、Appendix Eq.(4)の証明、全参考文献。

**内容:** PauliとCliffordをGF(2)のsymplectic行列＋二次位相で表現する。安定化子状態の振幅はアフィン部分空間に支持され、非零振幅の位相は二次式。CliffordをO(n²)個の1/2量子ビット演算へ構成する。

**今回の実装への判断:** HMR位相追跡、線形回路の等価性、到達可能部分空間での位相を含む厳密検証に利用可能。Clifford数だけが減っても現在のToffoli費用は減らない。

**留保:** magic論文[27]と重複。全本文を読了した共有キャッシュとして利用可。

同一文献: magic:27

## shallow:37 — E. Knill, Fault-tolerant postselected quantum computation: Schemes, arXiv preprint quant-ph/0402171 (2004).

**一次資料:** https://arxiv.org/pdf/quant-ph/0402171

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** arXiv quant-ph/0402171v1全17頁。本文I–XI、回路の全図説明、注記・参考文献。7–8頁の抽出欠落も再読補完。

**内容:** 4qubit error-detecting codeで論理bitとspectator bitを符号化し、purification、Bell teleportation、transversal Clifford、postselectionを連結する。concatしても一定depthを維持する設計と、magic one-qubit状態の注入/蒸留を示す。

**今回の実装への判断:** 既知のspectator状態を利用して検査を省略/追加する考え方は到達部分空間の仕様確認に関係する。一方、postselectionの成功確率と大量の並列資源を落とせないため、低depthだけをKMB費用改善と評価できない。

**留保:** この論文自身が閾値・性能の定量的error analysisは未実施と明記する。成功確率が小さくなりうる理論設計であり、実装可能な低費用oracleを保証する論文ではない。

## shallow:38 — S. Bravyi and A. Kitaev, Universal quantum computation with ideal clifford gates and noisy ancillas, Physical Review A—Atomic, Molecular, and Optical Physics 71 , 022316 (2005).

**一次資料:** https://arxiv.org/pdf/quant-ph/0403025

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** arXiv quant-ph/0403025v2 全15頁。本文I–VII、5→1と15→1蒸留の導出、Appendix A、全参考文献。

**内容:** 理想Clifford、Pauli測定、独立に供給される雑音混合状態ρからmagic状態を蒸留して普遍計算する。T-typeは5qubit code、H-typeは15qubit CSS codeでエラー検出後にpostselectしdecodeする。

**今回の実装への判断:** 符号空間へ制限すると非Pauli測定がPauli測定に一致する仕組みは、到達部分空間の最適化を考える参考になる。ただし蒸留や注入が無料ではなく、既製magic ancillaを認めないKMB実装の直接費用改善にはならない。

**留保:** 同論文のT-typeはBloch(1,1,1)/√3の状態で、現代のπ/8 T状態と命名が違う。現代のT状態は同論文H-typeのClifford同値類。magic論文[1]と重複。

同一文献: magic:1

## shallow:39 — H. J. Garcia-Ramirez, Hybrid Techniques for Simulating Quantum Circuits using the Heisenberg Representation. , Ph.D. thesis, University of Michigan (2014).

**一次資料:** https://deepblue.lib.umich.edu/bitstream/handle/2027.42/107198/hjgarcia_1.pdf / https://deepblue.lib.umich.edu/bitstream/2027.42/107198/1/hjgarcia_1.pdf

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加で Chapter I 冒頭〜§1.6、Chapter II 冒頭・§§2.1–2.2、Chapter III 冒頭・§3.1 全小節を通読。既読201,041文字（表紙・目次・Abstract、§§1.7–1.8、§§2.3–2.5、§§3.2–3.3、Chapters IV–VIII 全文）へ137,121文字を追加。合算で主本文 Chapters I–VIII の全節・本文内の全証明を読解。主本文は文字区間[29497,356596)をすべて覆う。

**内容:** 追加範囲では strong/weak と direct/stateless simulation を分離し、Pauli stabilizer と Clifford conjugation、deterministic/random measurement、Z2 affine support＋quadratic phase、canonical generator 操作、状態の global phase の8乗根、stabilizer 近傍・Gramian による線形依存を確認した。§2.2.3.3 は5ブロック H–C–X–P–CZ の状態準備が |0^n> に限ることを明記し、HPH がこのテンプレートへ同じ行列として移せない例を示す。既読の後半では、複数の符号ベクトルで生成元行列を共有する frames/multiframes、cofactor・coalescing、p-blocking、Pauli 観測量の逆伝播とその項数増大を扱う。

**今回の実装への判断:** 具体的な利用先は古典検証器での生成元共有・位相追跡・小さな Clifford 部分の正規化。各 stabilizer 成分の global phase は線形結合内で相対位相となるため、KMB の HMR 分岐の証明でも捨てられない。|0^n> から同じ状態を作ることと、任意入力に同じ作用をする回路を作ることを区別する本文の条件は今回の oracle に直結する。frames の古典メモリ圧縮や特定入力に対する adder の高速 simulation は実量子回路の CCX 除去にはならない。

**留保:** 主本文完了は抽出テキストの実読を指し、Appendix A の1080状態一覧、末尾参考文献の全一覧、front matter の図表一覧[8130,26564)は未読。図はキャプション・抽出文字を確認したが全ピクセルの個別視認はしていない。本文の式には位相を含むPauli群と位相を除く基底の記法、正規化係数など簡略・不整合な表現があり、証明の独立再現はしていない。5ブロック state synthesis や destabilizer を省いた議論を、任意入力 oracle の等価性の証明へ直接流用しない。

## shallow:40 — S. X. Cui, D. Gottesman, and A. Krishna, Diagonal gates in the clifford hierarchy, Physical Review A 95 , 012329 (2017).

**一次資料:** https://arxiv.org/pdf/1608.06596

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** arXiv:1608.06596v1 全9頁。本文I–VI、Theorems1–3、Lemmas1–4と証明、Corollaries、参考文献。

**内容:** 素数次元quditの対角Clifford階層を、p^m乗根の位相と基底ラベルの多項式で特徴付ける。単項の階層位置は(p−1)(m−1)+degreeで決まる。対角部分は群だが第3層以上の全体は一般に群ではない。

**今回の実装への判断:** 小ブロックの位相多項式の次数と位相精度を分ける整理に有用。qubitのT, CS, CCZはいずれも第3層だが、同じ階層であることから同じ費用・等価なoracle実装とはならない。

**留保:** 分類定理でありゲート数最小化アルゴリズムでもToffoli削減保証でもない。

## shallow:41 — N. Schuch and J. Siewert, Programmable networks for quantum algorithms, Physical review letters 91 , 027902 (2003).

**一次資料:** https://arxiv.org/pdf/quant-ph/0303063

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** arXiv quant-ph/0303063全4頁。本文全体、Eq.(4)周辺の途中抽出欠落を再読して補完、全参考文献。

**内容:** 任意の対角ゲートをWalsh-Hadamard変換した角度とパリティ演算のネットワークで実装。最近接CNSゲートによるGray順序のネットワークを与える。

**今回の実装への判断:** 小さな局所位相関数をパリティ回転へ変換する候補比較に使える。一般のnビット関数では2^n−1個の回転になり、Toffoliを一般的に低減する方法ではない。Invsqrtの既存Walsh探索と範囲が重なる。

**留保:** 回転数、角度精度、実際のZ_POW費用をすべて算入する必要がある。

## shallow:42 — C. Gidney and N. C. Jones, A cccz gate performed with 6 t gates, arXiv preprint arXiv:2106.11513 (2021).

**一次資料:** https://arxiv.org/pdf/2106.11513

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** arXiv:2106.11513全1頁。全文と回路図をPDF画像で確認、参考文献も確認。

**内容:** i^(ab XOR cd)=i^ab i^cd (−1)^abcdという位相関係を用い、相対位相ANDのTを相殺してCCCZを6T＋測定補正で実装する。

**今回の実装への判断:** 仮に全Cliffordを利用できれば6Tは1.5 Toffoli換算。だが図はHで補助線を準備しXの平方根逆を経て測定する。実際のKMBではH/X_SQRTが未対応で、掲載図をそのまま有効候補にできない。

**留保:** Hを含む図を既製magic状態や無料初期化で置換して費用を過少計上しない。全8/16入力などの真理値表一致だけでなくcoherent phaseと測定補正も必要。

## shallow:43 — How can we implement controlled-t gate using cnot and h, s and t gates?, quantumcomputing.stackexchange.com/questions/13132 (2020), [Accessed: Sep 16th, 2024].

**一次資料:** https://api.stackexchange.com/2.3/questions/13132/answers?site=quantumcomputing&filter=withbody / https://api.stackexchange.com/2.3/questions/13132?site=quantumcomputing&filter=withbody / https://quantumcomputing.stackexchange.com/questions/13132/how-can-we-implement-controlled-t-gate-using-cnot-and-h-s-and-t-gates

**読解状態:** 全文テキスト読解・回路画像未取得

**実読範囲:** 一次Q&Aの質問および3回答の本文をすべて読んだ。図の4ファイルは直接CDN取得403、一部web表示が取得可能だが全図の視認は未完了。API JSONを保存。

**内容:** Craig Gidney回答はclean ancillaへANDを計算してTを作用しANDを測定消去するCT構成。別回答は√Tを用いる制御位相分解で、元の指定ゲート集合から外れる。

**今回の実装への判断:** 計算AND＋T＋HMR/CZ補正ならInvsqrtで1+1/4の局所費用として評価できる。これは一般のCT合成の一例で、全回路の幅や後続依存を別に評価する必要がある。

**留保:** Q&A本文は一次の提案そのもの。著者の主張を査読定理扱いしない。√Tがある分解が示されても、補助線を使う別分解が不可能とはいえない。

## shallow:44 — R. Raussendorf, D. E. Browne, and H. J. Briegel, Measurement-based quantum computation on cluster states, Physical review A 68 , 022312 (2003).

**一次資料:** https://arxiv.org/pdf/quant-ph/0301052 / https://arxiv.org/pdf/quant-ph/0301052v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。II Gの全7小節、恒等ゲート、隣接X測定の除去、X/Z/一般Euler回転、H/S、CNOTの相関・byproduct導出を含む20,674文字を追加実読。親のAbstract/I/II A/Dと先の自分のII B/C/E/F/H/I・III–VI読解と合わせ、本文I–VIの全節を読了。先の範囲はroot_reference_supplement_cost.jsonに保存済み。

**内容:** 測定projectorと可換なcluster相関が測定後にも保存されることを用い、入出力のX/Z相関を順に構成する。3-qubit chainはPauli補正付き恒等、片側1辺はHとなる。wire内の隣接2個のX測定は、周辺が空きsiteまたはZ測定という条件下で縮約できるが、結果依存のstabilizer符号を残す。一般回転の適応角は以前のX測定結果によって符号が変わり、Clifford H/Sの場合はPauli測定だけで同時実行できる。CNOTは4種類のPauli共役像と全測定結果の符号を照合して示す。

**今回の実装への判断:** パリティや基底写像だけでなく、測定結果から生じる符号と後続ゲートへの伝播まで残すことが必要。隣接測定の削除を任意の作業ビットの無料消去へ一般化しない。以前に整理した7T/幅の費用判断は変わらない。

**留保:** Appendix A（cluster decomposition）は未読。全図の原画像を個別視認・全恒等式を独立に実装検証したわけではない。本文内の帰納・相関証明は読んだが、読了と独立証明を区別する。

## shallow:45 — S. Aaronson, Quantum computing, postselection, and probabilistic polynomial-time, Proceedings of the Royal Society A: Mathematical, Physical and Engineering Sciences 461 , 3473 (2005).

**一次資料:** https://www.scottaaronson.com/papers/pp.pdf

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 著者公開PDF全9頁。PostBQP=PP の証明、閉包性、関連する非線形・postselection議論まで。

**内容:** PostBQP=PP を示し、確率が指数的に小さい非零分岐でも条件付けできる計算モデルの強さを特徴づける。

**今回の実装への判断:** 望ましい測定結果だけを残すことと、全測定分岐を補正して同じ coherent oracle を得ることを混同しないための根拠。

## shallow:46 — F. Arute, K. Arya, R. Babbush, D. Bacon, J. C. Bardin, R. Barends, R. Biswas, S. Boixo, F. G. Brandao, D. A. Buell, et al. , Quantum supremacy using a programmable superconducting processor, Nature 574 , 505 (2019).

**一次資料:** https://www.nature.com/articles/s41586-019-1666-5

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 出版社の本文 Main から The future まで。classical computational cost・digital error model・図説明を含む。別ファイルの Supplementary Information は未読。

**内容:** 53量子ビットの超伝導プロセッサで random circuit sampling と XEB を実施。古典費用は2019年時点のアルゴリズム・計算機に対する外挿である。

**今回の実装への判断:** XEB とハードウェア忠実度は全入力の厳密一致証明ではない。歴史的な古典時間見積もりを現在の性能や論理ゲート費用に流用しない。

## shallow:47 — M.-H. Yung and B. Cheng, Anti-forging quantum data: Cryptographic verification of quantum computational power, arXiv preprint arXiv:2005.01510 (2020).

**一次資料:** https://arxiv.org/html/2005.01510

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** 本文 I–III と Appendices A–C。IQP 相関推定、secret strings、GF(2) scrambling、乱択解析を含む抽出全文。

**内容:** IQP の秘密相関に基づく認証案。theta=pi/8 では Pauli 相関計算が Clifford に帰着し、一般角には加法誤差の推定を使う。厳密な安全性証明は未完と明記される。

**今回の実装への判断:** GF(2) 基底変換に伴う秘密ベクトルの逆変換、位相相関の検査に参考。サンプリング認証を全アドレス・任意標的・位相の一致の代用にはしない。

## shallow:48 — S. Bravyi, D. Gosset, and Y. Liu, How to simulate quantum measurement without computing marginals, Physical Review Letters 128 , 220503 (2022).

**一次資料:** https://arxiv.org/pdf/2112.08499 / https://arxiv.org/html/2112.08499v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。IおよびIIの全文、IIのDirichlet-form混合時間証明、Appendix A（A.1を含む）・D・Eの全証明を実読。Iは親既読分も再確認し、振幅問い合わせの意味と対角gateの扱いを確認した。親のAbstract/Introduction/Algorithms 1–2既読分と合わせ主要本文はすべて確認。Appendix Bの数値実験詳細、Appendix Cのsurface-code MBQC・#P-hard marginalの長い証明は今回未通読（親はB冒頭既読）。全82,989文字を読了したという意味ではない。

**内容:** m個のk-local unitaryからなる回路の出力分布を、各prefix回路の振幅を合計≤m 2^k回問い合わせてexact samplingする。現サンプルのgate作用外bitを固定し、作用するbitだけ更新する。局所unitaryは作用外marginalを保つので帰納的に正しい。CNOT等の基底置換はサンプルを直接更新し、対角gateではその時点の更新を省ける。後のprefix振幅には以前の対角gateの位相を含める必要がある。中間測定・古典制御への拡張では、測定済みqubitに後続gateが作用しないというモデル化を使う。一般のkで振幅計算が無料という主張ではなく、強シミュレーションからsamplingへの還元である。

**今回の実装への判断:** 古典的な独立検証で、振幅計算がmarginal計算より安い場合にsampling費用を下げる候補。exact stabilizer-rank分解ではrankへの依存を二乗から一次へ改善するが、rank自体はnon-Clifford数に対して指数的に大きくなり得る。全アドレスのloader一致や任意ターゲットのANF・HMR位相証明を、有限回のoutput samplingだけで置き換える根拠にはならない。対角gateで古典sample更新を省けることを、KMBから位相gateを削除できると解釈してはいけない。

**留保:** 49-qubit depth16 tensor-network比較のFLOP数は実縮約の実行時間ではなくCoTenGraによる推定と本文に明記する。planar surface-code stateの任意測定順samplingと2D cluster stateの普遍MBQCは別のresource state。Appendix Cの詳細証明は未読なので独立検証済みとはしない。ground-state MCMCの多項式性は1/γ・s・振幅比計算の費用などの条件付きであり、任意Hamiltonianを効率よくsamplingできる定理ではない。

## shallow:49 — C.-Y. Lai and H.-C. Cheng, Learning quantum circuits of some t gates, IEEE Transactions on Information Theory 68 , 3951 (2022).

**一次資料:** https://arxiv.org/pdf/2106.12524 / https://arxiv.org/html/2106.12524v3

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。表題・Abstract・I–VI・Acknowledgementまで本文全体を実読。II–Vの全証明、Algorithms 1/2、関連する全Lemma、Theorems 9/18、Corollary 19、Examples 1–9を含む。参考文献表の再読はしていない。図の画像は個別に開いておらず、本文・table・captionで読める範囲。既読だった親のI/VI等も再確認した。

**内容:** Clifford学習ではU|0^n>とU|+^n>のBell samplingからstabilizer基底を求め、さらに単一bitを変えた基底入力やX基底入力で生成子のラベルと符号を特定し、Clifford synthesisする。Algorithm 1/Theorem 9は2n²+10n+4 query、O(n³)時間、成功確率≥1−2^{-n+1}。T-depth1ではC2 T^v C1、Tのsupport上でC1|0^n>のX-rankがfullである条件を要求する。3^kの符号付きstabilizer pseudomixtureの代わりにn−k isotropic生成子と2k primary symplectic生成子の構造を利用する。Bell samplingでそのspanを求め、Pauli測定の確率1、(2+√2)/4、(1+2^{-m/2})/2、1/2を区別してprimary生成子を選ぶ。Algorithm 2が掲げるquery/時間はO(3^k n)/O(n³+3^k n)で、T-depth1という条件だけで多項式にはならずk=O(log n)が必要。

**今回の実装への判断:** state preparationの学習と、未知入力にcoherentに作用するoracleの合成を区別するために有用。今回の既知ソースKMBにはブラックボックス量子query学習をそのまま行う必要はない。T-depth低下やstabilizer生成子の数の減少を、実Toffoli数の減少として採点できない。学習したU|0^n>を再準備できることだけでは、提出loaderやinvsqrtの全入力作用・相対位相・測定補正の一致を保証しない。

**補完読解で確認した点:** 厳密な限定: arXiv v3 Algorithm 2の印刷された手順(1)–(7)が使うデータはU|0^n>のcopiesである一方、Theorem 18の末尾には固定した同じhat Uについて全vへの一致が記される。この強い量化は、そのデータだけからは同定できない。U=(T⊗T)(H⊗H)、V=U CNOT_{1→2}は両方T-depth1/full T-rank2でU|00>=V|00>だが、U|10>とV|10>は直交する。独立4×4行列チェックを保存した。各vごとの再学習や他の入力・U†への追加queryを使う別手続きはこの反例の対象外。本文全体が誤りであるという結論ではなく、今回の任意入力oracle置換の根拠としてこの強い読みに依存しない。

**留保:** 全計算基底について出力状態をphaseを捨てて学習しても、基底間のrelative phaseは未確定。別の簡単な例W=U(Z⊗I)では各基底の出力rayは同じでも|+0>入力の出力は直交する。3^kのpseudomixtureは負の係数を含み、物理的な確率混合や無料な直交枝としては扱わない。noisy circuit学習のLPNへの関連は計算量仮定に依存し、実証された一般不可能性ではない。原論文の全定理を独立に検証したわけではない。

## shallow:50 — S. Grewal, V. Iyer, W. Kretschmer, and D. Liang, Low-stabilizer-complexity quantum states are not pseudorandom, arXiv preprint arXiv:2209.14530 (2022).

**一次資料:** https://arxiv.org/pdf/2209.14530 / https://arxiv.org/html/2209.14530v1

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加読解: 2 Preliminaries (complete); 3 Certificate of Low Stabilizer Complexity, including all proofs (complete); 4 Algorithm and Sample Complexity Analysis, including all proofs (complete); 5 Open Problems (complete); Acknowledgments。未読: Appendix A (state-preparation-unitary access); Appendix B (tightness); Reference list

**内容:** 安定化子忠実度が無視できない状態を Haar random と区別する Bell-difference-sampling 法を与え、擬似乱数状態の non-Clifford 資源下界を導く。

**今回の実装への判断:** 検証に使うなら状態の統計的診断であり、全アドレス・任意ターゲット・HMR相対位相の厳密同値検証には置き換えない。6コピー測定を128Q回路の無料操作と扱わない。

**補完読解で確認した点:** Algorithm 1は4コピーのBell difference samplingと追加2コピーのPauli測定を各反復で使う。未知pure stateがHaarまたはstabilizer fidelity≥1/kというpromiseの下で区別する手順である。 / Theorem 4.1のv1条件はn≥33、k≤(4/5)2^(n/12)。標本数O(k^12 log(1/δ))、時間O(n k^12 log(1/δ))で、有限失敗確率とHaar ensembleに関する平均を伴う。 / Corollary 4.3は擬似乱数状態ensembleに必要なT数ω(log n)を導く。固定した決定的なtruth tableや任意入力unitaryに対する数値下界ではない。 / Section 5は低stabilizer rankとfidelityの関係、学習、より強いT下界を未解決問題として区別する。低extent、低rank、低実ゲート数を同一視できない。

## shallow:51 — S. Grewal, V. Iyer, W. Kretschmer, and D. Liang, Efficient learning of quantum states prepared with few non-clifford gates, arXiv preprint arXiv:2305.13409 (2023).

**一次資料:** https://arxiv.org/pdf/2305.13409 / https://arxiv.org/html/2305.13409v5

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加読解: 2–10 complete, including all extracted proofs, algorithms 1–4, and open problems; Acknowledgments。未読: Appendix A (one-round adaptivity); Appendix B (mixed states); Reference list

**内容:** 少数 non-Clifford ゲートで準備した状態を、stabilizer dimension と Bell/single-copy measurements を用いて poly(n,2^t,1/epsilon) の資源で学習する。

**今回の実装への判断:** 状態記述の圧縮をToffoli数の改善と扱えない理由が本文自身に明示されている。任意32ターゲットは既知の|0>や観測済みbasis stateに置き換えられず、位相を捨てたunsigned Pauli groupだけではcontrolled演算の厳密監査が足りない。

**補完読解で確認した点:** 一般single-qubit non-Clifford t個でstabilizer dimension≥n−2t。論文後半のn−tはstabilizer dimensionのpromiseであり、一般gate数のtと無条件に一致しない。 / Lemma 3.2はisotropic subspaceをPauli Z標準形へ写すCliffordをH・S・CNOTで構成する。古典的な行操作はbasis表現の変更であって、実回路の非Clifford積を無料に消す操作ではない。 / Algorithms 2–4は大きなPauli probability massをもつ部分空間を学習し、C|ψ>を少数qubit状態と既知basis stateに近似分離してtomographyする。測定によるpostselection、state trace-distance誤差ε、失敗率δを伴う。 / Bell measurements版の部分空間学習はO(n/ε²)標本だが、残ったt-qubit状態の一般tomographyにはpoly(2^t)の資源が残る。Single-copy版はrandom Cliffordを使い2^tにも依存する。 / Section 10は本手法がproper learnerではないと明記する。少数non-Cliffordで準備された状態を学習できても、その少数ゲート数を保った準備回路の効率的合成はQuestion 10.1として未解決である。 / Section 3の行列図と証明の一部は一次HTML抽出で文字が結合している。抽出された全文は読んだが、全行列図の別PDF照合や全式の独立再証明はしていない。

## shallow:52 — S. Grewal, V. Iyer, W. Kretschmer, and D. Liang, Improved stabilizer estimation via bell difference sampling, in Proceedings of the 56th Annual ACM Symposium on Theory of Computing (2024) pp. 1352–1363.

**一次資料:** https://arxiv.org/pdf/2304.13915 / https://arxiv.org/html/2304.13915v3

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加読解: 1–8 complete, including all extracted proofs and algorithms 1–4; Acknowledgments。未読: Appendix A (squared Weyl expectation estimation); Reference list

**内容:** Bell difference sampling による stabilizer fidelity 推定を改善し、擬似乱数状態に必要な T/non-Clifford ゲート数の下界を強める。

**今回の実装への判断:** 候補の構造分析の道具にはなるが、J=4でL≤4170を証明・達成する結果ではない。近似fidelityと統計的promise判定を、厳密なtruth-table/HMR同値検証へ読み替えない。

**補完読解で確認した点:** 擬似乱数ensembleには一般single-qubit non-Clifford≥n/2、diagonal non-Clifford/Tなら≥nが必要という下界。根拠はBell difference sampleが張るPauli部分空間の次元で、任意の固定oracleのgate最適化下界ではない。 / Algorithm 2の最近傍stabilizer近似は標本数こそO((n+log(1/δ))/(ε²τ^4))だが、maximal clique列挙と各stabilizer basisの2^n候補を調べ、時間はexp(O((n+log(1/δ))/τ^4))/ε²。標本効率と計算時間効率を混同しない。 / Algorithm 3がpoly-timeになるbounded-distance条件はfidelity>cos²(π/8)≈0.8536に正のmargin γがある場合で、この条件はunique closest stabilizerを保証する。元の状態をそのstabilizerに物理的に置換してよいという意味ではない。 / Tolerant testerは全ての二閾値で使えるわけではなく、γ=α1^6−(3α2+1)/4>0というgap条件が必要。Weyl expectationの二乗は符号・相対位相の完全な情報ではない。 / 一般の近いstabilizerを求める方法やmatching-pursuitと組み合わせる応用は、classical simulation用の分解探索であり、実ゲートの削減とは目的関数が異なる。

## shallow:53 — L. Leone, S. F. Oliviero, and A. Hamma, Learning t-doped stabilizer states, Quantum 8 , 1361 (2024a).

**一次資料:** https://arxiv.org/pdf/2305.15398 / https://arxiv.org/html/2305.15398v6

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加読解: II Algebraic structure (complete); III Learning from characteristic-distribution samples (complete); IV Sampling (complete); V Learning without conjugate-state access (complete); VI Concurrent work (complete); VII Conclusions (complete); Acknowledgments。未読: Appendices A–D; Reference list

**内容:** t-doped stabilizer state の Pauli characteristic distribution と有限解像度を利用して poly(n,2^t) で厳密に学習する。学習した表現から効率的な準備回路を合成する問題は残る。

**今回の実装への判断:** 固定初期状態のtomographic descriptionを得る結果であり、任意アドレス・任意32ターゲットに同じunitary/XOR作用をする安価な回路を自動合成する定理ではない。測定標本数やstabilizer nullityを実Toffoli数へ換算しない。

**補完読解で確認した点:** II–IIIのfinite resolutionによるexact learningはTゲート限定。一般O(1)-local non-Clifford gateに対する代数的分解は扱うが、同じ離散間隔とexact learningの保証は成立しないと明記する。 / Stabilizer groupとbad-generatorのcoset分解を学ぶ。m≥n−t、bad-generator数k≤4^t−1で、poly(n,2^t)はt=O(log n)のときにpoly(n)。各測定の有限標本による失敗確率は残る。 / IVの直接Bell samplingは状態とその複素共役へのquery accessを使う。Vは同じ状態の2コピーへBell測定を行い、その2回のPauli標本の積を検査する別手順で、複素共役を無料の物理演算と仮定していない。 / Vは学習したstabilizerからClifford diagonalizerを構成して、残った少数qubitの状態をtomographyする。VIIは学習した表現からClifford+T準備回路を合成する問題をopen questionとして挙げる。

## shallow:54 — D. Hangleiter and M. J. Gullans, Bell sampling from quantum circuits, Physical Review Letters 133 , 020601 (2024).

**一次資料:** https://arxiv.org/pdf/2306.00083 / https://arxiv.org/html/2306.00083v5

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加読解: Bell samples as classical circuit shadows (complete); Depth test (complete); Magic test and Clifford+T learning (complete); Error Detection and Correction (complete); Discussion and outlook (complete)。未読: Supplementary Material S1–S5; Acknowledgments and reference lists

**内容:** 同じ状態の2コピーへ transversal Bell measurements を行い、回路の忠実度・深さ・magic を推定する。Bell 分布自体の計算困難性も分析する。

**今回の実装への判断:** 独立の統計的診断としては参考になるが、全1232アドレスとHMR枝の相対位相の厳密検証の代わりにはしない。二倍のqubit使用や追加のH・CNOT・測定費用も固定128Qの外に出せない。

**補完読解で確認した点:** Purityからfidelityを推定する主張にはlocal circuit-level Pauli noise、平均を取る回路ensemble、noiseless Bell measurementという条件がある。測定noiseの補正にはi.i.d.条件を追加する。任意の同じcoherent errorを2コピーに掛けた場合には対応が壊れると本文にある。 / Depth testは指定されたgate architectureの境界をまたぐgate数とsubsystem entropyから深さをlower-boundする。今回の自由配置回路のToffoli数の下界とは違う。 / Magic testはO(n/epsilon)標本で近い状態のstabilizer nullityを推定し、t-qubit部分に追加tomographyを行う。推定値が元の状態のexact T-countや最適回路費用を直接決めるわけではない。 / Antisymmetric Bell outcomeの破棄やvirtual-distillation比による誤差抑制は、測定分布・期待値の処理である。二つのコピーと測定を使い、単一のcoherent oracleを保つuncompute手順ではない。 / 後半のdepth/magic testはpurityが1に近い設定に移っており、noise-robustな一般版はoutlookに残されている。

## shallow:55 — S. F. Oliviero, L. Leone, S. Lloyd, and A. Hamma, Unscrambling quantum information with clifford decoders, Physical Review Letters 132 , 080402 (2024).

**一次資料:** https://arxiv.org/pdf/2212.11337

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** letter の抽出本文全体、全節・数式・図説明。外部Supplemental Materialは未読。一般化の詳証は参考文献56側。

**内容:** tが制限された quasichaotic scrambler から指定部分系の情報を Clifford decoder で回復する。学習費用や成功率・忠実度は n,t とアクセス領域に依存する。

**今回の実装への判断:** 部分系の復号とユニタリ全体の逆演算は異なる。Toffoliを全てCliffordへ置換できるという結果ではない。

## shallow:56 — L. Leone, S. F. Oliviero, S. Lloyd, and A. Hamma, Learning efficient decoders for quasichaotic quantum scramblers, Physical Review A 109 , 022429 (2024b).

**一次資料:** https://arxiv.org/pdf/2212.11338 / https://arxiv.org/html/2212.11338v4

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加読解: Metadata and abstract; II–VI complete, including all extracted main-text proofs, technical definitions/examples, CC algorithm, numerical conditions, conclusions and acknowledgments。未読: Appendix A (notation); Appendix B (subroutines); Appendix C (proof of Theorem 1); Appendix D (finite resolution lemma); Reference list

**内容:** t-doped Clifford unitary の非Clifford部分を高々t量子ビットへ集約する構造を利用し、quasichaotic scrambler の効率的decoderを学習する。

**今回の実装への判断:** 有限幅の非Clifford核を探す発想と、共役像の符号を別途追う設計は参考になる。しかし部分系復号には破棄する自由度があり、任意入力のXOR loaderとclean ancillaの全体一致を保つ無料Clifford置換にはならない。H/Sを含む全Clifford操作も公式gate alphabetと照合が必要。

**補完読解で確認した点:** Theorem 1はscrambler U_tに対する部分情報の復号である。EPR pair、部分系Dと既存のB′へのアクセス、追加EPR pair、DD′へのBell projectionを使い、投影成功確率と条件付きfidelityを区別する必要がある。 / 復号器生成はG_D上のPauli共役作用を符号まで合わせ、残るtableau自由度をrandom completionする。成功率の下界1−2^{−(2|C|−t)}とfidelity近似1/(1+2^{2|A|+t−2|D|})は異なる条件であり、両方を同時に満たす余白が必要。 / IV.3 Remark T4とVIは、Dを全系へ拡張するとunitary fidelityに戻り、非Clifford U_tとClifford Vのfidelityは1未満になると明記する。部分系復号を全unitary置換に使えない。 / V.2のcompression theoremはU_tをCliffordで挟んだ高々t-qubitの非Clifford核へ写すが、核には最大t個のTが残る。O(n²+t³)はH/CNOT/Tなどの全ゲート数の漸近上界で、Toffoli数が減ったという結果ではない。 / V.2はT gatesを仮定して|G(U_t)|≥2^(2n−t)などを導く。一般single-qubit非Cliffordへの拡張を脚注は述べるが、同じtの定数やfinite-resolution保証を無条件に移さない。Corollary 2のstate diagonalizerは入力のstabilizer stateに依存すると証明末尾が明記する。 / CC algorithmのworst-case資源は本文では時間O(n^5 2^(6t))、query O(n^4 2^(6t))。t=O(log n)なら多項式、tがnに比例すると指数的。実験はn=8、100 realizations、t=0…6の特定構造であり一般的な実用速度保証ではない。 / IIIの学習困難性はquery modelや既存の仮定付き結果を区別する。Metropolis探索の失敗やbest-known simulatorの指数費用は、全アルゴリズムに対する無条件下界ではない。 / V.1のEq.(31)にはHTML抽出由来の描画命令が混入する。tableauの後続説明とphase bit更新は読んだが、その図式の独立PDF照合はしていない。

## shallow:57 — P. Niroula, C. D. White, Q. Wang, S. Johri, D. Zhu, C. Monroe, C. Noel, and M. J. Gullans, Phase transition in magic with random quantum circuits, arXiv preprint arXiv:2304.10481 (2023).

**一次資料:** https://arxiv.org/pdf/2304.10481 / https://arxiv.org/html/2304.10481v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加読解: I Model (complete); II Quantifying magic (complete); III Vanishing rate (complete); IV Constant rate (complete); V Discussion (complete); Acknowledgments/data availability/disclaimer; Supplement A Basis-minimized entropy; Supplement B Syndrome distribution; Supplement C Decoder breakdown。未読: Supplement D–M; Reference list

**内容:** Clifford encoding、coherent single-qubit rotations、decode、syndrome measurements という模型で、回転強度や符号率に対する magic の相転移を調べる。

**今回の実装への判断:** 測定後magicが小さいというだけでは、古い中間値を自由に測定・消去できない。HMRで正しいbyproduct correctionを全入力に適用する具体的恒等式が必要。最適Toffoli数やJ=4境界をこの相転移から導けない。

**補完読解で確認した点:** 模型は|0>からClifford encode、全qubitへのcoherent Z rotation、inverse decode、syndrome measurementを行う。得たmagicは条件付き論理状態の性質で、元の入力に対して同じchannelを保つ変換ではない。 / Vanishing-rateの解析にはsyndromeごとのerror数の仮定がある。Constant-rateのcritical pointと指数は有限サイズfitとscaling hypothesisに敏感で、SSREとconditional entropyの転移が一致するか本文は結論していない。 / 実験のmagic推定はsyndrome classへのgrouping、tomography後の最大固有状態への射影、理想分布のsupportへの投影等の古典postprocessingを使う。これを物理回路のexact動作保証と読まない。 / Supplement Aが示すbasis-minimized entropyの性質はpure stateでのfaithfulness、Clifford不変性、subadditivity。任意の許可stabilizer操作に対する全ての資源単調性まで証明したとは扱わない。 / Supplement Cは小さい測定entropyでも情報回復を保証しないと明記する。Syndrome measurementが初期状態とは異なるpure stabilizer stateへ射影しうるためである。Syndromeごとにminimizeした平均と、全syndromeで共通basisをminimizeした値も区別する。

## shallow:58 — M. Bejan, C. McLauchlan, and B. Béri, Dynamical magic transitions in monitored clifford+ t circuits, PRX Quantum 5 , 030332 (2024).

**一次資料:** https://arxiv.org/pdf/2312.00132 / https://arxiv.org/html/2312.00132v3

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加読解: Table of contents, title, authors and abstract; I–VII complete, including all subsections, Theorem 1 proof, Theorem 2 statement, equations and extracted figure captions; Acknowledgments。未読: Appendices A–H (A–D and E.1–part of E.3.2 are cached but not read as substantive supplementary review); Appendix E.3.2 remainder, E.4 and F–H are absent from this truncated cache; Reference list is absent from this cache

**内容:** 監視された Clifford+T 回路の stabilizer purification と magic fragmentation を解析。簡略模型の定理と、より一般の模型の数値結果を分けている。

**今回の実装への判断:** 測定依存を含むPauli supportグラフの分解は検証用シミュレーターの設計に参考になる。ただし入力を固定すること、magic-state準備を費用外に置くこと、Pauli符号を捨てることは現在のexact XOR loaderの要件を満たさない。全1232アドレス・任意32ターゲット・HMR枝位相を保つ具体的回路と実CCX計数が別途必要であり、本論文から削減量は得ていない。

**補完読解で確認した点:** 対象はランダムなClifford+T回路に中間Z測定を含む模型の古典シミュレーション。PBCへの変換はmagic ancilla、Pauli測定、結果に応じたClifford更新を使う。既知の安定化子入力と出力分布の再現が基礎で、任意入力に対する同じunitaryをCliffordだけで合成する定理ではない。 / III.2のCPX_PBCは、magic-state registerで重なる測定supportをまとめたブロックの大きさt_iに対するΣ_i 2^t_iというruntime proxy。多項式係数や指数内定数を省き、最終出力に関係するブロックだけを数える。実行ゲート数でも、すべての古典アルゴリズムに対する無条件下界でもない。 / VIIはCPX_PBCがCliffordで増加し得るためmagic monotoneではないこと、測定結果でPauliの符号が変わってもsupport構造とproxyは変わらないことを明記する。この符号を省く指標はHMR枝の相対位相検証に使えない。 / V.1の単一Tゲートを消す測定は、動的stabilizer codeに符号化された論理qubitのPauliを測る。Theorem 1は既知stabilizer入力について、元回路と対応PBCの出力がstabilizerであることの同値を示す。SPからmagic fragmentationへの証明は、各ブロックにO(1)個のTを置き、その終点がstabilizerという簡略模型の仮定を使う。一般回路への形式的拡張はVIIで未解決とする。 / V.3のpurification確率は、測定Pauliを所定の生成元集合から一様に選ぶ近似、共通のγや固定幅wなどを用いる。Theorem 2の生成元数とentanglementの関係の証明はAppendix Dに置かれ、今回未読。確率・時間scalingを個々の固定ローダーへの厳密保証へ移さない。 / 固定qD=O(1)の数値転移p_c=0.159±0.001と、固定qでの振舞いを区別する。V.4.2の脚注は極めて小さいqのeasy phaseを排除できないと記し、本文のhard phaseの議論も一般最悪時下界として扱えない。 / V.5は同時に未purifyのmagicがO(log n)個に留まれば、poly(n)個のstabilizer状態の重ね合わせとしてexact stateを追跡し、strong/weak simulationを効率化できると述べる。これは状態表現の古典計算費用であり、元のT/Toffoli実命令が減ったことを意味しない。 / VIのT-correlated monitoringではT直後のZ測定を増やすと、体積則entanglementのままシミュレーションが容易になる。perfect monitoringは各Tのmagicをすぐ射影で除くが、その測定を任意入力のoracleに挿入してよいことを保証しない。 / VIIはvon Neumann entropyによるarea lawからの近似MPS simulationと、Hartley entropyのarea lawを使うexact TN simulationを区別する。また独立研究とのqD一定の場合の転移の相違をNote addedで明記している。数値critical値を普遍的な回路定数として流用しない。

## shallow:59 — X. Turkeshi, E. Tirrito, and P. Sierant, Magic spreading in random quantum circuits (2024), arXiv:2407.03929 [quant-ph] .

**一次資料:** https://arxiv.org/pdf/2407.03929 / https://arxiv.org/html/2407.03929v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加読解: Metadata, abstract and unnumbered introduction; I–VIII complete, including Methods VIII.1.1, VIII.1.2, VIII.2, all extracted equations and captions; Acknowledgments opening。未読: Supplemental Material sections 1–6; Reference list; Remaining acknowledgment/funding/data statements after character 67418

**内容:** ランダム回路の magic spreading を generalized stabilizer entropy、replica/tensor-network法で解析し、entanglement spreading と異なる時空間尺度を示す。

**今回の実装への判断:** GSEやentanglementを探索の指標として使うとしても、低い値を厳密な回路削減証明と扱わない。測定によるmagic低下からHMR消去の正しさは導けず、実CCXと全入力・位相の別検証が必要。

**補完読解で確認した点:** 解析対象は|0>^Nからの1次元brick-wall Haar-random two-qudit circuit。一般化stabilizer entropyのensemble平均の成長であり、特定回路のT/Toffoli最小数を与えない。 / Section IはClifford不変性・faithfulness・additivityと測定下の単調性を区別し、任意GSEのPauli測定に対する単調性は保証されずqutrit反例があると明記する。SRE部分族やodd-prime manaの主張を全GSEへ一般化しない。 / 平均の対数であるannealed値と対数の平均であるquenched値を区別する。Methodsでは差が固定時刻にN比例、係数が時間とともに指数減衰するという数値scalingを調べており、両者を厳密に同一とする恒等式ではない。 / Replica/Weingarten法は平均した非unitary transfer tensorのMPS contractionを行う。qubitで有効local dimension24から14へ減らすのはClifford commutantの表現空間であり、75語truth tableの積数削減ではない。 / GSE飽和までのt∝log Nは固定の小さなtoleranceでΔM≈aN exp(−αt)という数値結果に基づく。一般のchaotic Hamiltonianへの拡張はVIでconjectureと記される。 / 大規模1024-quditの結果はbond-dimension convergenceを確認したensemble量のtensor-network計算。任意1回路の全振幅のexact simulationではない。manaはN≤14に留まり、log N飽和時間の明確な実証には不十分とMethods自身が述べる。 / Section IIIのtensor-network図はHTML抽出でSVG/TeX描画命令になる。周囲の式と説明は読んだが、全図の視認・数値再現やSupplementの証明検証はしていない。

## shallow:60 — G. E. Fux, B. Béri, R. Fazio, and E. Tirrito, Disentangling unitary dynamics with classically simulable quantum circuits, arXiv preprint arXiv:2410.09001 (2024).

**一次資料:** https://arxiv.org/pdf/2410.09001 / https://arxiv.org/html/2410.09001v3

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加読解: Results including Theorem 1 and proof (complete); Consequences for Hamiltonian dynamics; Applications; Discussion and conclusion; Acknowledgments; End Matter: Hamiltonian dynamics and matchgate disentangling (complete)。未読: Reference list

**内容:** Clifford符号化された状態の未使用|0>自由度へ Pauli rotation のmagicを移し、entanglementを抑えた表現を構成する。magicそのものを消去する操作ではない。

**今回の実装への判断:** 状態表現やsampling幅の圧縮と、実命令のCCX削減は別。固定した任意32ターゲットを|0>のfree qubitと扱えず、追加magic preparationやCliffordのH/Sを公式gate alphabetの外へ無料に置けない。

**補完読解で確認した点:** Theorem 1はC(|phi>⊗|0>^(N−k))という符号化されたstateと、logical operatorではないPauli Pに適用する。Pがstabilizerなら位相のみ、anticommutingなら未使用|0>にmagicを移す。任意入力の全Hilbert空間上で同じoperatorという主張ではない。 / 非Clifford rotationごとにfree qubitを使うか、残ったMPSのbond dimensionを最大2倍にする。Typicalなt*≈N−1.607は深いrandom Cliffordの確率模型であり、与えられた語表回路に対する無条件保証ではない。 / Greedy sweepは二qubit Cliffordのlocal-operation quotient 20候補を調べる。実験で少数sweepが有効という結果と、常に最適disentanglerを見つける保証を区別する。 / Applicationsの量子回路圧縮はsampling taskであり、free-qubit測定のランダムな結果とClifford更新を用いる。Pauli expectationがpoly-timeでも、全qubitのjoint samplingは一般に指数的という違いを本文と結論が明記する。 / End Matterでは一般非可積分Ising dynamicsのmagic/entanglementを十分には除去できなかった。Matchgate版は特定の逆時間発展による試算であり、一般最適化手順はfuture work。

## shallow:61 — Z. Liu and B. K. Clark, Classical simulability of clifford+ t circuits with clifford-augmented matrix product states, arXiv preprint arXiv:2412.17209 (2024).

**一次資料:** https://arxiv.org/pdf/2412.17209 / https://arxiv.org/html/2412.17209v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加読解: II Background; III.1–III.4 including all proofs and Algorithms 1–2; IV.1–IV.2 OBD and comparison; V.1–V.2 numerical results; VI.1–VI.3 probability/sampling/amplitude/entropy and Algorithms 3–4; VII Conclusions; Acknowledgments; Appendix B complete, including Algorithm 5 and Proposition 1 proof; Appendix C complete counterexample。未読: Appendix A; Appendices D–I; Reference list

**内容:** Clifford-augmented MPS において自由|0>量子ビットと Pauli string の構造を用いて magic とentanglementを分離する。GF(2)行列のrankはdisentangle可能性を分類する。

**今回の実装への判断:** Pauli窓の状態シミュレーションや位相追跡の設計には参考になるが、75語表のjoint XOR loaderの実CCXを直接減らす結果ではない。現在のBoolean truth-table rankとは対象も最適化方向も異なる。

**補完読解で確認した点:** OFDは未使用のproduct |0> qubitにPauli stringのX/Y成分が作用するとき、同じqubitをcontrolとするcontrolled-Pauli列でmagicを局所化する。|0>という入力制約を外した任意ターゲットにはそのまま適用できない。 / III.3のGF(2)行列はtwisted Pauliを{I,Z}→0、{X,Y}→1で写したt×N行列。Rank rはOFDで処理できる独立方向の数で、未処理数t−rがbond dimensionの上界に入る。ここでは高rankが有利であり、truth-table bilinear rank低減とは別の目的である。 / 2^(t−r)はbond dimensionの上界であって厳密値でもToffoli下界でもない。単qubit作用、別領域への作用、T同士がCliffordへ結合する場合などで上界は緩む。Pauli順序は一般には交換できない。 / OBDの局所探索はOFDのlong-range controlled-Pauliを必ず発見しない。Appendix Cには5qubit・6stringsの明示反例がある。探索失敗を最適性証明として使わない。 / VIは小bond dimensionのCAMPSから全bitstring確率・sampling・振幅・entropyを求めるときにも一般に指数費用が残ることを示す。数値比較は有限precisionであり、truncationを使う大規模結果は厳密比較ではない。 / Appendix Bは任意MPS入力に対してZ stabilizerだけでは不十分とし、X/Z双方の共役像とi^sの位相を保持する。共役tableauは演算子全体のglobal phaseを同定しない点は、制御された部分演算へ移す場合に別途管理が必要。

## shallow:v1-only-55 — S. Aaronson and Y. Zhang, On verifiable quantum advantage with peaked circuit sampling, arXiv preprint arXiv:2404.14493 (2024).

**一次資料:** https://arxiv.org/pdf/2404.14493 / https://arxiv.org/html/2404.14493v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。追加で§2の全定義・Lemma・Theorem・証明、§3の数値最適化手順と全caption、§4の限界・将来課題、§5謝辞を実読した19,428文字。親のAbstract/§1全文と合わせ主本文全節を完了。今回読んだ版は取得済み2026-08-24改訂のarXiv v2であり、旧主論文v1に引用された2024年時点の版と同一だとは扱わない。

**内容:** well-spread random-circuit ensembleでは平均collision probability≤γ/2^nからδ-peaked回路の出現確率≤γ/(δ² 2^n)を得る。深いrandom回路に1/poly(n)のpeakednessを作る追加層の下界は、approximate unitary designとstrong state complexityの既知定理を用いた漸近的Ω((τ_r/n)^0.19)。固定gate集合・回路ensemble・初期状態・ancilla-free measurementによる識別という定義に依存する。数値部は1D brick wallのHaar 2-qubit層にparameterized peaking層を足し、|<0|C(θ)|0>|²をgradient optimizerで最大化する。small-nでピークを増やせるが、system sizeとともに平均peak weightは指数減少し、指数改善は数値的予想として扱う。

**今回の実装への判断:** 特定のoutput weightを増やすことと、固定Boolean写像を全入力で同じに保つことは異なる。strong complexityによるrandom-state下界を固定75語のToffoli下界へ転用できない。最適化による相殺探索の動機にはなるが、回路を厳密に短くしたという構成やスコア改善は与えない。

**留保:** Appendix Aの2層回路に関する平均ピーク証明と参考文献表の全読は未実施。本文の全数式を独立再導出・数値コードを再実行していない。効率的なpeaked回路生成と古典的秘匿性は未解決条件。50-qubitで約5e−4という数値は小規模fitの外挿と条件付き可能性であり、実機達成値ではない。barren plateauによりoptimizerは制限され、最良初期化選択も使っている。

## magic:1 — Sergei Bravyi and Alexei Kitaev. “Universal quantum computation with ideal Clifford gates and noisy ancillas”. [Physical Review A 71 , 022316](https://dx.doi.org/10.1103/PhysRevA.71.022316) (2005). [arXiv:quant-ph/0403025](http://arxiv.org/abs/quant-ph/0403025) .

**一次資料:** https://arxiv.org/pdf/quant-ph/0403025

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Shared independent reading of all15 primary PDF pages, main I–VII, distillation derivations, Appendix A, bibliography.

**内容:** 理想的 Clifford 操作と十分良い非安定化子状態を用い、蒸留から普遍量子計算へ進む構成を示す。独立な資源コピー、受理条件、復号を仮定し、原論文の T-type 状態は現在の T ゲート用状態と命名が異なる。

**今回の実装への判断:** 資源状態を用いる候補では準備・受理・補正を費用に含める根拠になる。既製の magic ancilla が無料で与えられない今回の評価では、そのままローダーの Toffoli 数を減らせない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

同一文献: shallow:38

## magic:2 — Austin G. Fowler, Matteo Mariantoni, John M. Martinis, and Andrew N. Cleland. “Surface codes: Towards practical large-scale quantum computation”. [Physical Review A 86 , 032324](https://dx.doi.org/10.1103/PhysRevA.86.032324) (2012). [arXiv:1208.0928](http://arxiv.org/abs/1208.0928) .

**一次資料:** https://arxiv.org/pdf/1208.0928

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete primary extracted manuscript text read, including all appendices and references. Not an independent verification of every printed equation or figure pixel.

**内容:** surface code の誤り訂正、欠陥移動、論理ゲート、magic-state 蒸留と物理資源見積りを体系的に説明する。Clifford frame の更新と非Clifford ゲートに伴う条件付き補正を明示する。

**今回の実装への判断:** 位相を含む論理演算子の追跡と測定順序の監査に役立つ。物理面積・誤り訂正周期・理想資源を含む歴史的見積りを、今回の native Toffoli 費用へ直接換算しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:3 — Hui Zhong, Jiachen Shen, Lei Fan, Xinyue Zhang, Hao Wang, Miao Pan, and Zhu Han. “UNIQ: Communication-efficient distributed quantum computing via unified nonlinear integer programming” (2025). [arXiv:2512.00401](http://arxiv.org/abs/2512.00401) .

**一次資料:** https://arxiv.org/pdf/2512.00401

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete arXiv v1 extracted manuscript read: Sections I–VII, both algorithms and theorem arguments, all tables/captions and 42 references. No original figure pixels or simulator/code reproduction.

**内容:** 量子プロセッサーへの配置、EPR ペアの管理、通信スケジュールを非線形整数計画とヒューリスティックで共同最適化する。目的は分散計算の通信と実行時間で、任意回路の大域最適性は保証しない。

**今回の実装への判断:** 通信費用を数える将来の構成では参考になる。局所ゲートを省略したネットワーク目的関数は、単一 KMB 回路の積共有や Toffoli 最小化とは一致しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:4 — Hui Zhong, Keyi Ju, Jiachen Shen, Xinyue Zhang, Xiaoqi Qin, Tomoaki Ohtsuki, Miao Pan, and Zhu Han. “Differential privacy preserving distributed quantum computing” (2024). [arXiv:2412.12387](http://arxiv.org/abs/2412.12387) .

**一次資料:** https://arxiv.org/pdf/2412.12387

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete arXiv v2 (6 Jan 2025) extracted manuscript read: Sections 1–8, all noise-model derivations and simulations, Appendix A/Theorems 6–8, all captions and 43 references. No figure pixels or independent proof reproduction.

**内容:** 分散量子計算で測定出力の Rényi differential privacy とノイズ機構・予算配分を扱う。有限個の入力対による推定と全入力に対する保証は区別が必要である。

**今回の実装への判断:** ノイズを導入して出力分布を近づける手法であり、任意入力のコヒーレントな可逆作用を保つ合成手順にはならない。量子チャネル一般の距離と測定後の古典分布の距離も混同しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:5 — Hui Zhong, Keyi Ju, Manojna Sistla, Xinyue Zhang, Xiaoqi Qin, Xin Fu, and Miao Pan. “Tuning quantum computing privacy through quantum error correction” (2023). [arXiv:2312.14521](http://arxiv.org/abs/2312.14521) .

**一次資料:** https://arxiv.org/pdf/2312.14521

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete arXiv v1 (22 Dec 2023) extracted manuscript read: Sections I–V, all equations, Steane syndrome table, captions and 23 references. No original circuit image pixels or device experiment reproduction.

**内容:** 誤り訂正の強さを変えることで、物理ノイズに由来するプライバシーと計算精度の関係を調整する。主な評価は独立な depolarizing noise と Steane 符号の簡略モデルに基づく。

**今回の実装への判断:** ノイズと公開出力のプライバシーが対象である。誤りを許して出力を変える操作から、今回の完全一致するローダーの削減は導けない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:6 — Yuqing Li, Yusheng Zhao, Xinyue Zhang, Hui Zhong, Miao Pan, and Chi Zhang. “Differential privacy preserving quantum computing via projection operator measurements” (2023). [arXiv:2312.08210](http://arxiv.org/abs/2312.08210) .

**一次資料:** https://arxiv.org/pdf/2312.08210

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete arXiv v2 (9 Apr 2024) extracted manuscript read: Sections I–V, all four theorem derivations, captions and 18 references; no separate appendix was present in this retrieved manuscript despite an introductory appendix mention. No figure pixels or device experiments.

**内容:** 有限回の射影測定による標本変動を differential privacy に利用する。導出は中心極限定理や有限の信頼範囲に依存するため、全事象に対する厳密な pure ε-DP と同一視できない。

**今回の実装への判断:** 測定統計の近似は、未知入力の相対位相を保つ回路同値性の証拠にはならない。サンプル誤差を許さないローダー検証には直接使わない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:7 — Yusheng Zhao, Hui Zhong, Xinyue Zhang, Yuqing Li, Chi Zhang, and Miao Pan. “Bridging quantum computing and differential privacy: Insights into quantum computing privacy” (2024). [arXiv:2403.09173](http://arxiv.org/abs/2403.09173) .

**一次資料:** https://arxiv.org/pdf/2403.09173

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete arXiv v3 (14 Aug 2024) extracted text read: Sections I–VI, all four comparison tables, all formulas/captions and 65 references. No original figure pixels.

**内容:** 量子計算と differential privacy を、入力の隣接関係、状態準備、回路ノイズ、測定出力などの観点から整理する調査論文である。統一的な評価基準やプライバシー予算管理の課題も指摘する。

**今回の実装への判断:** 関連研究の所在を確認する用途には有用である。近い入力を見分けにくくする要件は、入力全体をコヒーレントに保存する正確な可逆合成とは異なる。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

**取得版の注意:** The parent bibliography and the retrieved v3 manuscript both use Insights into Quantum Computing Privacy. The earlier title A Survey on Quantum Computing Privacy appears in other citations, for example magic[4] reference [41]; it is not the title of the primary v3 text reviewed here.

## magic:8 — Keyi Ju, Xiaoqi Qin, Hui Zhong, Xinyue Zhang, Miao Pan, and Baoling Liu. “Harnessing inherent noises for privacy preservation in quantum machine learning” (2023). [arXiv:2312.11126](http://arxiv.org/abs/2312.11126) .

**一次資料:** https://arxiv.org/pdf/2312.11126

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete arXiv v2 (7 Mar 2024) extracted text read: Sections I–V, Lemma 1 and Theorem 1 arguments, PEC/parameter-shift derivations, Iris experiment setup, all captions and 15 references. No original figure pixels or experiment/code rerun.

**内容:** 量子機械学習の有限ショットと物理ノイズによるプライバシーを解析し、Gaussian 近似や勾配の分散を評価する。確率的誤り軽減は期待値を回復しても標本分散を増やし得る。

**今回の実装への判断:** 期待値推定の改善を、未知入力に対するチャネルの完全一致へ置き換えない。正確な chemistry ローダーのゲート削減案は得られない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:9 — Sergey Bravyi and Jeongwan Haah. “Magic-state distillation with low overhead”. [Physical Review A 86 , 052329](https://dx.doi.org/10.1103/PhysRevA.86.052329) (2012). [arXiv:1209.2426](http://arxiv.org/abs/1209.2426) .

**一次資料:** https://arxiv.org/pdf/1209.2426

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Entire11-page primary v1 extraction: sections I–IX, Appendices A–B, bibliography and table/figure captions. Missing tool-output middle was separately reread in full; no figure-pixel verification.

**内容:** triorthogonal な二進行列から、多数の T 資源を同時に出力する蒸留符号を構成する。理想 Clifford、独立な入力誤り、受理条件を仮定し、出力間の相関は次の蒸留段で扱う必要がある。

**今回の実装への判断:** 列の重複度と GF(2) 制約を使う限定的な符号探索は参考になる。ただし符号の蒸留率は、任意の Boolean ローダーの AND/Toffoli 複雑さの下界ではない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:10 — Adam M. Meier, Bryan Eastin, and Emanuel Knill. “Magic-state distillation with the four-qubit code”. [Quantum Information and Computation 13 , 195–209](https://dx.doi.org/10.26421/QIC13.3-4-2) (2013). [arXiv:1204.4221](http://arxiv.org/abs/1204.4221) .

**一次資料:** https://arxiv.org/pdf/1204.4221

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Entire10-page primary v1 extraction, all main sections I–VI, exact acceptance/error polynomials, Lemma IV.1 and Corollary IV.2, bibliography, appendix and all captions. Circuit images not rendered.

**内容:** 4量子ビット符号を用いた 10-to-2 の Hadamard 型 magic-state 蒸留を示す。誤り率だけでなく受理率と出力間相関を含めて、後続段への接続を設計する。

**今回の実装への判断:** 資源状態の準備費用を評価する際には有用である。準備済み状態と理想補正が別途必要なため、現在1と数える CCZ の費用をこれだけで下げられない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:11 — Cody Jones. “Multilevel distillation of magic states for quantum computing”. [Physical Review A 87 , 042305](https://dx.doi.org/10.1103/PhysRevA.87.042305) (2013). [arXiv:1210.3388](http://arxiv.org/abs/1210.3388) .

**一次資料:** https://arxiv.org/pdf/1210.3388

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Entire10-page primary v2 extraction, main I–V, bibliography, Appendices A–D and complete numerical Table I; figure pixels not inspected.

**内容:** transversal-H 符号の多段構成によって magic-state 蒸留の資源消費を抑える。高い段数では追加チェックと相関管理が必要で、漸近的な指数は一般最適性の証明ではない。

**今回の実装への判断:** 生の magic-state 消費量と物理回路全体の費用を分ける必要がある。今回の小規模な可逆ロード回路へ、その指数だけを移して改善とは数えない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:12 — Earl T. Campbell, Barbara M. Terhal, and Christophe Vuillot. “Roads towards fault-tolerant universal quantum computation”. [Nature 549 , 172–179](https://dx.doi.org/10.1038/nature23460) (2017). [arXiv:1612.07330](http://arxiv.org/abs/1612.07330) .

**一次資料:** https://arxiv.org/pdf/1612.07330

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Entire9-page primary v2 extraction: main I–V, Boxes1–3, Table I, all figures through text/captions and85 references. Linked supplementary video not watched.

**内容:** magic-state 蒸留、color code、gauge fixing、pieceable fault tolerance などの普遍耐故障計算を比較する。各方式で符号、局所性、測定、物理資源の前提が異なる。

**今回の実装への判断:** 候補がどの操作と物理モデルを追加しているかを点検する見取り図になる。幾何学的な no-go 定理から、全結合の有限ローダーの Toffoli 下界は得られない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:13 — Victor Veitch, Seyed Ali Hamed Mousavian, Daniel Gottesman, and Joseph Emerson. “The resource theory of stabilizer quantum computation”. [New Journal of Physics 16 , 013009](https://dx.doi.org/10.1088/1367-2630/16/1/013009) (2014). [arXiv:1307.7171](http://arxiv.org/abs/1307.7171) .

**一次資料:** https://arxiv.org/pdf/1307.7171

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete primary arXiv v1 extracted text read: main Sections I–V, conclusions, Appendices A–B, all references and captions; no figure pixels or independent proof verification.

**内容:** stabilizer 操作の資源理論を構成し、相対エントロピーや Wigner negativity・mana による変換制限を論じる。mana の主要な構成は奇素数次元に依存し、量子ビットへそのまま適用できない。

**今回の実装への判断:** 資源単調量の前提と許可操作集合を確認するために有用である。単調量の値を特定の qubit 回路の Toffoli 数や構成法と同一視しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:14 — Mark Howard, Joel J. Wallman, Victor Veitch, and Joseph Emerson. “Contextuality supplies the “magic” for quantum computation”. [Nature 510 , 351–355](https://dx.doi.org/10.1038/nature13460) (2014). [arXiv:1401.4174](http://arxiv.org/abs/1401.4174) .

**一次資料:** https://arxiv.org/pdf/1401.4174

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete primary arXiv v2 extracted text read: main article, all references, Supplementary Information including Theorem 2, Lemmas 3–5 and Theorem 6 proofs; no figure pixels or independent proof verification.

**内容:** 奇素数次元の安定化子測定と contextuality・離散 Wigner 表現を結び付ける。contextuality と実際の蒸留可能性の関係には、証明された部分と予想の部分がある。

**今回の実装への判断:** 非古典性の資源を特定する理論であり、回路合成アルゴリズムではない。量子ビットの状態非依存 contextuality という例外もあるため、native CCX 数への直接換算は避ける。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:15 — Mark Howard and Earl T. Campbell. “Application of a resource theory for magic states to fault-tolerant quantum computing”. [Physical Review Letters 118 , 090501](https://dx.doi.org/10.1103/PhysRevLett.118.090501) (2017). [arXiv:1609.07488](http://arxiv.org/abs/1609.07488) .

**一次資料:** https://arxiv.org/pdf/1609.07488

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Entire10-page primary PDF extraction read including main text, bibliography, all appendix proofs and tables; diagrams read through captions/text, not pixel-rendered.

**内容:** robustness of magic を線形計画で扱い、Clifford 同値な資源状態を用いた小規模な対角ゲート合成を示す。測定補助付きの決定的 CCZ 合成に4個の T 資源が必要かつ十分であることを得る。

**今回の実装への判断:** 具体的な合成と資源下界が結び付く重要な参考文献である。ただし今回の評価では CCZ 自体を1 Toffoli 相当として扱うため、4T 実装だけでは1未満への改善にならない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:16 — James R. Seddon and Earl T. Campbell. “Quantifying magic for multi-qubit operations”. [Proceedings of the Royal Society A 475 , 20190251](https://dx.doi.org/10.1098/rspa.2019.0251) (2019). [arXiv:1901.03322](http://arxiv.org/abs/1901.03322) .

**一次資料:** https://arxiv.org/pdf/1901.03322

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete primary arXiv v2 (2 Jul 2019), 40-page extracted manuscript read: Sections 1–9, all references, Appendices A–E, numerical tables, algorithms and captions. No figure pixels, source-code execution or independent proof verification.

**内容:** 多量子ビットのチャネルについて robustness、magic capacity、古典 Monte Carlo シミュレーションを構成する。Choi 状態の単調量とチャネル合成に対する単調量は区別される。

**今回の実装への判断:** 演算全体の位相と資源を評価する方法として参考になる。CSP という広い自由操作集合での変換や古典標本化は、許可された KMB ゲート列を与えるものではない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:17 — Sergey Bravyi and David Gosset. “Improved classical simulation of quantum circuits dominated by clifford gates”. [Physical Review Letters 116 , 250501](https://dx.doi.org/10.1103/PhysRevLett.116.250501) (2016). [arXiv:1601.07601](http://arxiv.org/abs/1601.07601) .

**一次資料:** https://arxiv.org/pdf/1601.07601

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read; all captions but not image pixels. Full reading is distinct from independent proof or implementation verification.

**内容:** stabilizer 分解によって Clifford+T 回路を古典計算し、確率推定と近似サンプリングの計算量を抑える。付録はアフィン支持、二次位相、内積計算などを明示する。

**今回の実装への判断:** 位相を保持する独立検証器の構成に使える。近似した出力分布を標本化できることは、任意入力のコヒーレントな回路を同じ Toffoli 数で実装できることとは別である。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

同一文献: shallow:19

## magic:18 — Markus Heinrich and David Gross. “Robustness of magic and symmetries of the stabiliser polytope”. [Quantum 3 , 132](https://dx.doi.org/10.22331/q-2019-04-08-132) (2019). [arXiv:1807.10296](http://arxiv.org/abs/1807.10296) .

**一次資料:** https://arxiv.org/pdf/1807.10296

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete primary arXiv v3, 35-page extracted manuscript read: Sections 1–6, Appendices A–E including symmetry/3-design proofs, algorithm, numerical tables, captions and all 42 references. No original figure pixels, source execution, or independent proof reproduction.

**内容:** 対称性で stabilizer polytope の線形計画を縮約し、robustness の数値計算と近似階層を構成する。有限個の数値結果や制限された分解による上界は、一般の漸近最適性とは異なる。

**今回の実装への判断:** 正しい対称群がある場合の探索空間削減は参考になる。資源分解の効率や古典シミュレーションの指数から、今回のローダーの積共有数は直接決まらない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:19 — Craig Gidney, Noah Shutty, and Cody Jones. “Magic state cultivation: growing T states as cheap as CNOT gates” (2024). [arXiv:2409.17595](http://arxiv.org/abs/2409.17595) .

**一次資料:** https://arxiv.org/pdf/2409.17595

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** All 33 pages of extracted primary v1 PDF: main sections, references, Appendices A–C, captions and tables. Figures not rendered; published code and numerical data not rerun.

**内容:** 注入、検査、符号成長、脱出を組み合わせた T-state cultivation を設計する。読んだ v1 の大規模評価には S-state proxy と明示された仮定があり、符号や誤りモデルを固定して比較している。

**今回の実装への判断:** 測定をまたぐ stabilizer flow を契約として検査する発想は有用である。受理率、準備、成長、最終消費までの費用を省略したまま native Toffoli の節減としない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:20 — I-Chi Chen, Matheus da Silva Fonseca, and Andrew Sornborger. “Efficient magic state cultivation for $\sqrt{T}$ gates” (2026). [arXiv:2606.10430](http://arxiv.org/abs/2606.10430) .

**一次資料:** https://arxiv.org/pdf/2606.10430

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Entire22-page extracted primary v1 PDF: main I–V, Appendices A–G, reference list, tables and captions. No figure pixel inspection or independent circuit/noise simulation.

**内容:** 二重 color code と符号変換を使い、sqrt(T) など高い Clifford 階層の資源状態へ cultivation を拡張する。大規模評価の proxy、成長工程、触媒状態の初期準備が性能比較の条件になる。

**今回の実装への判断:** 利用する回転の角度と資源準備モデルが一致する場合に検討できる。許可された回転が固定された今回の評価では、新しい資源状態を導入するだけで費用を下げられない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:21 — Jahan Claes. “Cultivating T states on the surface code with only two-qubit gates” (2025). [arXiv:2509.05232](http://arxiv.org/abs/2509.05232) .

**一次資料:** https://arxiv.org/pdf/2509.05232

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Entire extracted primary v2 PDF: all 14 pages, main text, noise-model appendix, bibliography, captions and tables. Figure pixels not inspected.

**内容:** surface code の折り畳みと cat ancilla を用い、二量子ビットゲートだけで T-state cultivation を行う構成を示す。物理接続、qubit 移動、proxy による評価条件を伴う。

**今回の実装への判断:** 三量子ビット物理ゲートを使えない装置では有用な設計比較になる。論理 CCX を既に1と数えるモデルでは、物理ゲート種の変更だけでローダー費用は下がらない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:22 — Kaavya Sahay, Pei-Kai Tsai, Kathleen Chang, Qile Su, Thomas B. Smith, Shraddha Singh, and Shruti Puri. “Fold-transversal surface code cultivation”. [PRX Quantum 7 , 033006](https://dx.doi.org/10.1103/gpvl-lg4c) (2026). [arXiv:2509.05212](http://arxiv.org/abs/2509.05212) .

**一次資料:** https://arxiv.org/pdf/2509.05212

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Entire extracted primary v2 PDF: all 25 pages, main sections I–IV, bibliography, Appendices A–E, all extracted table contents and figure captions. Figure pixels and supplied code not independently inspected.

**内容:** surface code 内で fold-transversal な Clifford 検査と符号成長を行い、cultivation の物理費用を評価する。Appendix D の syndrome 引き継ぎは、後続が特定の Clifford 操作であることを利用する。

**今回の実装への判断:** 古い測定値を使う際に、その後の全論理作用を確認する考え方は HMR 監査に役立つ。非局所接続、受理率、補正、成長工程を数えずに Toffoli 削減へ換算しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:23 — Yotam Vaknin, Shoham Jacoby, Arne Grimsmo, and Alex Retzker. “High rate magic state cultivation on the surface code”. [PRX Quantum 7 , 010353](https://dx.doi.org/10.1103/p8tw-6kq9) (2026). [arXiv:2502.01743](http://arxiv.org/abs/2502.01743) .

**一次資料:** https://arxiv.org/pdf/2502.01743

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Entire21-page extracted primary v4 PDF, main I–VII, bibliography, Appendices A–L, all captions/tables/pseudocode; figures not rendered and external code not rerun.

**内容:** 非局所な controlled fold と三量子ビットゲートを用い、surface code 上の H/HXY cultivation と erasure 検出を評価する。取得 v4 の表紙は High Rate、取得メタデータと abs は Efficient と題名が異なるため、読了は実キャッシュの版とハッシュに固定する。

**今回の実装への判断:** Appendix I の Fredkin＝1 CCZ＋2 CX は今回の cache retirement と同じ恒等式を確認する。CX 射影の多次元受理空間や物理ノイズの前提を省略して、未知入力の無料リセットや追加の Toffoli 節減を導かない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

**取得版の注意:** The cached primary PDF explicitly bears title High Rate Magic State Cultivation on the Surface Code, matching the parent bibliography. The fetch metadata title, and the arXiv abstract page independently opened by the root, instead say Efficient Magic State Cultivation on the Surface Code. The full-text reading claim is pinned to the cached v4 PDF/header and SHA256 below, not inferred from the current abstract-page title. No newer differently titled full text is claimed read.

## magic:24 — Dennis Kretschmann, Dirk Schlingemann, and Reinhard F. Werner. “A continuity theorem for Stinespring’s dilation”. [Journal of Functional Analysis 255 , 1889–1904](https://dx.doi.org/10.1016/j.jfa.2008.07.023) (2008).

**一次資料:** https://arxiv.org/pdf/0710.2495

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Entire18-page primary arXiv v1 extraction: sections1–5, Theorems1–2, all lemmas/propositions and proofs, Appendices A–B, references. Original publisher landing page was abstract-only and is not the reading source.

**内容:** CP map の cb/diamond 型距離と、共通環境上の Stinespring dilation を最適化した距離の連続性を示す。近い dilation が存在することと、任意に固定した dilation が近いことは異なる。

**今回の実装への判断:** 親論文の局所誤差を一つの整合した回路表現へ結合できるかを点検する根拠になる。個別に最適化した gauge を、固定された回路で同時に使えると仮定しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

**取得版の注意:** Publisher page contains abstract/section snippets; full primary arXiv text recovered separately.

## magic:25 — Daniel Gottesman. “Stabilizer codes and quantum error correction”. [PhD thesis](https://dx.doi.org/10.7907/rzr7-dt72) . California Institute of Technology. (1997). [arXiv:quant-ph/9705052](http://arxiv.org/abs/quant-ph/9705052) .

**一次資料:** https://arxiv.org/pdf/quant-ph/9705052

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete primary extracted thesis text read: front matter, Chapters 1–8, Appendices A–B and bibliography [1]–[65]. Captions and extracted code tables read; not every circuit figure pixel or formula transcription independently audited.

**内容:** stabilizer 符号、符号化・復号、測定を使う論理ゲート、閾値の概算、符号パラメーターの境界と具体例を体系的に導く。測定による置換には既知 stabilizer と入力非依存 syndrome が必要で、Toffoli ancilla の準備には非Clifford 操作を使う。

**今回の実装への判断:** 位相を含む GF(2) 表現と測定後補正の正当化に直接役立つ。符号空間内の恒等式を任意入力へ拡張せず、encoded zero を清浄な物理 qubit と数えず、本文の Clifford T を現代のπ/8 T と混同しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

同一文献: shallow:13

## magic:26 — Scott Aaronson and Daniel Gottesman. “Improved simulation of stabilizer circuits”. [Physical Review A 70 , 052328](https://dx.doi.org/10.1103/PhysRevA.70.052328) (2004). [arXiv:quant-ph/0406196](http://arxiv.org/abs/quant-ph/0406196) .

**一次資料:** https://arxiv.org/pdf/quant-ph/0406196

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read; image pixels not inspected. Reading does not independently certify every proof.

**内容:** destabilizer を併用した tableau により、stabilizer 回路の測定と更新を効率化する。Clifford の標準形と CNOT 数の漸近境界、混合状態や非Clifford 拡張も扱う。

**今回の実装への判断:** 測定・符号・論理作用の検証器に有用である。大域位相を省く内積処理と、相対位相を必要とする HMR の契約を分け、Clifford の一般的境界をローダーの Toffoli 最適性と解釈しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

同一文献: shallow:16

## magic:27 — Jeroen Dehaene and Bart De Moor. “The clifford group, stabilizer states, and linear and quadratic operations over GF(2)”. [Physical Review A 68 , 042318](https://dx.doi.org/10.1103/PhysRevA.68.042318) (2003). [arXiv:quant-ph/0304125](http://arxiv.org/abs/quant-ph/0304125) .

**一次資料:** https://arxiv.org/pdf/quant-ph/0304125

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Shared independent reading of all9 primary PDF pages, main I–VI, Theorems1–6 and proofs, Appendix Eq(4) proof, bibliography.

**内容:** Clifford 操作と stabilizer 状態を、二進 symplectic 行列、アフィン支持、二次位相で表現する。位相補正を含む合成法と二体ゲート分解を与える。

**今回の実装への判断:** Boolean 値だけでなく相対位相まで保つ GF(2)/HMR 検証の独立した根拠になる。Clifford ゲートの削減だけでは、現在の Toffoli 目的関数は改善しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

同一文献: shallow:36

## magic:28 — A. Yu. Kitaev. “Fault-tolerant quantum computation by anyons”. [Annals of Physics 303 , 2–30](https://dx.doi.org/10.1016/S0003-4916\(02\)00018-0) (2003). [arXiv:quant-ph/9707021](http://arxiv.org/abs/quant-ph/9707021) .

**一次資料:** https://arxiv.org/pdf/quant-ph/9707021

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and appendices; figure captions read, image pixels not inspected. Reading is not an independent verification of every proof.

**内容:** toric code と有限群の quantum double を構成し、anyon の融合・組紐を用いる耐故障計算の枠組みを示す。非可換例の普遍性や物理的な安定性には、別途必要な条件と構成がある。

**今回の実装への判断:** topological operation の意味を確認する基礎資料である。位相の分類や局所誤りからの保護は、有限温度での自己訂正や今回の可逆算術の無料実装を意味しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:29 — Alexei Kitaev and Liang Kong. “Models for gapped boundaries and domain walls”. [Communications in Mathematical Physics 313 , 351–373](https://dx.doi.org/10.1007/s00220-012-1500-5) (2012). [arXiv:1104.5047](http://arxiv.org/abs/1104.5047) .

**一次資料:** https://arxiv.org/pdf/1104.5047

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and appendices; figure captions read, image pixels not inspected. Reading is not an independent verification of every proof.

**内容:** Levin–Wen 型格子模型の gapped boundary と domain wall を module・bimodule category で記述する。Morita 同値と透明な壁の関係を整理する。

**今回の実装への判断:** 壁や境界を使う構成の可逆性を確認する理論である。非可逆な壁の分類と物理ゲート費用は別なので、圏論上の同値だけで qubit や Toffoli を消去しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:30 — Salman Beigi, Peter W. Shor, and Daniel Whalen. “The quantum double model with boundary: Condensations and symmetries”. [Communications in Mathematical Physics 306 , 663–694](https://dx.doi.org/10.1007/s00220-011-1294-x) (2011). [arXiv:1006.5479](http://arxiv.org/abs/1006.5479) .

**一次資料:** https://arxiv.org/pdf/1006.5479

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and appendices; figure captions read, image pixels not inspected. Reading is not an independent verification of every proof.

**内容:** 有限群の quantum double に境界を導入し、部分群と cocycle から凝縮・anyon の透過・対称性を解析する。折り畳みによる記述では組紐の向きや境界条件も追跡する。

**今回の実装への判断:** ラベル対応があっても融合と位相の整合性が必要であることを示す。modular S/T を保存する置換を、完全な braided 同値や無料の回路置換と同一視しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:31 — Maissam Barkeshli, Parsa Bonderson, Meng Cheng, and Zhenghan Wang. “Symmetry fractionalization, defects, and gauging of topological phases”. [Physical Review B 100 , 115147](https://dx.doi.org/10.1103/PhysRevB.100.115147) (2019). [arXiv:1410.4540](http://arxiv.org/abs/1410.4540) .

**一次資料:** https://arxiv.org/pdf/1410.4540

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete primary extracted manuscript text read by /root/shared_synthesis, including all appendices and references. Figure captions read; not every image or mathematical transcription independently checked.

**内容:** 対称性の分数化、欠陥の融合・組紐、gauging を G-crossed 理論で整理し、H³/H⁴ の障害と多数の例を与える。有限・オンサイト・unitary 対称性などの仮定を区別し、ラベルが固定でも −1 位相が残る例を含む。

**今回の実装への判断:** ビット値や固定点だけでなく相対位相を検査する必要性の具体例になる。圏論上の gauge 変更や分類結果から、固定した75語の Toffoli 最小数や無料の物理変換は導けない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:32 — Eric Dennis, Alexei Kitaev, Andrew Landahl, and John Preskill. “Topological quantum memory”. [Journal of Mathematical Physics 43 , 4452–4505](https://dx.doi.org/10.1063/1.1499754) (2002). [arXiv:quant-ph/0110143](http://arxiv.org/abs/quant-ph/0110143) .

**一次資料:** https://arxiv.org/pdf/quant-ph/0110143

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete primary manuscript text actually read; all captions but not diagram pixels. No claim of independent full proof or numerical reproduction.

**内容:** topological quantum memory の復号と閾値を、homology と格子統計模型へ結び付ける。最尤の homology class を選ぶ方法と、最小重みの単一誤り鎖を選ぶ方法は異なる。

**今回の実装への判断:** 測定履歴、hook error、入力条件を保った論理操作の監査に役立つ。実数化や共役回路による出力統計の再現を、未知入力の完全なチャネル同値として使わない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:33 — Guillaume Duclos-Cianci and David Poulin. “Fast decoders for topological quantum codes”. [Physical Review Letters 104 , 050504](https://dx.doi.org/10.1103/PhysRevLett.104.050504) (2010). [arXiv:0911.0581](http://arxiv.org/abs/0911.0581) .

**一次資料:** https://arxiv.org/pdf/0911.0581

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and any appendices present; figure captions read, image pixels not inspected. Reading is not an independent verification of all proofs.

**内容:** renormalization と belief propagation を組み合わせ、topological code の復号を並列化する。報告された高い閾値は主に完全な syndrome を仮定した数値評価である。

**今回の実装への判断:** 大規模な物理誤り訂正器の古典実行時間を改善する方法である。復号の計算量や並列深さは、今回の量子ローダーの Toffoli 数とは別に数える。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:34 — Nicolas Delfosse and Naomi H. Nickerson. “Almost-linear time decoding algorithm for topological codes”. [Quantum 5 , 595](https://dx.doi.org/10.22331/q-2021-12-02-595) (2021). [arXiv:1709.06218](http://arxiv.org/abs/1709.06218) .

**一次資料:** https://arxiv.org/pdf/1709.06218

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and appendices; figure captions read, image pixels not inspected. Reading is not an independent verification of every proof.

**内容:** union-find による cluster 成長と peeling を用い、ほぼ線形時間で Pauli 誤りと erasure を復号する。距離に基づく訂正保証と数値性能を分けて提示する。

**今回の実装への判断:** 古典的な誤り位置の管理には有用である。復号器内の virtual erasure は量子状態の消去ではないため、live qubit の無料リセットには使えない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:35 — Dominic Horsman, Austin G. Fowler, Simon Devitt, and Rodney Van Meter. “Surface code quantum computing by lattice surgery”. [New Journal of Physics 14 , 123011](https://dx.doi.org/10.1088/1367-2630/14/12/123011) (2012). [arXiv:1111.4022](http://arxiv.org/abs/1111.4022) .

**一次資料:** https://arxiv.org/pdf/1111.4022

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and appendices; figure captions read, image pixels not inspected. Reading is not an independent verification of every proof.

**内容:** planar surface code の merge と split により、局所性を保った論理測定や CNOT を構成する。境界測定の結果に応じた補正と、距離を確保する面積・測定周期が必要になる。

**今回の実装への判断:** 二つの論理入力を一つへ merge する操作は一般には非unitaryである。符号空間と測定補正を省略したまま、任意入力の可逆ロードへ置き換えない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:36 — Robert Raussendorf, Jim Harrington, and Kovid Goyal. “Topological fault-tolerance in cluster state quantum computation”. [New Journal of Physics 9 , 199](https://dx.doi.org/10.1088/1367-2630/9/6/199) (2007). [arXiv:quant-ph/0703143](http://arxiv.org/abs/quant-ph/0703143) .

**一次資料:** https://arxiv.org/pdf/quant-ph/0703143

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and appendices; figure captions read, image pixels not inspected. Reading is not an independent verification of every proof.

**内容:** 3D cluster-state 計算を2D空間と時間の構成として用い、欠陥の幾何と誤り訂正から耐故障計算を実現する。非Clifford 資源には別の準備・蒸留工程を要する。

**今回の実装への判断:** topological な回路同値の前提となる相関と境界条件を確認できる。物理体積や特定ノイズ模型の閾値は、有限の KMB 回路の CCX 数の改善証拠にはならない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:37 — Daniel Litinski and Felix von Oppen. “Lattice surgery with a twist: Simplifying clifford gates of surface codes”. [Quantum 2 , 62](https://dx.doi.org/10.22331/q-2018-05-04-62) (2018). [arXiv:1709.02318](http://arxiv.org/abs/1709.02318) .

**一次資料:** https://arxiv.org/pdf/1709.02318

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and appendices; figure captions read, image pixels not inspected. Reading is not an independent verification of every proof.

**内容:** Clifford frame の古典追跡と twist を含む lattice surgery により、surface-code 操作と長距離の多標的 CNOT を整理する。測定軸、接続用面積、hook error の管理を伴う。

**今回の実装への判断:** 後続の測定基底まで変更できる場合は、Clifford の移動・吸収が可能である。固定した出力レジスターと位相を要求するローダーでは、frame を戻す費用まで確認する。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:38 — Daniel Litinski. “A game of surface codes: Large-scale quantum computing with lattice surgery”. [Quantum 3 , 128](https://dx.doi.org/10.22331/q-2019-03-05-128) (2019). [arXiv:1808.02892](http://arxiv.org/abs/1808.02892) .

**一次資料:** https://arxiv.org/pdf/1808.02892

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete primary manuscript text read including appendices and captions; diagrams not visually audited, no independent full implementation or proof replication.

**内容:** surface-code patch を tile と時間段階で表し、data block と magic-state 工場の面積・時間を比較する。蒸留の spectator 消去や Clifford frame の吸収には、初期状態と終端測定の条件がある。

**今回の実装への判断:** 既知状態の中間レジスターを省く着想は検討できる。tile の0時間はゼロゲートを意味せず、未知入力の cache 消去や固定出力へは補正と相関の確認が必要である。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:39 — Matthew B. Hastings and Jeongwan Haah. “Dynamically generated logical qubits”. [Quantum 5 , 564](https://dx.doi.org/10.22331/q-2021-10-19-564) (2021). [arXiv:2107.02194](http://arxiv.org/abs/2107.02194) .

**一次資料:** https://arxiv.org/pdf/2107.02194

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and appendices; figure captions read, image pixels not inspected. Reading is not an independent verification of every proof.

**内容:** 二体 Pauli 測定を周期的に並べる honeycomb Floquet code で、静的 gauge group からは見えない論理量子ビットを生成する。測定順序と instantaneous stabilizer group が保護される情報を決める。

**今回の実装への判断:** 同じ測定集合でも順序が変わると論理情報を失い得る、という監査上の注意を与える。周期や情報の移動だけから物理 qubit の節約は導けない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:40 — Christophe Vuillot. “Planar floquet codes” (2021). [arXiv:2110.05348](http://arxiv.org/abs/2110.05348) .

**一次資料:** https://arxiv.org/pdf/2110.05348

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and appendices; figure captions read, image pixels not inspected. Reading is not an independent verification of every proof.

**内容:** planar な Floquet boundary を検討するが、読んだ v2 は回転する境界構成に一定重みの時空論理誤りがあり、耐故障ではないと訂正している。後の別構成の性能をこの版の結果に含めない。

**今回の実装への判断:** 見かけの各時刻の符号距離だけでは、全測定履歴を含む安全性を保証できない例である。この境界構成を改善済みの回路候補として採用しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:41 — Margarita Davydova, Nathanan Tantivasadakarn, Shankar Balasubramanian, and David Aasen. “Quantum computation from dynamic automorphism codes”. [Quantum 8 , 1448](https://dx.doi.org/10.22331/q-2024-08-27-1448) (2024). [arXiv:2307.10353](http://arxiv.org/abs/2307.10353) .

**一次資料:** https://arxiv.org/pdf/2307.10353

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete primary extracted manuscript text read, including all appendices and references. This is not full visual audit of the many detector diagrams, nor independent reproof or circuit implementation.

**内容:** 局所可逆な測定列で符号空間を移しながら論理ゲートを実行する dynamic automorphism code を構成する。効率的復号器・閾値や一部の耐故障性は未解決で、非Clifford 操作には非Pauli測定と適応補正を要する。

**今回の実装への判断:** 測定結果を捨てられる条件と、全論理演算子を保持する検査は有用である。符号化、多層 qubit、非Pauli測定、復号と frame の費用を含む実回路なしに、今回の Toffoli 数や幅の改善とは数えない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:42 — S. B. Bravyi and A. Yu. Kitaev. “Quantum codes on a lattice with boundary” (1998). [arXiv:quant-ph/9811052](http://arxiv.org/abs/quant-ph/9811052) .

**一次資料:** https://arxiv.org/pdf/quant-ph/9811052

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and any appendices present; figure captions read, image pixels not inspected. Reading is not an independent verification of all proofs.

**内容:** rough/smooth boundary を持つ格子符号を relative homology で表し、境界の配置と論理自由度の関係を示す。符号空間内の string operator が論理演算子になる。

**今回の実装への判断:** surface-code 境界を使う提案の情報量と論理作用を数える基礎となる。一般の算術回路の ancilla 再利用法や Toffoli 削減を与えるものではない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:43 — H. Bombin and M. A. Martin-Delgado. “Optimal resources for topological 2D stabilizer codes: Comparative study”. [Physical Review A 76 , 012305](https://dx.doi.org/10.1103/PhysRevA.76.012305) (2007). [arXiv:quant-ph/0703272](http://arxiv.org/abs/quant-ph/0703272) .

**一次資料:** https://arxiv.org/pdf/quant-ph/0703272

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Complete cached primary manuscript text actually read, including terminal references and any appendices present; figure captions read, image pixels not inspected. Reading is not an independent verification of all proofs.

**内容:** 2D の surface code と color code を、符号距離に対する data qubit 数の比で比較する。torus と planar boundary では条件と有利な配置が異なる。

**今回の実装への判断:** 符号化したアーキテクチャを選ぶ場合の比較である。syndrome ancilla、非Clifford 操作、耐故障の全費用を含まない比率を、今回の回路幅へ直接置き換えない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:44 — Nobuyuki Yoshioka, Alireza Seif, Peter Groszkowski, Andrew Cross, and Ali Javadi-Abhari. “Theory and architecture of syndrome-resolved logical gates” (2025). [arXiv:2510.08290](http://arxiv.org/abs/2510.08290) .

**一次資料:** https://arxiv.org/pdf/2510.08290

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Actual complete primary-text reading by named collaborating agent; detailed scope and primary-image checks in evidence ledger.

**内容:** 各 syndrome 分岐が入力非依存な確率で論理ユニタリを与える weak transversal gate を構成し、RUS で角度を補正する。既存 CNOT の伝播へ回転を埋め込む手法も示す。

**今回の実装への判断:** K_s†K_s＝p_s I と補正後の論理位相を別々に証明する基準、既存パリティの再利用が参考になる。物理工場の倍率は native Toffoli の倍率ではなく、proxy の誤差指標や hook doping による距離低下を含めて評価する。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:45 — Eric Huang, Pierre-Gabriel Rozon, Arpit Dua, Sarang Gopalakrishnan, and Michael J. Gullans. “A robust phase of continuous transversal gates in quantum stabilizer codes” (2025). [arXiv:2510.01319](http://arxiv.org/abs/2510.01319) .

**一次資料:** https://arxiv.org/pdf/2510.01319

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Actual complete primary-text reading by named collaborating agent; detailed scope and primary-image checks in evidence ledger.

**内容:** 奇数距離の surface code で連続角の transversal 操作を繰り返し、復号・reset を含む方策によって資源状態を準備する。主要な評価は物理 Z dephasing のモデルに基づく。

**今回の実装への判断:** 準備される状態を指定した繰り返し手順として検討できる。状態準備中の reset を、任意の未知入力を保持する oracle の reset として使わない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:46 — Sergey Bravyi and Robert Koenig. “Classification of topologically protected gates for local stabilizer codes”. [Physical Review Letters 110 , 170503](https://dx.doi.org/10.1103/PhysRevLett.110.170503) (2013). [arXiv:1206.1609](http://arxiv.org/abs/1206.1609) .

**一次資料:** https://arxiv.org/pdf/1206.1609

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Actual complete primary-text reading by named collaborating agent; detailed scope and primary-image checks in evidence ledger.

**内容:** 幾何学的に局所な topological stabilizer code の一定深さユニタリを、空間次元に対応する Clifford 階層へ制限する。符号を保ち、伝播範囲が限定されることが重要な仮定である。

**今回の実装への判断:** 無料の保護ゲートを仮定する提案の条件を点検できる。全結合、適応測定、任意の code deformation を含む今回の有限回路の Toffoli 下界ではない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:47 — Michael E. Beverland, Oliver Buerschaper, Robert Koenig, Fernando Pastawski, John Preskill, and Sumit Sijher. “Protected gates for topological quantum field theories”. [Journal of Mathematical Physics 57 , 022201](https://dx.doi.org/10.1063/1.4939783) (2016). [arXiv:1409.3898](http://arxiv.org/abs/1409.3898) .

**一次資料:** https://arxiv.org/pdf/1409.3898

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Actual complete primary-text reading by named collaborating agent; detailed scope and primary-image checks in evidence ledger.

**内容:** 2D TQFT の locality-preserving な保護ゲートを、各融合基底で整合する位相付き置換として制約する。Fibonacci・Ising などの結論は曲面、荷電ラベル、mapping class group の条件に依存する。

**今回の実装への判断:** ラベルの置換だけでなく位相と基底間の整合性を検査する根拠になる。固定2Dトポロジーと局所ユニタリの no-go を、一般の KMB 回路の4170境界へ適用しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:48 — David Aasen, Jeongwan Haah, Zhi Li, and Roger S. K. Mong. “Measurement quantum cellular automata and anomalies in floquet codes” (2023). [arXiv:2304.01277](http://arxiv.org/abs/2304.01277) .

**一次資料:** https://arxiv.org/pdf/2304.01277

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Actual complete primary-text reading by named collaborating agent; detailed scope and primary-image checks in evidence ledger.

**内容:** 局所可逆な Pauli 測定列を measurement QCA として扱い、情報の流れと Floquet 境界の anomaly を分類する。補正後の論理情報保存と、境界に生じる非自明な流れを区別する。

**今回の実装への判断:** 測定が未知入力の情報を漏らさず論理作用を保つ条件に役立つ。情報の移動や周期変更は物理 qubit の削除ではなく、ancilla 追加も含めた実回路の費用が必要である。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:49 — Paul Webster and Stephen D. Bartlett. “Locality-preserving logical operators in topological stabiliser codes”. [Physical Review A 97 , 012330](https://dx.doi.org/10.1103/PhysRevA.97.012330) (2018). [arXiv:1709.00020](http://arxiv.org/abs/1709.00020) .

**一次資料:** https://arxiv.org/pdf/1709.00020

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Actual complete primary-text reading by named collaborating agent; detailed scope and primary-image checks in evidence ledger.

**内容:** locality-preserving logical operator を透明な domain wall と対応付け、topological stabilizer code の論理操作を分類する。空間次元、励起の次元、stack と境界条件が許される Clifford 階層を決める。

**今回の実装への判断:** 3D 符号で CCZ が可能という構造は、現在の1 CCZ の費用を下回る置換ではない。Boolean address 変換や積共有とは別に、符号化と物理操作を全て数えて検討する。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:50 — Sergey Bravyi, Isaac Kim, Alexander Kliesch, and Robert Koenig. “Adaptive constant-depth circuits for manipulating non-abelian anyons” (2022). [arXiv:2205.01933](http://arxiv.org/abs/2205.01933) .

**一次資料:** https://arxiv.org/pdf/2205.01933

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Actual complete primary-text reading by named collaborating agent; detailed scope and primary-image checks in evidence ledger.

**内容:** 固定された有限 solvable group の quantum double について、適応測定と古典処理を用いる一定量子深さの状態準備・anyon 操作を示す。付録の印刷式2箇所には独立の反例・正規化不整合を記録したが、全主定理の否定とはしていない。

**今回の実装への判断:** compute–位相–uncompute を直接の対角位相へ吸収する着想は、中間値を減らす候補になる。qudit、非局所古典処理、既知 ground state などの前提を除かず、実際の二進ゲート数と全入力作用を検証する必要がある。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## magic:51 — Gaurav Saxena and Gilad Gour. “Quantifying multiqubit magic channels with completely stabilizer-preserving operations”. [Physical Review A 106 , 042422](https://dx.doi.org/10.1103/PhysRevA.106.042422) (2022). [arXiv:2202.07867](http://arxiv.org/abs/2202.07867) .

**一次資料:** https://arxiv.org/pdf/2202.07867

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Actual complete primary-text reading by named collaborating agent; detailed scope and primary-image checks in evidence ledger.

**内容:** 完全 stabilizer-preserving 操作を自由とする動的 magic の資源理論を構成し、単発の費用・蒸留境界と古典シミュレーションを扱う。読んだ公開 v2 には min-relative entropy の faithfulness と full-rank 計算の不整合がある。

**今回の実装への判断:** 広い自由操作集合での上界は、許可された Clifford・測定回路の実装を保証しない。当該の不整合な断言や、誤差制限を外した標本数の constant runtime を、正確なローダー合成へ転用しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

**取得版の注意:** The parent bibliography uses the published title Quantifying multiqubit magic channels with completely stabilizer-preserving operations. The reviewed arXiv:2202.07867v2 PDF, dated 4 July 2022 on its title page and 1 July 2022 in its version header, instead has the title Quantifying dynamical magic with completely stabilizer preserving operations as free. Reading and formula cautions apply to that cached preprint version, not an uninspected corrected publication.

## magic:52 — Arne Heimendahl, Markus Heinrich, and David Gross. “The axiomatic and the operational approaches to resource theories of magic do not coincide”. [Quantum 6 , 878](https://dx.doi.org/10.22331/q-2022-12-22-878) (2022).

**一次資料:** https://arxiv.org/pdf/2011.11651

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Actual complete primary-text reading by named collaborating agent; detailed scope and primary-image checks in evidence ledger.

**内容:** Clifford・安定化子準備・Pauli 測定などで作る操作 SO は、複数量子ビットでは公理的な CSP の真部分集合であると示す。単一 qudit の場合との違いと、測定の構造を明示する。

**今回の実装への判断:** magic を増やさない写像でも、許可ゲートで無料実装できるとは限らない直接的な根拠になる。任意 Boolean 関数を測定・再準備に埋め込む例は coherence を失うため、coherent XOR ローダーの代用にならない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

**取得版の注意:** Cited journal/DOI inconsistent with title-author primary metadata. Primary arXiv and author publication list identify J. Math. Phys. 63,112201 (2022), DOI10.1063/5.0085774; manuscript cites Quantum6,878. Raw citation preserved.

## magic:53 — Ryohei Kobayashi and Guanyu Zhu. “Cross-cap defects and fault-tolerant logical gates in the surface code and the honeycomb floquet code”. [PRX Quantum 5 , 020360](https://dx.doi.org/10.1103/PRXQuantum.5.020360) (2024). [arXiv:2310.06917](http://arxiv.org/abs/2310.06917) .

**一次資料:** https://arxiv.org/pdf/2310.06917

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Actual complete primary-text reading by named collaborating agent; detailed scope and primary-image checks in evidence ledger.

**内容:** cross-cap を含む surface/Floquet code で一定深さの論理 Clifford 操作を構成する。open boundary で元の gauge fixing に戻る工程には O(d) の測定が別途必要になる。

**今回の実装への判断:** 論理操作後に評価で要求される状態へ戻す費用も数える例になる。固有位相 e^(±iπ/4) の相対位相はπ/2なので、その操作を非Clifford T と混同しない。

**留保:** 全文読解は図の全画素確認や全証明の独立再導出を意味しない。

## graphene:1 — R. Bistritzer and A. H. MacDonald, Moire bands in twisted double-layer graphene, Proc. Natl. Acad. Sci. **108** , 30 (2011).

**一次資料:** https://www.pnas.org/doi/10.1073/pnas.1108174108

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Abstract–Discussion, extracted characters 2416–23556; numerical figures not independently digitized.

**内容:** 連続体Diracモデルと三つの層間結合で、微視的に非整合な二層でも小角度の低エネルギーを周期的moiréバンドとして扱う。約1.05度でDirac速度が消失し、狭いバンドと大きい状態密度が現れる。Model/Resultsは計算行列の縮小、層間平行移動を基底位相で除く方法を説明する。

**今回の実装への判断:** 基底と対称性によるモデル縮小の例。固定された75語の厳密XOR表を近似連続体へ置換する根拠にはならない。magic angleは非Clifford magic量と無関係。

**留保:** 相互作用は扱わない。取得HTMLでは表示数式に欠落があるため、全数式を独立検算したとはしない。

## graphene:2 — Y. Cao et al., Correlated insulator behaviour at half-filling in magic-angle graphene superlattices, Nature **556** , 7699 (2018).

**一次資料:** https://arxiv.org/pdf/1802.00553

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main article through Methods, characters 0–21500; supplementary material not read.

**内容:** 約1.1度の二層で半充填の絶縁的輸送を測り、容量測定・量子振動・磁場依存と、狭いバンドで相互作用が優勢になる説明を組み合わせる。Mott-likeな解釈を支持するが、本文は競合する秩序や歪みの可能性も議論する。

**今回の実装への判断:** 物理的モデル選択の資料。ローダーの全アドレス同値性、任意ターゲットXOR、測定枝の位相補正を与えない。

**留保:** 観測と単純な三角格子Hubbard解釈を同一視できない。補足の全解析は未読。

## graphene:3 — Y. Cao, V. Fatemi, S. Fang, K. Watanabe, T. Taniguchi, E. Kaxiras, and P. Jarillo-Herrero, Unconventional superconductivity in magic-angle graphene superlattices, Nature **556** , 7699 (2018).

**一次資料:** https://arxiv.org/pdf/1803.02342v2

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** All extracted preprint text, characters 0–72946, including Methods, Extended Data captions and bibliography; arXiv v2 (2018-05-20). Supplementary animation not viewed.

**内容:** 約1.1度の二層を半充填相関絶縁状態からドープすると最大1.7 Kのゼロ抵抗、臨界電流、磁場抑制が現れる。量子振動とHall密度は小さいFermi面を支持する。Methodsは位相干渉をJosephson経路で説明するが電流分布を一意決定できないと明記し、厳密な原子整合性と連続体近似も区別する。

**今回の実装への判断:** 近似的に滑らかな物性を、離散語表の全入力で成立する恒等式へ変換できない。単一の観測量や位相干渉の署名を、任意ターゲットXORの全演算子検証の代用にしない。

**留保:** 公刊題名と著者公開稿題名が異なる。強結合の解釈と特定のpairing symmetryの実証は同じでなく、本文は追加実験を必要とする。数式OCRの乱れと図・動画未検証がある。

## graphene:4 — Y. Xie et al., Fractional Chern insulators in magic-angle twisted bilayer graphene, Nature **600** , 7889 (2021).

**一次資料:** https://arxiv.org/pdf/2107.10854

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text characters 0–19931; final paragraph re-read at 18800–20550; Methods/supplement not read.

**内容:** 局所圧縮率とStreda関係から八つのFCI状態を同定する。最初の状態は5 Tで出現し、隣接CDWの消失を伴う。磁場が既存ChernバンドのBerry曲率を均一化するという数値・幾何学的説明を提示する。

**今回の実装への判断:** 位相幾何と材料の設計条件。任意の真理値表を低ランク化する定理、ゲート恒等式、anyon braiding回路を提供しない。

**留保:** ゼロ磁場FCIはこの実験の観測結果ではなく将来の提案。スピン構造や準粒子の直接同定も残る。

## graphene:5 — E. Codecido et al., Correlated insulating and superconducting states in twisted bilayer graphene below the magic angle, Sci. Adv. **5** , eaaw9770 (2019).

**一次資料:** https://arxiv.org/pdf/1902.05151

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** All extracted preprint text, characters 0–20138; opening re-read to repair truncated combined output.

**内容:** 0.93度の試料で半充填の相関絶縁状態と近傍の超伝導、さらに±5電子/単位胞の抵抗ピークを報告する。改良連続体計算は主magic angle以下でも狭いバンドと高エネルギー側の平坦領域を示す。

**今回の実装への判断:** 探索を単一パラメータ点に限定しない発想は参考になるが、物理角度範囲をJ幅の改善境界へ換算する根拠はない。

**留保:** ±5の新しい絶縁状態の解釈は暫定的。二段階転移や不均一性の代替説明があり、図を独立数値化してはいない。

## graphene:6 — A. L. Sharpe, E. J. Fox, A. W. Barnard, J. Finney, K. Watanabe, T. Taniguchi, M. A. Kastner, and D. Goldhaber-Gordon, Emergent ferromagnetism near three-quarters filling in twisted bilayer graphene, Science **365** , 6453 (2019).

**一次資料:** https://arxiv.org/html/1901.03520

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text characters 0–21558; supplement not read.

**内容:** 3/4充填近傍で大きい異常Hall応答、磁場履歴依存、非局所輸送、微小DC電流での磁化反転を観測する。論文はincipient Chern insulatorという解釈を提示する。

**今回の実装への判断:** 物理実験での不完全な署名の扱いが参考になる。出力の一部一致や統計一致を厳密な量子oracle同値と見なす根拠にはならない。

**留保:** Hall抵抗は量子化せず散逸が残る。非局所信号も理想的QAHの実証ではなく、バルクや磁区の寄与を考慮する。

## graphene:7 — Y.-H. Zhang, D. Mao, and T. Senthil, Twisted bilayer graphene aligned with hexagonal boron nitride: Anomalous Hall effect and a lattice model, Phys. Rev. Res. **1** , 3 (2019).

**一次資料:** https://arxiv.org/html/1901.08209

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text characters 0–23823; supplemental derivations not read.

**内容:** hBN整列によるC2対称性破れがDirac交差を開き、谷ごとに±1のChernバンドを生む。C2T保護が外れると伝導・価電子帯を合わせたWannier構成が可能で、拡張Hubbard/Haldane格子モデルを得る。3/4充填のChern絶縁体と圧縮可能なcomposite Fermi liquidを区別して提案する。

**今回の実装への判断:** 基底変換を使える条件を先に確定するという具体的教訓。GF(2)出力変換に使うなら固定語表で可逆性・再構成を別証明する必要があり、本論文だけでは費用減は出ない。

**留保:** 最初の解析ではhBNの非整合moiré項を弱いとして落とす。単一伝導帯射影の極限と実験のU~W>gapは違うことを明示する。

## graphene:8 — G. Chen et al., Signatures of tunable superconductivity in a trilayer graphene moiré superlattice, Nature **572** , 7768 (2019).

**一次資料:** https://arxiv.org/pdf/1901.04621

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text 0–18552 and Methods 23952–27000; separate supplement not read.

**内容:** ABC三層/hBNで変位場により狭い孤立バンドを調整し、1/4充填Mott状態の近傍に超伝導の署名を報告する。温度・電流・磁場依存と、金属/絶縁体/候補超伝導間の変化を調べる。

**今回の実装への判断:** 可調整の物性モデル。量子回路の測定後位相消去や表読み出しの構成法はない。

**留保:** 本文はcandidate/signaturesと表現し、残留抵抗や不均一性、未説明の磁場挙動も記載する。

## graphene:9 — H. Kim et al., Imaging inter-valley coherent order in magic-angle twisted trilayer graphene, Nature **623** , 942 (2023).

**一次資料:** https://arxiv.org/html/2304.10586

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text and Methods characters 0–34551; long supplementary theory not read.

**内容:** STMで低歪み三層のKekulé格子三倍化とmoiré尺度の変調を測る。Fourierフィルタと原子位置を整列した自己相関で変調波数を抽出し、ドープ依存のincommensurate Kekulé spiralに整合する結果を得る。ゼロ磁場の信号から少なくともKramers-IVC候補を排除する。

**今回の実装への判断:** 有限語表の相関を調べる探索の着想にはなるが、Fourierピークの近似的一致をbit単位の恒等式と置換できない。

**留保:** 理論比較は歪み・Hartree変形等に依存する。画像のパターン同定は量子状態全体のトモグラフィーではない。

## graphene:10 — H. Kim, Y. Choi, C. Lewandowski, A. Thomson, Y. Zhang, R. Polski, K. Watanabe, T. Taniguchi, J. Alicea, and S. Nadj-Perge, Evidence for unconventional superconductivity in twisted trilayer graphene, Nature **606** , 7914 (2022).

**一次資料:** https://arxiv.org/html/2109.12127

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Preprint main text characters 0–23603; supplementary Methods not read.

**内容:** STM/STSで鏡映対称領域、flat/Diracバンド、充填依存のHartree変形と超伝導的coherence peakを観測する。U形からV形のトンネルスペクトルを、単一nodal秩序のBEC–BCS転移などと比較する。

**今回の実装への判断:** 弱く結合したsectorの存在を物理的に検証する例。任意入力での出力sector分離を保証せず、ローダー回路削減は導かない。

**留保:** ペアリング機構は確定しない。低エネルギーphononや複数秩序の代替説明を残す。公開プレプリント題名はSpectroscopic Signatures...。

## graphene:11 — J. M. Park, Y. Cao, K. Watanabe, T. Taniguchi, and P. Jarillo-Herrero, Tunable strongly coupled superconductivity in magic-angle twisted trilayer graphene, Nature **590** , 7845 (2021).

**一次資料:** https://arxiv.org/html/2012.01434v1

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Scientific text characters 0–61570 (all main text, Methods 1–8, Extended Data captions and acknowledgements). Site feedback footer excluded. arXiv v1 (2020-12-02); references render as unresolved citation keys.

**内容:** 鏡映対称な三層のflat bandとDirac bandの共存を利用し、変位場で混成・超伝導を調整する。zero-D連続体モデルは鏡映セクターに分解し、一方を有効角度が1/√2の二層へ写す。二キャリア/単位胞由来の超伝導、van Hove境界、GL長が粒子間隔に近づくこと、TBKT/TFが0.1以上になることを報告する。

**今回の実装への判断:** 対称性によるブロック分解の条件を明示する好例。ただし実数/複素数の層基底と√2を用いる変換はCNOTによるGF(2)出力基底ではなく、対称性を破る項を任意に省けない。

**留保:** Methodsのモデルは外側二層間の直接結合等を捨て、電場screeningの完全な自己無撞着計算は範囲外。弱い超伝導境界には例外も記載される。抽出HTMLの引用文献リストは欠落し、数式や単位の変換乱れが残る。

## graphene:12 — D. Halbertal et al., Unconventional non-local relaxation dynamics in a twisted trilayer graphene moiré superlattice, Nat. Commun. **13** , 7587 (2022).

**一次資料:** https://www.nature.com/articles/s41467-022-35213-5

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Abstract–Methods/Data availability characters 2986–42259; page recommendations excluded; supplementary material not read.

**内容:** 実際の対象はtwisted double trilayer。近接場・STMとDFTを照合し、一層の全体滑りによってABABAB/BCBACA領域が形成される説明を得る。一部の局所エネルギー増を、別領域の拡大と全体の弾性/積層エネルギー減が補う。Methodsは32積層候補と連続体緩和を説明する。

**今回の実装への判断:** 局所コスト増も全体で評価する原則は共同合成に整合する。ただしエネルギー最小化と公式λQTは別目的で、準備・復元・全バッチを含む実ゲート集計が必要。

**留保:** 数値最適化は特定の力学モデルによる。GSFEの一部は近い関数への制約付きフィットで近似する。

## graphene:13 — I. M. Craig, M. Van Winkle, C. Groschner, K. Zhang, N. Dowlatshahi, Z. Zhu, T. Taniguchi, K. Watanabe, S. M. Griffin, and D. K. Bediako, Local atomic stacking and symmetry in twisted graphene trilayers, Nat. Mater. 323 (2024).

**一次資料:** https://arxiv.org/html/2303.09662

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text 0–22916 and Methods/Data/Code 25252–31655; supplement not read.

**内容:** 干渉4D-STEMで層界面を選択的に調べ、AAAの縮小やAtA/AtBの面積比を直接測定する。わずかな非整列でAtBがほぼ消えるという従来像に対し、かなりのAtB領域が残る結果を示す。Methodsはマスク、強度閾値、平滑化、角度/歪み推定を説明する。

**今回の実装への判断:** 見かけの対称性を別の測定法で監査する教訓。全アドレスと全ターゲットの厳密照合の代わりにはならない。

**留保:** 空間分解能やGaussian平滑化、強度の混入、運動学的緩和不足の限界を記す。

## graphene:14 — C. Shen, P. J. Ledwith, K. Watanabe, T. Taniguchi, E. Khalaf, A. Vishwanath, and D. K. Efetov, Dirac spectroscopy of strongly correlated phases in twisted trilayer graphene, Nat. Mater. **22** , 316 (2023).

**一次資料:** https://arxiv.org/pdf/2204.07244

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text characters 0–21320; supplementary theory/Methods not read.

**内容:** Dirac coneのLandau準位とflat-band gapの交差を用いて、隠れた相関gapの大きさとChern数を推定する。整数充填のC=0状態、分数充填CDW候補、変位場によるhybridization/相転移を解析する。

**今回の実装への判断:** 補助sectorで本体を診断する考え方は検証設計に類似するが、可逆補助レジスタの準備とcleanupを省ける定理ではない。

**留保:** 強くhybridizeすると測定手法の前提が失われることを本文が明示する。抽出数式には添字欠落があり式の再実装には原PDF確認が必要。

## graphene:15 — G. Chen et al., Evidence of a gate-tunable Mott insulator in a trilayer graphene moiré superlattice, Nat. Phys. **15** , 237 (2019).

**一次資料:** https://arxiv.org/pdf/1803.01985

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main article characters 0–18812; remaining figure captions and separate SI not read.

**内容:** ABC三層/hBNで1/4・1/2充填の絶縁的輸送が変位場で強化される結果を報告する。低エネルギー二成分Hamiltonianとmoiré potentialを対角化し、帯域幅とCoulomb反発の競合で説明する。

**今回の実装への判断:** 固定物理問題を別の有効模型に置換するなら誤差評価が必要。厳密ローダーのbit出力を変更する許可は与えない。

**留保:** 輸送gapとU−Wの推定は定性的対応である。取得PDFテキストの数式には欠落が多い。

## graphene:16 — M. Fujimoto, N. Nakatsuji, A. Vishwanath, and P. Ledwith, Four Moiré materials at One Magic Angle in Helical Quadrilayer Graphene, arxiv:2510.02444 (2025).

**一次資料:** https://arxiv.org/html/2510.02444

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text characters 0–30440; Appendices A–E not read.

**内容:** 四層の同方向twistを理論解析し、緩和後の四種の領域がほぼ共通の約2.3度で狭いバンドを持つと予測する。Type-Iでは±2 Chern基底、Type-IIでは別の量子幾何とdomain-wall networkを論じる。

**今回の実装への判断:** 共通パラメータで複数sectorを整理する発想のみ。本文のTは量子幾何のtrace-condition deviationであり、Tゲート数ではない。

**留保:** 局所周期モデルと緩和計算に基づく予測。正確なvortexabilityはchiral limitで、実材料のFCIや超伝導を実証したものではない。

## graphene:17 — D. Guerci, Y. Mao, and C. Mora, Nature of even and odd magic angles in helical twisted trilayer graphene, arxiv: 2308.02638 (2023).

**一次資料:** https://arxiv.org/html/2308.02638

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Sections I–V and acknowledgments, characters 0–52946; appendices not read.

**内容:** chiral連続体模型の零モードを解析的に構成する。奇数magic angleではChern 2と−1の二平坦帯、偶数では四平坦帯とDirac coneが現れる。直交性、Wronskianの消失、零点の次数から生成元の数を説明し、C3z/C2yTと粒子正孔対称性の役割を分離する。

**今回の実装への判断:** 核/商空間の証明方法は参考になるが、GF(2)多出力テンソルrankや乗法複雑度への移植定理はない。低ランクの発見だけで実CCXが減るともいえない。

**留保:** rankは複素波動関数の位置依存layer空間での次元。AA結合を戻すと有限帯域が生じ、粒子正孔対称性破れ等も別途解析される。

## graphene:18 — C. Yang, J. May-Mann, Z. Zhu, and T. Devakul, Multi-moiré trilayer graphene: Lattice relaxation, electronic structure, and magic angles, Phys Rev B **110** , 115434 (2024).

**一次資料:** https://arxiv.org/html/2310.12961

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Sections I–IV, characters 0–44951; appendices not read.

**内容:** 二角度の三層を緩和と局所連続体で系統探索する。最初のmagic angle近傍では比±1、+1/2で周期的domain、それ以外の調べた単純比では主に準結晶となる。相対shiftを固定した局所Hamiltonianやshift平均DOSでmagic lineを推定する。

**今回の実装への判断:** 高側アドレスに応じた低側shift探索に形式的な類似はある。ただし各shiftの順列作用を厳密に戻し、出力tagも含める必要があり、物理近似は使えない。

**留保:** 整合近似を作る微小strainは必ずしも実在しない。超moiré coherenceによる小gapを捨て、粒子正孔非対称も近似する。

## graphene:19 — Y. Liu et al., Electronic Correlations in Rhombohedral Graphene at Atomic Scale, Phys Rev Lett **135** , 156401 (2025).

**一次資料:** https://arxiv.org/pdf/2412.06476v1

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** All extracted preprint text, characters 0–46277, including main, Methods, Extended Data captions and references. arXiv v1 (2024-12-09); arXiv metadata explicitly links published DOI.

**内容:** 著者公開稿は四層rhombohedral grapheneの電荷中性点で最大17 meVの相関gapを報告し、磁場・dopingによる抑制、intervalley干渉の不在、欠陥散乱をLAF解釈と結びつける。三層のCu tip測定はgapを示さず、Au tipによる外因的電場で大きいgapが生じ得ると比較する。欠陥近傍の三回対称束縛状態の解釈には追加のspin-sensitive検証を求める。

**今回の実装への判断:** 測定・モデルの外因と固有効果を切り分ける実例。LAFやSSHの物理的類推は固定語表の可逆乗法回路の恒等式ではない。実CCX削減は導いていない。

**留保:** 公刊版題名はこの項目名、読んだ稿の題名はReal-space study of zero-field correlation in tetralayer rhombohedral graphene。公刊要旨の最大gapは19 meVで、公開稿の17 meVと版差がある。公刊本文そのものは取得できず、全図の独立検査もしていない。

## graphene:20 — Z. Lu, T. Han, Y. Yao, A. P. Reddy, J. Yang, J. Seo, K. Watanabe, T. Taniguchi, L. Fu, and L. Ju, Fractional quantum anomalous Hall effect in multilayer graphene, Nature **626** , 759 (2024).

**一次資料:** https://arxiv.org/pdf/2309.17436

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Entire fetched 35117-character preprint, including main text, captions, references and acknowledgements; separately cited Methods and Extended Data were not included or read.

**内容:** rhombohedral五層/hBNで整数および六つの分数充填にHall plateauと縦抵抗dipを観測し、磁気履歴がゼロ磁場を囲むことやStreda傾斜を併せてFQAHEを示す。1/2充填では抵抗dipがなく連続的Hall応答が残り、CFLに類似する挙動と解釈する。変位場で金属・絶縁相へ遷移する。

**今回の実装への判断:** トポロジカル計算の候補物理系であり、braidingを実装・検証した論文ではない。今回のゲート集合で任意XOR oracleを安価に合成する手法やToffoli数の改善を与えない。

**留保:** 概観の相図は±0.1 Tで対称化しており、ゼロ磁場の主張には別途hysteresis測定を用いる。CFL/相転移の詳細検証と非Abelian braidingは将来課題。Methods/Extended Data全体は未読、式のOCRに欠落がある。

## graphene:21 — Z. Guo, X. Lu, B. Xie, and J. Liu, Fractional Chern insulator states in multilayer graphene moiré superlattices, Phys. Rev. B **110** , 075109 (2024).

**一次資料:** https://arxiv.org/html/2311.14368v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** All main text and Methods, characters 0–59285; Supplementary Information S1–S6 and bibliography after it not read. arXiv v2 (2023-12-12).

**内容:** 高エネルギーのCoulomb相互作用を摂動RGで繰り込み、低エネルギー24バンドのHFを解き、ν=1の二つの競合HF状態から孤立帯を作り、hole doping後のED結果を比較する。3分の2と5分の3でFCI候補を得る。粒子・正孔変換後に異なるHF真空のエネルギー定数を保存しないと、候補間比較が誤ることをMethodsと式(6)–(7)で説明する。

**今回の実装への判断:** 比較の基準状態と定数項を揃える手順は費用監査に参考となる。ただしエネルギー窓の射影やHF平均場で語表を近似することは許されず、32ターゲット全体・HMR枝の相対位相を保つ実装証明は別途必要。

**留保:** EDは有限20/24/27サイトかつHF孤立帯への射影後の厳密解で、全元模型の厳密解ではない。12充填価電子帯を凍結する根拠は80–100 meV gapと約20 meV相互作用の分離。FCI判定のgap/spread閾値や有限サイズcross-overを明記する。公刊題名は多層、読んだv2題名はpentalayer。

## graphene:22 — J. Dong, T. Wang, T. Wang, T. Soejima, M. P. Zaletel, A. Vishwanath, and D. E. Parker, Anomalous Hall Crystals in Rhombohedral Multilayer Graphene. I. Interaction-Driven Chern Bands and Fractional Quantum Hall States at Zero Magnetic Field, Phys. Rev. Lett. **133** , 206503 (2024).

**一次資料:** https://arxiv.org/html/2311.05568

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text characters 0–25165; long appendices not read.

**内容:** 自己無撞着Hartree–Fockで相互作用起源のChern bandとanomalous Hall crystalを得て、射影したbandのED/DMRGで2/3 FQAHを支持する。moiré potentialを消してもSCHFで秩序が残るため、相互作用が周期性と時間反転を同時に破る機構を提案する。

**今回の実装への判断:** モデルと対照計算を分ける良い例。EDのexactは射影済み模型の有限系内であり、全語表の厳密性や汎用oracleの証明にはならない。

**留保:** 7伝導帯への射影、spin/valley偏極を仮定。分数量子状態の計算はν=1のSCHF最低bandに制限し、著者自身がFCIを有利にするbiasとHartree–Fockの結晶化過大評価を記す。

## graphene:23 — S. Zhang, B. Xie, Q. Wu, J. Liu, and O. V. Yazyev, Chiral Decomposition of Twisted Graphene Multilayers with Arbitrary Stacking, Nano Lett. **23** , 2921 (2023).

**一次資料:** https://arxiv.org/html/2012.11964

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text characters 0–25037; separate supplementary material not read; 2020 preprint of 2023 publication.

**内容:** 任意積層N+Mをmoiré部分と残りのchirality-J doubletへ分ける規則を示す。chiral limitの低エネルギーHamiltonianを直和として扱い、A-ABAとA-ABACの一次/二次摂動でDirac/二次doubletを具体的に導く。変位場で平坦帯を分離しChern数を定義できる場合も解析する。

**今回の実装への判断:** 今回最も形式的に近いのは構造を基に分割して再構成する点。回路へ使うには有限語表の依存グラフで厳密な不変部分を証明する必要がある。論文中のJはchiralityで、バッチ幅Jとは別。

**留保:** AA hoppingゼロ、nearest-neighbor層間結合、magic angleおよび低エネルギー射影という条件付き。全Hilbert空間の任意ユニタリの直和分解ではない。

## graphene:24 — Y. Park, Y. Kim, B. L. Chittari, and J. Jung, Topological flat bands in rhombohedral tetralayer and multilayer graphene on hexagonal boron nitride moiré superlattices, Phys Rev B **108** , 155406 (2023).

**一次資料:** https://arxiv.org/html/2304.12874

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Sections I–V characters 0–49791; appendices not read.

**内容:** 四層/hBNから八層までの連続体模型で帯域、gap、valley Chern数、局所密度を探索する。電場・twist・基板配向で局在と帯域が変わり、狭いbandでも実空間に広がる場合がある。band overlapによるscreeningを加えると相関有望領域も変わる。

**今回の実装への判断:** 帯域の平坦さ、位相指標、波動関数の局在はそれぞれ異なる尺度。どれも二値表の低ランクやゲート数と同一視しない。

**留保:** Ueff/Wは相関相の候補指標で、相関基底状態を全て解いたものではない。抽出本文には添字等の誤植があり数値式を移植していない。

## graphene:25 — Z. Dong, L. Levitov, and A. V. Chubukov, Superconductivity near spin and valley orders in graphene multilayers, Phys. Rev. B **108** , 134503 (2023).

**一次資料:** https://arxiv.org/html/2306.11005

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Sections I–VI and acknowledgments, characters 0–59130; bibliography not read as separate full texts.

**内容:** 二谷のU1/U2/U3相互作用からspin/valley秩序近傍のpairing vertexをdiagram級数で求める。FM+/FM−ではそれぞれtriplet/singletの引力、CDWではsinglet引力等を得る。小さいU3でも有限次数で打ち切ると発散形を誤り、無限級数の和が必要であると示す。

**今回の実装への判断:** 共通中間式の解析的因数化という一般的着想はあるが、実数/複素数のdiagram和をGF(2)可逆演算へ置換する規則は与えない。

**留保:** 相互作用とpolarization bubbleを運動量に対して定数とする近似。SDWの非引力結論もその一定gap仮定に限定され、運動量依存を戻すと変わり得る。

## graphene:26 — Y. Zhang et al., Promotion of superconductivity in magic-angle graphene multilayers, Science **377** , 6614 (2022).

**一次資料:** https://arxiv.org/html/2112.09270

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text and Methods characters 0–25247; extensive supplement not read.

**内容:** WSe2上の交互twist三・四・五層で相関相と超伝導を測定し、層数増加で超伝導の充填範囲が広がる。五層ではflat bandだけの単純な充填像を超え、Hartree shiftや分散bandとのhybridizationの役割を議論する。

**今回の実装への判断:** 単純なブロック分解の適用範囲を調べる教訓。材料層の追加が有利でも、公式λQTで量子ビット追加が有利になるとは限らない。

**留保:** 非相互作用でのTBG sector分離が実際の高充填まで有効とは限らない。層依存のchargeや遠方層結合で、鏡映対称でもmixingする。公開題名はAscendance...。

## graphene:27 — S. Zhang, X. Dai, and J. Liu, Spin-Polarized Nematic Order, Quantum Valley Hall States, and Field-Tunable Topological Transitions in Twisted Multilayer Graphene Systems, Phys Rev Lett **128** , 026403 (2022).

**一次資料:** https://arxiv.org/html/2101.04711

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** Main text characters 0–24195; supplementary analysis not read.

**内容:** 二層–一層および二層–二層をHartree–Fockで解析し、半充填でspin偏極nematic絶縁相を予測する。intra-valley Coulombのみで近接するvalley偏極との縮退をon-site Hubbard項が分裂させ、弱い磁場のorbital Zeeman/密度補正がQAH相へ競合する。

**今回の実装への判断:** 一見小さな項でも縮退を解く例。ローダーのtag、復元、HMR位相など小コスト項を省略しない動機にはなるが、直接の合成法ではない。

**留保:** 模型の基底状態はHF近似下での結果。谷間の長距離相互作用と弱磁場Landau量子化を省くなど適用条件を持つ。

## graphene:28 — J. Liu, Z. Ma, J. Gao, and X. Dai, Quantum Valley Hall Effect, Orbital Magnetism, and Anomalous Hall Effect in Twisted Multilayer Graphene Systems, Phys Rev X **9** , 031021 (2019).

**一次資料:** https://journals.aps.org/prx/pdf/10.1103/PhysRevX.9.031021

**読解状態:** 取得した本文・付録の抽出テキストを全読

**実読範囲:** Entire 14-page extracted paper, characters 0–64533, including Appendices A–C and references; equations have substantial PDF extraction damage.

**内容:** chiral積層M+Nの二平坦帯とChern-number hierarchyを提案し、より現実的なtight-bindingとの比較を行う。Appendix Aは基底変更と零pseudo-Landau-level射影、Bはchiralityに応じたChern和、Cは局所電流の計算法を与える。

**今回の実装への判断:** 正確な基底変換と部分空間への射影を区別する資料。全ターゲットXOR oracleでは射影やgarbageの廃棄を認められないため、同じ縮小は適用できない。

**留保:** Appendix Aは高いpseudo-Landau levelを捨て、連続体結合も線形化する。遠方hoppingでchiral対称性が破れ、hierarchyは全積層で厳密には残らないことを本文が明示する。数式OCRは独立検算不能箇所あり。

## graphene:29 — C. Xu and L. Balents, Topological Superconductivity in Twisted Multilayer Graphene, Phys. Rev. Lett. **121** , 087001 (2018).

**一次資料:** https://arxiv.org/html/1803.08057v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、節番号のない本文全体（単一バンドSU(4) Hubbard模型、超交換・Fierz分解、Hund結合、A/B候補、時間反転・半量子渦・端状態、結論とv2追加議論）、謝辞まで。

**内容:** 単一三角格子バンド、谷間散乱の抑制、反強磁性的超交換と正のHund結合を仮定して、谷一重項・スピン三重項d波の二候補を得る。Aは時間反転を破るchiral状態、Bは時間反転を保つhelical状態で、平均場では縮退し優劣を決めていない。2DかつSU(2)対称なら有限温度で通常の秩序は崩れ、charge-4eの代数秩序とhc/(4e)半渦を論じる。

**今回の実装への判断:** グラフェンの電子構造・超伝導・相関状態を扱う研究であり、coherent XORローダー、CCZ/Toffoli分解、HMR補正または物理qubit削減の実装は提示しない。今回の回路最適化への直接適用は導けない。

**留保:** 単一バンド模型の有効範囲が重要で、v2末尾は二本の絡み合ったバンドがある場合に単純三角格子記述が不十分と明記。A/Bの選択、無秩序・磁場などは今後の課題。図説明は読んだが原画像・独立再導出は未実施。参考文献一覧は今回の範囲外。

## graphene:30 — X.-F. Zhou, Y.-W. Liu, C.-Y. Hao, C. Yan, Q. Zheng, Y.-N. Ren, Y.-X. Zhao, K. Watanabe, T. Taniguchi, and L. He, Coexistence of reconstructed and unreconstructed structures in the structural transition regime of twisted bilayer graphene, Phys Rev B **107** , 125410 (2023).

**一次資料:** https://arxiv.org/pdf/2209.14730

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。取得した26,629文字全部：Abstract、節番号のない主本文、結論、謝辞、参考文献43件、Fig.1–4のキャプション。独立Methods節はなく、製作・解析の詳細Methodsは別Supplemental Materialへ参照。

**内容:** 0.10–3.59度のTBGをhBN/WSe2上で調べ、60試料以上のDW/AA高さ比とVHSの空間分布から、約0.90度未満の再構成、約1.80度超の剛体、その間の二構造共存を報告する。AA領域はVHS空間分布のGaussian幅から推定し、stackingエネルギー比較は原子数固定・既報の領域面積・層間隔3.2–3.6Åに基づく。

**今回の実装への判断:** グラフェンの電子構造・超伝導・相関状態を扱う研究であり、coherent XORローダー、CCZ/Toffoli分解、HMR補正または物理qubit削減の実装は提示しない。今回の回路最適化への直接適用は導けない。

**留保:** 再構成と剛体の共存をエネルギーの釣合いで解釈するが、全弾性エネルギーの独立計算や普遍的角度境界の証明ではない。Supplemental Materialの製作Methods・追加データ・解析詳細は本キャッシュになく今回未読。原図画像・生データの再解析は未実施。

## graphene:31 — C.-Y. Hao, Z. Zhan, P. A. Pantaleón, J.-Q. He, Y.-X. Zhao, K. Watanabe, T. Taniguchi, F. Guinea, and L. He, Robust flat bands in twisted trilayer graphene moiré quasicrystals, Nat. Commun. **15** , 8437 (2024).

**一次資料:** https://www.nature.com/articles/s41467-024-52784-7

**読解状態:** 本文文章の全節を読解（埋め込み表・数式に取得欠落）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、Introduction、Resultsの全4小節、Discussion、Methods全4小節（製作、STM、TB/LDOS、continuum/Hartree）、Data/Code availabilityまでを通読。

**内容:** 五つのTTG角度対で、局所C3対称性、stacking、flat-bandの層別局在、moiré間結合をSTM/STSとTB/continuum/Hartree計算で比較する。78K・5mV変調のSTS幅には熱・歪み・再構成・相互作用の寄与があり、理論帯域より広い。大角度側は二つのTBGの弱い重ね合わせ、小角度の一部は三層へ広がる強い混成となり、Hartree計算は孤立した狭いbandを持つsample3/4に適用する。

**今回の実装への判断:** グラフェンの電子構造・超伝導・相関状態を扱う研究であり、coherent XORローダー、CCZ/Toffoli分解、HMR補正または物理qubit削減の実装は提示しない。今回の回路最適化への直接適用は導けない。

**留保:** 本文全節とMethodsは取得済みで通読したが、Table1は外部リンクだけで表セルが抽出されていない。全原図画像と別Supplementary Notes/Figuresは今回未読。無限個のmagic-angle pairは理論の主張を五試料で支持するもので、無限個を実測したわけではない。

## graphene:32 — O. Aguilar-Spíndola, A. Rubio-Ponce, F. López-Urías, and F. Sánchez-Ochoa, Electronic and optical properties in helical trilayer graphene under compression, Phys Chem Chem Phys **27** , 11541 (2025).

**一次資料:** https://pubs.rsc.org/en/content/articlehtml/2025/cp/d5cp00337g

**読解状態:** 本文文章の全節を読解（埋め込み表・数式に取得欠落）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、§1 Introduction、§2 Computational methodology、§3.1–3.3、§4 Conclusions、著者貢献・Data availability・利益相反・謝辞冒頭まで。

**内容:** 21.78度・294原子の三つのcommensurate HTG配置をPBE/SIESTAで比較し、層間距離を固定して面内座標を緩和する。高圧縮で電子正孔非対称・低エネルギーDOSと光学応答が増強するが、光学計算は単粒子・垂直interband遷移でDrude成分を除外する。圧力換算は二層の既報パラメーターによる概算で、低角度magic HTGの直接計算ではない。

**今回の実装への判断:** グラフェンの電子構造・超伝導・相関状態を扱う研究であり、coherent XORローダー、CCZ/Toffoli分解、HMR補正または物理qubit削減の実装は提示しない。今回の回路最適化への直接適用は導けない。

**留保:** 本文の文章と全節は読了。式(3)–(6),(8),(9)および一部の式中項が外部画像で、抽出本文には内容がないため数式全体の読了とはしない。別ESI・原図画像・DFT再計算は未実施。磁性相転移は高DOSからの可能性の指摘で実証ではない。

## graphene:33 — S. Niu, J. Alicea, D. N. Sheng, and Y. Peng, Quantum Anomalous Hall Effects and Emergent SU(2) Hall Ferromagnets at Fractional Filling of Helical Trilayer Graphene, Phys Rev Lett **135** , 146505 (2025).

**一次資料:** https://arxiv.org/html/2505.24146v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、Introduction、モデル/投影Hamiltonian、QHC、FCI、QHF、global phase diagram、Summary、謝辞の全主本文。Figures1–4の抽出キャプションも読了。

**内容:** hBNを模した層別sublattice potential、固定twist1.44度・誘電率4で|C|=2バンドを分離し、flavor偏極を仮定した有限サイズEDを行う。ν=2/3は√3×√3の電荷秩序Hall結晶、1/3はHalperin(112)型FCI、1/2は準縮退する擬スピン強磁性を予測する。三flavorが満たされた3+νではHartreeによる帯域縮小が相を安定化し、SU(2)量子数は厳密でなく数%の誤差を伴う近似対称性として示される。

**今回の実装への判断:** グラフェンの電子構造・超伝導・相関状態を扱う研究であり、coherent XORローダー、CCZ/Toffoli分解、HMR補正または物理qubit削減の実装は提示しない。今回の回路最適化への直接適用は導けない。

**留保:** 有限サイズ・単一バンド投影・flavor偏極・基板potentialに依存する予測で、観測された実験相の確定同定ではない。補足I–Vにあるcluster詳細・PES・擬スピン構成・pair correlationの全検査は今回未読。全図画像、ED再実行、熱力学極限の独立検証は未実施。

## graphene:34 — J. C. Hoke, Y. Li, Y. Hu, J. May-Mann, K. Watanabe, T. Taniguchi, T. Devakul, and B. E. Feldman, Imaging supermoiré relaxation in helical trilayer graphene, Nat. Mater. (2026). https://doi.org/10.1038/s41563-025-02423-3

**一次資料:** https://arxiv.org/html/2410.16269v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、Introduction、電子構造と格子緩和、実空間のsupermoiré観測、domain wallの伝導、磁場応答、Conclusion、謝辞・著者貢献・Data availability、Methods全3小節（試料製作、SET測定、twist angle決定）。抽出された主図キャプションも通読。

**内容:** 約1.45度のHTGを走査SETで測定し、ν=±4の単一対の非圧縮ピークと空間像から、大きなmoiré周期domainへの緩和を支持する。thermal cycling後にsupermoiréの面積・形状が変わり、moireの有効twist角は保たれるため、微小な層間strainへの高感度と整合する。ACとDCの応答差からdomain wallの相対的な高伝導を示すが、著者自身が測定は相対伝導度を調べるもので境界のtopologyを直接判定しないと明記する。MethodsではSETの有限径・高さ、測定温度と周波数、chemical potential gapのfit、Landau levelからの密度校正を説明し、推定角は緩和後の有効moiré角である。

**今回の実装への判断:** グラフェンの電子構造・超伝導・相関状態を扱う研究であり、coherent XORローダー、CCZ/Toffoli分解、HMR補正または物理qubit削減の実装は提示しない。今回の回路最適化への直接適用は導けない。

**留保:** 単一非圧縮ピークは緩和の証拠だが、緩和前の二つのtwist角を個別に決める測定ではない。非magic角試料で中間充填の相関gapは観測されず、有限磁場の多くの構造は単粒子理論でも説明される。境界のbackscattering保護や絶対伝導度は未実証。Supplementary I–VI、Extended Dataの全図・生データ、原画像の独立検査は今回未読・未実施。

## graphene:35 — L.-Q. Xia et al., Topological bands and correlated states in helical trilayer graphene, Nat. Phys. **21** , 239 (2025).

**一次資料:** https://arxiv.org/html/2310.12204 / https://arxiv.org/html/2310.12204v1

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、IntroductionからOutlookまでの主本文全節（HTG、相関状態、異常Hall効果、電場駆動遷移、Chern domain、length scale）、Methods .1–.13全小節、謝辞・著者貢献・Data availabilityまで。主図キャプションと本文中に抽出された数式も通読。

**内容:** 約1.8度の複数HTG試料で、電子側の整数・分数充填に抵抗異常と非量子化の異常Hall効果を観測し、緩和した局所domainのvalley Chern bandと対比する。ν=2/3の分数充填AHEはFCIの可能性を示す一方、topological charge density waveも候補として残す。電場によるgapの閉鎖・再開はtopological transitionを示唆し、Chern mosaicの履歴はdomainごとの磁化を用いて説明するが、著者は説明の未完性を認める。Methodsには対称化・密度校正・Curie推定・二中心bandに投影したHF・磁化模型・4D configuration-space弾性緩和が含まれ、HFの秩序/gap過大評価とparticle-hole非対称の未説明部分を明記する。

**今回の実装への判断:** グラフェンの電子構造・超伝導・相関状態を扱う研究であり、coherent XORローダー、CCZ/Toffoli分解、HMR補正または物理qubit削減の実装は提示しない。今回の回路最適化への直接適用は導けない。

**留保:** AHEは量子化されておらず、ν=2/3のFCI確定やdomain-wall networkの直接画像化とは区別する。Curie解析はHall抵抗を磁化proxyに用い、磁化反転の一部計算は剛体band shiftの模型である。Methods全13小節は読了したが、参照されるExtended Data Fig.1–12とTable1–2の全内容、別補足、原図画像の独立検査は今回未読。v1から出版版への変更は今回調査していない。

## graphene:36 — T. Devakul, P. J. Ledwith, L.-Q. Xia, A. Uri, S. C. de la Barrera, P. Jarillo-Herrero, and L. Fu, Magic-angle helical trilayer graphene, Sci. Adv. **9** , eadi6063 (2023).

**一次資料:** https://arxiv.org/html/2305.03031 / https://arxiv.org/html/2305.03031v1

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、導入部、§I Reconstruction、§II Electronic structure、§III Chiral limit、§IV Correlated states、§V Discussion、謝辞まで。本文内のTable1–2、主図キャプション、抽出数式を含む。このv1に独立Methods/Appendix節はない。

**内容:** 格子緩和によりHTGが局所的にC2zを破るh/反転h domainへ分かれ、相反するChern数を持つ孤立した狭帯域が生じると予測する。局所周期BM模型のchiral limitでは特定magic angleで厳密なflat bandとholomorphicな理想量子幾何を構成し、現実的corrugationでは厳密flatではない近似理想bandを得る。Jastrow型状態が厳密なground stateとなる主張はflat band、短距離に投影した相互作用、空真空基準のnormal orderingなどの条件付きであり、現実的長距離Coulomb下のFCI安定性は別の多体検証を要する。微小strainで巨大な単一domainを作る案は可能性の提案で、実験的達成ではない。

**今回の実装への判断:** グラフェンの電子構造・超伝導・相関状態を扱う研究であり、coherent XORローダー、CCZ/Toffoli分解、HMR補正または物理qubit削減の実装は提示しない。今回の回路最適化への直接適用は導けない。

**留保:** 局所周期近似とcontinuum模型パラメーターに依存し、全原子緩和の全効果を定量的に含む模型ではない。整数強磁性の厳密固有状態と実際のground stateは同義ではなく、分散・Hartree項・競合秩序に留保がある。今回読んだv1には独立Methods/Appendix節がなく、出版版やPMCの補足を全読したとは扱わない。原図画像・独立解析/数値再実行は未実施。

## graphene:37 — Y. H. Kwan, P. J. Ledwith, C. F. B. Lo, and T. Devakul, Strong-coupling topological states and phase transitions in helical trilayer graphene, Phys Rev B **109** , 125141 (2024).

**一次資料:** https://arxiv.org/html/2308.09706 / https://arxiv.org/html/2308.09706v1

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、§I–VIの全主本文、§II.1–II.3 Methods、§III.1–III.2、Tables1–2、Figures1–15の抽出キャプション、謝辞まで。

**内容:** 緩和後の一つの周期domainで、中心bandへの投影、gate-screened Coulomb、平均密度subtractionを用いた強結合解析とHFにより整数充填相を分類する。HFはspin-collinearな状態と限られた倍周期・三倍周期を調べ、近似particle-hole対称性や谷間Hund項の省略を含む。displacement fieldでband inversionとChern数変化、さらにKekulé spiralや電荷秩序が現れると予測する。HFのflavor縮退を説明する「一方のspinだけの時間反転」は二次のエネルギー汎関数の対称性であり、全Hilbert空間のunitary/antiunitary対称操作ではないと本文が明確に区別する。

**今回の実装への判断:** グラフェンの電子構造・超伝導・相関状態を扱う研究であり、coherent XORローダー、CCZ/Toffoli分解、HMR補正または物理qubit削減の実装は提示しない。今回の回路最適化への直接適用は導けない。

**留保:** 相図は制限したHF/強結合近似内の結果で、微小な相間エネルギー差は基板・省略相互作用・量子揺らぎで変わり得る。部分充填のFCIをここで確定計算したわけではない。Appendix Aの強結合補正、Bのspin basis、CのHF flavor symmetry全体はこの補完では未読。原図画像・独立HF再実行・熱力学極限検証は未実施。

## graphene:38 — A. Datta, D. Guerci, M. O. Goerbig, and C. Mora, Helical trilayer graphene in magnetic field: Chern mosaic and higher Chern number ideal flat bands, Phys Rev B **110** , 075417 (2024).

**一次資料:** https://arxiv.org/html/2404.15452 / https://arxiv.org/html/2404.15452v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、導入部、§I Model、§II.1–II.2 Numerical study、§III.1–III.3 Analytical construction、§IV Second magic angle、§V Away from chiral limit、§VI Conclusion、謝辞まで。本文Tables1–2、主図キャプション、抽出されたtheta-functionとzero-modeの式を含む。

**内容:** 局所ABA/BAB continuum模型で、Zeeman効果を無視しchiral limitを取ると、第一magic angleのzero-energy flat bandが有限磁場でも保持される。chosen valley/stackingで正負の磁束に非対称な一量子・半量子磁束のtopological transitionを示し、theta-functionで構成するzero modeとB=0では特異なhidden stateの正則化で説明する。第二magic angleでは四flat bandとDirac coneを扱い、対応する解析解は今後の課題とする。有限corrugationではbandは分散し、magic angleとtransitionの一致も一般に失われる。

**今回の実装への判断:** グラフェンの電子構造・超伝導・相関状態を扱う研究であり、coherent XORローダー、CCZ/Toffoli分解、HMR補正または物理qubit削減の実装は提示しない。今回の回路最適化への直接適用は導けない。

**留保:** 第一chiral magic angleの代表磁場は約34/68Tで、有限corrugation・異なるtwist角の例も14/40T程度などパラメーター依存である。低磁場実験へ値を直接移す根拠にはしない。Appendices A–F（数値法、対称性、index/zero-mode補足、非chiral spectra等）はこの補完では未読。全式の独立証明、原図画像、数値再現は未実施。

## graphene:39 — Y. H. Kwan, T. Tan, and T. Devakul, Fractional Chern mosaic in supermoiré graphene, Phys Rev Res **7** , L032070 (2025).

**一次資料:** https://arxiv.org/html/2411.08880 / https://arxiv.org/html/2411.08880v1

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、§I Introduction、Non-interacting model、Interactions、Hartree–Fock phase diagram、Sublattice transitions、Exact diagonalization、Fractional Chern mosaics、Discussion、謝辞まで。Figures1–3の抽出キャプション、式(1)–(6)、脚注も通読。

**内容:** h-HTGの局所周期模型に有限範囲hopping由来のmomentum-dependent tunnelingを加えると、粒子正孔非対称とChern-sublattice間の平均エネルギー差が生まれ、ν=3から約3.5まで狭い|C|=1 conduction bandが保たれる。七HF bandを満たして残り一bandへ投影したN=30のEDでは、ν=3+1/3に三重準縮退とflux threading下のgapが得られ、FCIを支持する。二band EDは最大spin-valley偏極sector内では厳密だが、全八bandのground stateを無制約で調べるものではなく、FCIの直接徴候は有限サイズのため十分頑健ではない。局所FCIが成立すると仮定した先に、domainごとの谷偏極次第でHall伝導度やanyon統計が空間変調するfractional Chern mosaicを予測する。

**今回の実装への判断:** 分数電荷とanyon統計の理論予測はあるが、符号化qubit、braidingによる論理ゲート、magic-state準備またはcoherent XORローダーの回路は構成しない。fractionalizationから今回のToffoli数改善を導くことはできない。

**留保:** Coulomb screening、中心band投影、有限cluster、flavor偏極という条件を伴う理論予測であり、mosaicの実験観測ではない。domain間偏極配置の選択はdomain-wall energeticsに依存し未確定。Appendix A–DのMDT導出、追加HF/ED、FCI競合・finite-size検査全体はこの補完では未読。原図画像・ED再実行・多体熱力学極限検証は未実施。

## graphene:40 — D. Guerci, Y. Mao, and C. Mora, Chern mosaic and ideal flat bands in equal-twist trilayer graphene, Phys Rev Res **6** , L022025 (2024).

**一次資料:** https://arxiv.org/html/2305.03702 / https://arxiv.org/html/2305.03702v1

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、Introduction、Chern mosaic on the supermoiré scale、ABA stacking、AAA stacking/domain-wall lines、Stability away from chiral limit、Conclusions、謝辞とNote addedまで。Figures1–5の抽出キャプション、式(1)–(16)を含む主本文の全節。

**内容:** 等twistのstaircase TTGでmoireとsupermoiréの長さを分離し、ゆっくり変わる位相をparametricに扱う局所HamiltonianからABA/BAB周辺の総Chern数±1とAAAを結ぶgaplessな境界を得る。chiral limitの約1.69度では、sublatticeに分けたChern +2と−1のflat bandをtheta-functionによって解析構成し、holomorphicな理想量子幾何を示す。AAAの約0.75度では四重flat sectorがDirac coneと接続し、Γ点ではBerry curvatureの定義に例外がある。有限corrugationではbandが分散しても総Chern数とmosaicが保持される例をWilson loopで確認する。

**今回の実装への判断:** color-entangled bandやholomorphicな波動関数は電子バンドの構成であり、量子回路のmagic state、CCZ/Toffoliのphase-polynomial分解とは別の対象である。今回のローダー合成・HMR補正・qubit数削減に適用できるゲート列は提示しない。

**留保:** 主に非相互作用・局所断熱模型の結論で、FCIの多体ground stateの確定ではない。等しくないtwistへの拡張は本文ではconjectureとして置く。付録/補足A–Gはこの補完では未読。抽出式にはsubscriptの重複や未展開macroがあり、原PDFによる全式の照合・原図画像の独立検査は未実施。

## graphene:41 — Y. Mao, D. Guerci, and C. Mora, Supermoiré low-energy effective theory of twisted trilayer graphene, Phys Rev B **107** , 125423 (2023).

**一次資料:** https://arxiv.org/html/2210.11507 / https://arxiv.org/html/2210.11507v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、§I–VII全主本文、§IV.1–IV.3を含む有効模型の導出・gauge symmetry、等角と1/2角度比の数値結果、全主図キャプション、謝辞まで。

**内容:** moireとsupermoiréの空間尺度が十分離れる場合に、局所固有状態へ射影した長波長有効Hamiltonianを導く。位置依存のDirac速度だけでなくnon-Abelian connectionを残すことでgauge covarianceとcoherentな長距離状態を表し、局所DOSの単純加算では失われるpseudo-minibandを得る。C2zTと孤立Dirac coneの保護により等角のbandは接続し、角度比1/2では二coneのsectorにgapが生じ得る。小角度で速度成分がゼロになるとmomentum cutoffへの収束が失われ、短距離正則化が必要になることを明記する。

**今回の実装への判断:** non-Abelian connectionは連続空間の有効Hamiltonianでgauge covarianceを保つ項であり、non-Cliffordゲート合成ではない。任意の基底変更を費用ゼロの回路操作と読み替える根拠はなく、今回のToffoli/qubit削減を直接導かない。

**留保:** 一般の任意twist対を無条件に扱う模型ではなく、近い有理数比と尺度分離を要する。図14の数値地図は|δq|/|q̄|≤0.2を課し、等角は2度より上、1/2または2比は小さい方の角≥1.8度に制限する。約2度未満などのDOS増強について著者の定性的期待はあるが、その領域のcutoff-independentな定量予測ではない。Appendices A–F、原図画像、独立数値再現はこの補完では未読・未実施。

## graphene:42 — Z. Zhu, S. Carr, D. Massatt, M. Luskin, and E. Kaxiras, Twisted Trilayer Graphene: A Precisely Tunable Platform for Correlated Electrons, Phys Rev Lett **125** , 116404 (2020).

**一次資料:** https://arxiv.org/html/2006.00399 / https://arxiv.org/html/2006.00399v2

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、Introduction、Momentum-space Hamiltonian、Density of states、Evolution of VHS、Moiré of moiré、まとめ、謝辞まで。Figures1–4の抽出キャプション、式(1)–(7)、脚注を含む主本文全節。

**内容:** 二つの独立twist角を持つ一般の非整合TTGをmomentum-spaceで記述し、有限energy cutoffでも二段散乱で低energyに戻る状態が無限にあり、通常のmoire Brillouin zoneでは閉じないことを示す。実計算では各単層reciprocal vectorにも追加cutoffを置き、約5600momentumとGaussian smearingでDOS/VHSを評価する。異なるtwist角では第三層の非整合摂動によりTBG型magic条件が曲線へ広がる一方、等角のVHS hybridizationは別機構で、perturbativeな速度消失条件と数値結果が一致しない。強相関や超伝導を直接計算したのではなく、DOS/VHSを相関効果のproxyとして用いる。

**今回の実装への判断:** グラフェンの電子構造・超伝導・相関状態を扱う研究であり、coherent XORローダー、CCZ/Toffoli分解、HMR補正または物理qubit削減の実装は提示しない。今回の回路最適化への直接適用は導けない。

**留保:** 追加cutoffが低energy状態も落とすため一般の収束保証はないと本文が明記し、調べたDOS最大・VHS位置の安定性と厳密収束を区別する。first-shell摂動のmagic条件はω0=ω1を仮定し、等角付近には適用できない。Supplemental Material I–IV、原図画像、公開MATLABの再実行は今回未読・未実施。原文数式の単位・組版を独立に全検証したものではない。

## graphene:43 — C. Mora, N. Regnault, and B. A. Bernevig, Flatbands and Perfect Metal in Trilayer Moiré Graphene, Phys Rev Lett **123** , 026402 (2019).

**一次資料:** https://arxiv.org/html/1901.05469

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。表題・Abstract・導入、Bloch-band coupling、equal angles、symmetries、等角・不等角での全バンド接続性の二つの証明、結論・謝辞まで全文。独立のMethods節はなく、模型導出は本文内に含む。

**内容:** ['低エネルギーDirac近似、隣接層の短距離一様トンネル、同じ方向に並ぶ運動量差、連続twist角の有理比を用いてmomentum-space moiré周期性を構成する。一般の非整合角へ同じBloch周期性を保証しない。', 'magic angleでDirac速度は消えるが、全バンドが一斉に平坦になるわけではなく、特定対称線近傍での平坦化。全bandの接続性はemergent particle-hole symmetryとC2zT等の対称性に依存する。', '等角の場合は表現multiplicityの偶奇、不等角の場合は奇数Dirac coneとwindingの議論を使う。粒子・正孔対称性を破る曲率項を無視した模型の主張で、任意の実材料に全エネルギーgaplessを無条件に保証しない。奇数多層への拡張はconjecture。']

**今回の実装への判断:** 今回の固定語表ローダーの回路構成・厳密等価変換・Toffoli削減を与える結果はない。物理系の低エネルギー近似やband topologyを、任意入力のXOR回路の正しさ・費用境界へ置き換えない。

**留保:** ['Supplement S-I–S-IVは今回未読（従前レビューの確認範囲を別記）。参考文献全項の本文は今回の範囲外。', '図の画素照合や全証明の独立再導出はしていない。HTMLの著者欄に後年日付があるが、ヘッダのv1と内容hashを版識別に用いる。']

## graphene:44 — N. Nakatsuji, T. Kawakami, and M. Koshino, Multiscale Lattice Relaxation in General Twisted Trilayer Graphenes, Phys Rev X **13** , 041007 (2023).

**一次資料:** https://arxiv.org/pdf/2305.13155

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、I、II A–D（構造・commensurate近似・格子緩和・電子continuum方法）、III A–B、IV A–B、V、謝辞を全文。図1–16の抽出説明を含む。参考文献冒頭も区間に含むが残りは未読。

**内容:** ['弾性energyと隣接層の結合energyを最小化し、Fourier展開したEuler–Lagrange方程式を自己無撞着に解く。out-of-plane displacementと層1–3のremote interaction/hoppingは無視する。G=0は別パラメータとして走査して低energy解を選ぶ。', 'chiralとalternatingの各3例を比較。A1/A2では二つのmoiré格子の微小な相対回転を捨てる近似commensurate構造を使い、他の例と同じexact commensurationではない。有限Fourier cutoffも指定されている。', '中間層の緩和のfrustrationによりchiralではAA点をずらすdomain、alternatingではAA点を重ねるdomainが好まれる。chiral domain間の1D状態は局所模型のvalley Chern差で説明され、両valleyを合わせた通常のcharge Chern insulatorとは区別する。', 'alternatingではmirror-odd Dirac coneとflat-band成分の混成が緩和で弱くなる。垂直電場は層間一定としたonsite potentialで導入し、混成とbandwidthを変える。観測実験や任意構造に対する厳密な最適解の証明ではない。']

**今回の実装への判断:** 今回の固定語表ローダーの回路構成・厳密等価変換・Toffoli削減を与える結果はない。物理系の低エネルギー近似やband topologyを、任意入力のXOR回路の正しさ・費用境界へ置き換えない。

**留保:** ['使用した一次本文は2023年6月のv2 preprint。出版版そのものの全差分照合はしていない。', 'このキャッシュには独立のAppendix/Supplement節はなく、参考文献の後半は未読。抽出した行列の配置崩れを独立PDF画像で全照合したとはしない。']

## graphene:45 — Y. Liu et al., Imaging moiré flat bands and Wigner molecular crystals in twisted bilayer MoTe2, Natl. Sci. Rev. **13** , nwag014 (2026).

**一次資料:** https://arxiv.org/pdf/2406.19310

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract、導入、二つのdevice setup、K/Γ valley bands、displacement field、Wigner molecular crystals、結論・追加注記を全文。本文末Methods（fabrication、angle/strain、STM/STS、DFTとcontinuum calculation）全節を含む。

**内容:** ['五つのdevice、twist角約2.3–3.8度でSTM/STSとDFTを比較。二重back gateはohmic contactと測定領域のFermi levelを別々に調整し、tip距離によりK/Γ谷・上下層の感度が変わる。', 'displacement fieldはback gateだけでなくtip biasと仕事関数にも依存する。XM/MXの縮退が解けるhoneycombからtriangularへの変化を観測し、topologyの解釈をDFT/continuum模型と結びつける。STS像単独でChern数を直接測った結果とはしない。', 'ν_MX=3の三つのcharge-density peakとtip距離依存からWigner分子・Kagome配置を論じる。tip screeningが相互作用を変えるため、測定probeを無影響と仮定しない。Methodsのheterostrain fitは一層の一軸strainを仮定し、DFT/Gaussian broadening・二調波continuum模型には明示した近似がある。']

**今回の実装への判断:** 今回の固定語表ローダーの回路構成・厳密等価変換・Toffoli削減を与える結果はない。物理系の低エネルギー近似やband topologyを、任意入力のXOR回路の正しさ・費用境界へ置き換えない。

**留保:** ['参考文献、Extended Data figuresの本文末の説明、別Supplementaryは今回通読していない。', 'PDF抽出ヘッダにversion番号が見当たらず、arXiv番号・cache hashで読んだ本文を同定する。出版版との差分照合や全行列の画像確認・実験再現はしていない。']

## graphene:46 — J. Jang, Effect of lattice relaxation on electronic spectra of helically twisted trilayer graphene: large-scale atomistic simulation approach, J. Korean Phys. Soc. **85** , 727 (2024).

**一次資料:** https://arxiv.org/pdf/2407.19143

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。表題・Abstract、I、II.1–II.2 Methods、III.1–III.2 Results、IV Discussion、V Conclusion、謝辞・声明まで全文。図1–5の抽出説明と参考文献冒頭を含む。

**内容:** ['500–1000 nmの有限試料をLAMMPS、Brenner/Kolmogorov–Crespi potential、FIREで緩和し、座標をpybindingのtight-bindingへ渡す。停止条件はenergy変化0.5 ppmであり、すべての構造のglobal minimumを証明するものではない。', '角度を増やすとatomic commensurate、moiré commensurate、supermoiréの三regimeが現れるという数値結果。低角度では初期ABA/AAA/ABC stack依存が残り、有限試料・potential選択・edge影響を無条件に消した定理ではない。', 'KPM/Jackson kernelと15 meV broadeningでDOS/LDOSを求め、緩和による低energy gapとdomain-wall statesの変化を示す。out-of-plane corrugationも含む点はin-plane continuum近似と異なる。STM/SETでの観測は提案で、この論文自体の実験検出ではない。']

**今回の実装への判断:** 今回の固定語表ローダーの回路構成・厳密等価変換・Toffoli削減を与える結果はない。物理系の低エネルギー近似やband topologyを、任意入力のXOR回路の正しさ・費用境界へ置き換えない。

**留保:** ['参考文献の後半は未読。キャッシュに独立のSupplement/Appendixはない。', '抽出にはhopping cutoffの単位がmm、図5のenergyが本文380 meVに対してcaption 0.38 meVとなる等の不整合があるため、これらの数値を確定実装値として引用しない。図の原画像との全照合はしていない。']

## graphene:47 — A. Kerelsky et al., Moiréless correlations in ABCA graphene, Proc. Natl. Acad. Sci. **118** , e2017366118 (2021).

**一次資料:** https://pmc.ncbi.nlm.nih.gov/articles/PMC7848726

**読解状態:** 本文文章の全節を読解（埋め込み表・数式に取得欠落）

**実読範囲:** 前回の読解範囲に補完読解を統合。PNAS/PMC本文のSignificance、Abstract、導入、Results、Discussion、Materials and Methods（Experiment、Tight Binding and DFT）を全節確認。図1–4の抽出説明を含む。

**内容:** ['微小twistのdouble bilayerからmicron-scale ABCA領域を作り、moiréの影響をdomain wallへ寄せた均一領域をSTSで測る。電場とdopingはback gateで同時に変わり、STMは主に最上層のLDOSへ感度を持つ。', '3–5 meV半値幅とCNP近傍の9.5 meV peak-to-peak gapを観測。低電場のgapは用いた単粒子DFTと合わず、短距離・層間相互作用のmean-field模型でferrimagnetとcharge-transfer excitonic insulatorを候補に挙げる。磁気秩序の確定には追加測定が必要と本文が述べる。', 'ABCA–ABAB境界でvalley Chern差に対応するsurface edge stateを論じるが、ABAB全体はmetallic。滑らかな境界でintervalley scatteringが弱い仮定とlayer polarizationにより混成が減り、他のbulk状態への散乱をtopologyが完全に禁止するわけではない。', 'Methodsは5.7 K STM、gap抽出のGaussian peak位置とplateau edge、LDA/600 eV/150×150×1 DFT、有限flakeとLanczos LDOSを明示する。経験的モデルと数値手順の条件を保持する。']

**今回の実装への判断:** 今回の固定語表ローダーの回路構成・厳密等価変換・Toffoli削減を与える結果はない。物理系の低エネルギー近似やband topologyを、任意入力のXOR回路の正しさ・費用境界へ置き換えない。

**留保:** ['SI Appendix、本文後の参考文献・関連データ、別訂正文は今回未読。ページに2021年3月のcorrectionへの告知があり、その内容の独立確認はしていない。', 'PMC抽出は一部数式・パラメータが空欄になる。全節の文章は読んだが、欠落した式を読了または実装可能に検証済みとはしない。']

## graphene:48 — D. Walkup, B. A. Assaf, K. L. Scipioni, R. Sankar, F. Chou, G. Chang, H. Lin, I. Zeljkovic, and V. Madhavan, Interplay of orbital effects and nanoscale strain in topological crystalline insulators, Nat. Commun. **9** , 1550 (2018).

**一次資料:** https://arxiv.org/pdf/1610.09337

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。表題、Abstract、導入からstrain抽出・QPI・orbital模型の結論まで主本文を全文。謝辞、Methods、図1–5の全抽出captionを含む。

**内容:** ['SnTe/PbSe(001)のmisfit dislocationを利用し、同じ領域のSTM topographとQPIを測る。Lawler–Fujita補正を2–3格子定数の尺度で使い、displacementの微分からbiaxial・uniaxial・shear・rotation成分を分ける。', 'strainごとのmaskを掛けたdI/dVのFourier peakを比較し、一方向のstrainで垂直方向のDirac-node変位が強いという結果を得る。shearが小さい試料に対象を絞り、全strain tensorの独立な実験制御を行ったわけではない。', '説明はTe由来conduction bandのpx/py軌道とtwo-center tight-binding近似での重なり変化。Methodsは約40層の薄膜、約4.5 K、10 meVのlock-in励起などの測定条件を示す。mirror保護とtime-reversal保護を区別する。']

**今回の実装への判断:** 今回の固定語表ローダーの回路構成・厳密等価変換・Toffoli削減を与える結果はない。物理系の低エネルギー近似やband topologyを、任意入力のXOR回路の正しさ・費用境界へ置き換えない。

**留保:** ['Supplementary I–III、参考文献本文は今回未読。測定maskの詳細・軌道hoppingの展開証明を独立に再現したとはしない。', '全figure画像のpixel照合はしていない。']

## graphene:49 — M. J. Lawler et al., Intra-unit-cell electronic nematicity of the high-Tc copper-oxide pseudogap states, Nature **466** , 347 (2010).

**一次資料:** https://arxiv.org/pdf/1007.3216

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract相当の導入、本文全段落と式(1)–(5)、結論、謝辞、図1–4の全説明を通読。独立の本文末Methods節はなく、本文内の観測量・registry・normalization・coarse grainingの方法を確認。

**内容:** ['Cu原点で位相をそろえたFourier変換の二つのBragg peakの実部差をnematic order parameterとする。sub-unit-cell解像度と極めて正確なCu位置registryが必要で、Cu点だけを標本化すると指標はゼロになる。', 'g(r,+ω)/g(r,−ω)の比と局所pseudogapで規格化したenergyを用いて電子不均一性の影響を抑える。実空間の二つのO site差から計算した独立指標と比較し、pseudogap付近でO-site由来のC4→C2対称性破れを示す。', 'nematicとsmecticの異なる波数成分・coarse-graining尺度を区別する。相関長が視野サイズへ到達する観測は無限系での厳密発散の直接測定ではない。ARPES・neutron結果と共通起源ならO-siteの弱い磁気状態という結論は条件付き解釈。']

**今回の実装への判断:** この原著はSTMの格子registry補正とnematic order parameterの方法論であり、graphene本論の画像解析には関連する。Boolean出力基底の変更やHMR位相補正、Toffoli積共有へ同じFourier手順を適用する構成は与えない。

**留保:** ['別Supplementary Information I–VIと動画は今回未読。本文で引用される全systematic-error検査の独立再解析はしていない。', 'PDF抽出で数式の添字や分数の順序が崩れる箇所がある。定義の説明を含め読んだが、全式を画像照合した実装仕様とはしない。']

## graphene:50 — L. Ju et al., Topological valley transport at bilayer graphene domain walls, Nature **520** , 7549 (2015).

**一次資料:** https://wanglab.berkeley.edu/wp-content/uploads/2009/12/nature14364.pdf

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 著者大学公開PDFの抽出全文41,003文字を実読。本文、Methods、図1–4とExtended Data 1–2のキャプション。参照されるExtended Data 3は抽出に含まれず、全図画像の独立検査は行っていない。

**内容:** AB/BA bilayer graphene domain wall の伝導を、同じflakeの壁なし対照、電場・温度・長さ依存で確認。約400 nmのballistic length（適合では420 nm）と4e^2/hに近い短チャネル伝導を示す。保護にはvalley混合散乱が少ない条件があり、完全に無条件の無散乱伝導ではない。

**今回の実装への判断:** 滑らかな結晶境界のvalley輸送の実験。今回の論理ゲート合成・可逆語ローダーへ転用できる回路恒等式は含まない。

## graphene:51 — H. Yoo et al., Atomic and electronic reconstruction at the van der Waals interface in twisted bilayer graphene, Nat. Mater. **18** , 448 (2019).

**一次資料:** https://arxiv.org/pdf/1804.03806

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。Abstract相当導入、主本文全文、謝辞・著者情報、図1–3caption、本文末Methods（TEM、FEM、DFT/tight binding、transport）を全節通読。区間内の主参考文献も読んだがMethods後の追加参考文献は未読。

**内容:** ['TEM dark-field像とSAED satellite intensity、有限要素計算、transportを突き合わせ、約1度を目安に滑らかなmoiréからAB/BA domain・soliton壁へのcrossoverを示す。diffraction intensityだけでは位相情報が失われ、完全構造を直接復元できないと明記する。', 'FEMは非線形弾性・bending・Kolmogorov–Crespi界面energyとL-BFGSを使う。1.1度付近と0.47度付近で緩和がband構造へ及ぼす影響は異なり、rigid模型の第二magic angleをそのまま用いない。', '垂直場でAB/BAをgappedにした1D networkの輸送像を示す。h/(4e²)の抵抗networkとの比較には頂点でのincoherentな混合を仮定する。強い場でのHofstadter feature減少は2Dからnetwork輸送への解釈で、coherent量子ゲートの実装ではない。', 'MethodsではTEMとtransport用のsample構造・測定条件を分ける。一般試料は4端子、1.1度試料は2端子の測定であり同一条件の直接比較としない。']

**今回の実装への判断:** 今回の固定語表ローダーの回路構成・厳密等価変換・Toffoli削減を与える結果はない。物理系の低エネルギー近似やband topologyを、任意入力のXOR回路の正しさ・費用境界へ置き換えない。

**留保:** ['別Supplementary Information S1以降の全体は今回未読。Methods後の参考文献は未読。', '抽出中のθや数式文字が二重化している箇所があり、全式・図をpixel照合していない。']

## graphene:52 — S. Huang, K. Kim, D. K. Efimkin, T. Lovorn, T. Taniguchi, K. Watanabe, A. H. MacDonald, E. Tutuc, and B. J. LeRoy, Topologically Protected Helical States in Minimally Twisted Bilayer Graphene, Phys Rev Lett **121** , 037702 (2018).

**一次資料:** https://arxiv.org/html/1802.02999

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。表題・Abstractから作製・STM/STS測定方法、continuum Hamiltonian、gate依存・spatial LDOS・contrast解析、結論・謝辞まで全主本文を通読。図1–4の抽出captionを含む。独立のMethods節はない。

**内容:** ['57.6±0.7 nmのmoiré周期（twist約0.245度）のsampleを含む、50 nm超の周期のtBLGを作製し、電場でAB/BAにgapが開いたときにdomain wallのdouble-line LDOSを観測する。', 'back gateはdopingと電場を共に変え、tip biasとtip/sampleの仕事関数差がzero-field gate offsetを生む。contrastはdomain wallとABのLDOS差をAB値で規格化した測定量である。', 'continuum Hamiltonianはspin/valleyのdecouplingと4重縮退を仮定。低energy network模型が要求するE_λ≪Δが実験で十分満たされず、対応するpeakは一つだけ明確と本文が認める。高energyの二つのpeakは別のsaddle-point DOSとして説明する。', '将来のdissipationless network応用への展望と、今回の局所spectroscopyによる証拠を分ける。量子情報の論理ゲート、braiding操作またはToffoli構成の実証ではない。']

**今回の実装への判断:** 今回の固定語表ローダーの回路構成・厳密等価変換・Toffoli削減を与える結果はない。物理系の低エネルギー近似やband topologyを、任意入力のXOR回路の正しさ・費用境界へ置き換えない。

**留保:** ['本文が引用する別Supplementary Informationはこのcacheに含まれず、今回未読。参考文献全項の本文も対象外。', 'HTML著者欄に後年日付が現れるため、arXiv headerのv2とhashで版を同定する。']

## graphene:53 — J. S. Alden, A. W. Tsen, P. Y. Huang, R. Hovden, L. Brown, J. Park, D. A. Muller, and P. L. McEuen, Strain solitons and topological defects in bilayer graphene, Proc. Natl. Acad. Sci. **110** , 11256 (2013).

**一次資料:** https://arxiv.org/pdf/1304.7549

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。表題・要旨から主本文全節、Figure 1–4の抽出キャプション、Methods（Growth and transfer、ADF-STEM、DF-TEM、Multislice simulations）と謝辞、主本文参考文献1–30までを連続して読んだ。Supplementary Materials開始直前まで。

**内容:** ['AB/BA積層を層間変位の秩序変数で表し、三方向の一結合長のずれが有限幅solitonを作る。六つのdomainが会するAA coreの周りで変位が2π巻く構造欠陥を観察する。ここでの位相欠陥は結晶構造の欠陥であり、非可換anyonや量子ゲートの実証ではない。', '原子分解能像からshear wallの幅6.2±0.6 nm、tensile wallの幅10.1±1.4 nmを得て、角度依存をFrenkel–Kontorova型モデルへ適合する。弾性率Et=340 N/mとPoisson比0.16を固定し、障壁Vsp約1.2 meV/atomとshear modulus約130 N/mを推定する。障壁はモデルを介した推定値である。', '80 keV電子線の高い照射量でもwallは移動し、1000°C超の加熱でも運動が増える。beam-induced motionと熱的運動、wrinkle等のpinningを分けている。低い照射量で800°C未満の運動が稀という観察を、照射条件に依存しない普遍的閾値へ外挿しない。', 'Methodsは60 kV ADF-STEM、80 kV DF-TEM、20秒/frame、加熱stageとmultislice散乱計算を記述する。予測されるdomain-wallの電子的1D伝導は本論文で測定した輸送特性ではない。']

**今回の実装への判断:** 有限幅domain wall、変位の巻き数、構造解析を理解する資料。これをBoolean中間値の共有、HMRの位相修正、CCX数の削減へ変換する構成は提示されていない。

**留保:** ['今回の通読は29329文字のSupplementary Materials開始まで。補足本文、Supplementary Figures、動画本文・映像の全体は通読・再生していない。従前の補足資料の部分確認とは区別する。', '原子像の画素から幅を再測定しておらず、multislice計算やモデル適合の数値再現もしていない。PDF抽出で崩れた数式記号を全箇所画像照合したとはしない。']

## graphene:54 — Y. Sha, J. Zheng, K. Liu, H. Du, K. Watanabe, T. Taniguchi, J. Jia, Z. Shi, R. Zhong, and G. Chen, Observation of a Chern insulator in crystalline ABCA-tetralayer graphene with spin-orbit coupling, Science **384** , 414 (2024).

**一次資料:** https://arxiv.org/pdf/2310.17971

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。表題・要旨から主本文の全段落・結論までを読んだ。後置されたFigure 1–4の全抽出キャプション、謝辞等に加え、Materials and MethodsのS1–S4（結晶成長、device fabrication、transport、symmetrization/antisymmetrization）も読んだ。Figure S1開始以降は今回の通読に含めない。

**内容:** ['WSe2近接によるspin-orbit couplingを持つABCA tetralayer grapheneで、charge neutrality付近の磁気ヒステリシスと異常Hall応答を測定する。中間displacement fieldに現れる相を、低Dのlayer-antiferromagnetと高Dのlayer-polarized insulatorの間のChern相として解釈する。', 'ゼロ磁場でのHall抵抗は最大約5.0 kΩ、h/(4e²)の約78%であり、完全量子化値には達していない。他方、0.4 Tでh/(4e²)への量子化とChern数4に整合するStředa傾斜を示す。「ゼロ磁場で完全に量子化した」という読み替えを避ける。', '電荷Hall応答は実測だが、ALL状態に期待するspin、valley、spin-valley Hall応答をすべて直接測定したわけではない。flavor秩序やlayer配置の詳細には理論的解釈が含まれ、論文自身が追加のspin/valley-sensitive測定を提案する。', 'MethodsはSNOMによる積層確認、0.1 K dilution refrigeratorと1.5 K cryostat、1–10 nAの励起を述べる。主図のraw Hall信号と対称・反対称化したデータを区別し、縦抵抗の混入を扱う。parallel-plate capacitanceからの密度推定はCNPで絶縁的になると定量的に不正確になり得ると明記する。']

**今回の実装への判断:** 磁気秩序とChern絶縁相の条件を示す輸送実験。Chern数やHall抵抗から、固定テーブルXORのToffoli数や測定後の位相正当性は導けない。

**留保:** ['主参考文献22605–33195、Figure S1以降の補足図・captionの全体、補足参考文献は今回通読していない。S1–S4の方法本文は読了済み。', 'PDF抽出の式・図を全画素照合しておらず、磁化・Hall曲線の数値再現はしていない。量子計算への言及は展望であり、ゲートの実装や誤差率を実証したものではない。']

## graphene:55 — T. Han et al., Signatures of chiral superconductivity in rhombohedral graphene, Nature **654** , 643(2025).

**一次資料:** https://arxiv.org/pdf/2408.15233

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。表題・要旨からPhase diagram、normal-state fermiology、spin/valley polarization、temperature dependence、strong coupling、Discussion、全Methodsを連続して読んだ。主図1–5の抽出キャプション、device/transport、tight-binding、他device、fluctuations、quantum oscillations、coherence lengthの方法を含み、Author Contributions直前まで。

**内容:** ['rhombohedral tetra-/pentalayer grapheneの五deviceで複数の超伝導領域を調べ、最大Tc約300 mKを報告する。中心的なbare T3/P1 deviceではWSe2によるSOCを仮定せず、hBNをmisalignして観測可能なmoiréを避けている。他deviceとすべて同じ近接構造ではない。', 'zero-field anomalous Hall、垂直磁場での抵抗ヒステリシス、面内磁場への強さを合わせ、time-reversal symmetry breakingとspin/valley-polarized pairingを示唆する。ただしp+ipのpairing symmetry、topological superconductivity、Majorana zero modeを直接観察したわけではなく、Kerr、SQUID、Josephson、Little–Parks、熱輸送等の追加実験を提案する。', 'SC1の隣のquarter-metalでは単一spin/valley pocketの解析を示すが、SC2の親状態のFermiologyには不確実性が残る。annular pocketや他valley pocketの可能性、低周波FFT成分を解像しにくいこと、未同定metalをMethodsが明記する。全超伝導領域で完全なspin/valley分極が確定したとはしない。', '主図のnominal base temperature約7 mKと電子温度の下限約40 mKを区別する。小さいAC電流を用いる。垂直critical fieldはnormal-state抵抗の10%を基準とし、5–15%基準による不確実性を扱う。GL式からbase-temperature coherence lengthを評価し、Tc近傍でのGL fittingとは異なる。', 'coherence lengthが電子間隔に近いことは強結合・BCS–BEC crossoverへの接近を示唆するが、推定はなおBCS側でありBECの直接観測ではない。8/10-band SWMcClure計算、screened displacement field、単一valleyのbandや有効質量の定義などのモデル仮定が入る。抵抗fluctuationのdomain解釈もcooldown履歴等に依存する。']

**今回の実装への判断:** 将来のtopological superconductivity研究への動機はあるが、今回の128-qubit上限内のCCZ/Toffoli合成や任意target XORの実装手順は与えない。物質相の兆候からゲート資源削減を計上しない。

**留保:** ['41066以降のauthor statements、Extended Data Figures、参考文献、別Supplementary全体は今回通読していない。主本文末のMethodsは全節通読した。', '全band行列・数式のPDF画像照合、FFTやcritical-field fitの再実行、全図の独立解析は行っていない。抽出で崩れたtight-binding行列の記号を検証済みとはしない。', '論文表題のSignaturesを、確定したpairing symmetryや利用可能なMajoranaゲートの実証へ読み替えない。']

## graphene:56 — Z. Lu et al., Extended quantum anomalous Hall states in graphene/hBN moiré superlattices, Nature **637** , 1090 (2025).

**一次資料:** https://arxiv.org/pdf/2408.10203

**読解状態:** 本文の全節を読解（付録等に未読あり）

**実読範囲:** 前回の読解範囲に補完読解を統合。表題・要旨、導入、fractional/extended QAHの観測、温度・電流依存、displacement-field phase transitions、Discussionまで主本文全節と主図1–4の抽出captionを読んだ。後置Methodsの全節（IR imagingとfabrication、transport、縦/Hall抵抗分離、Device 2、Device 3）も読了した。

**内容:** ['二つのpentalayer deviceと一つのtetralayer graphene/hBN deviceを用い、fractional QAHと低温・低biasで現れるextended QAH (EQAH)を報告する。EQAHではRxy=h/e²、Rxx≈0が広い密度範囲へ広がる。最大ν≈0.5–1.3という範囲はtetralayerの結果であり、pentalayerの三領域には小さなgapが残る。すべてのdeviceで同じ連続plateauを観測したとはしない。', 'mixing chamberのbase temperature 10 mKと推定電子温度約40 mKを区別する。Methodsは17.77 HzのAC、DC bias、Landau fanからのgate capacitanceを記述する。保磁力を超える正負の磁場での測定を使う対称・反対称化で縦/Hall抵抗を分離し、磁気ヒステリシスと合わせてzero-field応答を判断する。', '低温・低biasではEQAHが一部のFQAH領域を置き換え、温度・current・Dによってfractional stateや(composite) Fermi liquidへ変わる。currentとtemperatureの依存は同一ではなく、非単調な抵抗とbreakdown thresholdを示すため、電流の全効果を単なる加熱と同一視しない。', 'Discussionは二つの候補像を区別する。ひとつはtime-reversalとtranslationを破るQAH crystal、もうひとつは整数QAH液体と余剰電荷のWigner crystalからなるre-entrant類似像である。広い非整合fillingや最下moire bandでの挙動は従来RQHEと異なり、電子結晶であることを確定するにはreal-space imaging、diffraction、narrow-band noise等が必要だと述べる。', '高throughput IR cameraはnear-field/Ramanと組み合わせて積層を確認する。中間積層が似たcontrastを示すこと、遠視野の約1 μm分解能では小domainを見逃すことをMethodsが認める。moireなしでQAH crystalを安定化できるという説明は将来の検証案であり、今回その実験を完了したものではない。']

**今回の実装への判断:** 多体輸送の相と条件を与える資料である。Hall量子化やelectron-crystalの候補像は、Boolean積の共有、Clifford+measurementによる無償非Clifford生成、HMRの位相検証を与えず、Toffoli削減の実証としては扱わない。

**留保:** ['31058–42567の参考文献、47751以降のauthor/data statementsおよびExtended Data Figuresの全体は今回通読していない。主本文および後置Methodsに途中切れは認めていない。', '全図の画素照合、全抵抗データの再解析、温度の独立校正、QAH crystalの直接観察は行っていない。後者は論文自身が未確定として追加実験を求める事項である。']
