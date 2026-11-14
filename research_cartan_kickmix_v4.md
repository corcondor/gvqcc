# Cartan/KAK研究と現在のKickMix最適化への対応

2026-11-15（日本時間）。文献と採点コードを確認した記録。現在の優先対象は `dfthcsos` の整数角度テーブルとANGLEローダーである。

## 1. 提示された4論文の確認

| 文献 | 一次資料で確認した内容 | 今回への読み替え |
|---|---|---|
| Ding, Yu Liu, Zi-Wen Liu, *On the KAK Decomposition and Equivalence Classes*, 2026-05-11 | [arXiv:2605.10783](https://arxiv.org/abs/2605.10783)。double-coset同値と、全体位相を無視するprojective-local同値を区別する。 | 最小Toffoli数を与える論文ではない。外部制御を持つ部分回路で全体位相を無断で捨てない、という監査に役立つ。 |
| Wierichs et al., *Recursive Cartan decompositions for unitary synthesis*, 2025-03-24 / v2 2025-06-13 | [arXiv:2503.19014](https://arxiv.org/abs/2503.19014)。再帰分解を統一し、回転パラメータ数の最適性も検討。1000-qubitの例はtransverse-field XYの構造を使う。 | 889-qubit DQI全体へ一般ユニタリ分解を適用できるという意味ではない。§V.3は誤り訂正下のCX費用と任意角回転費用を明確に区別する。 |
| Drury–Love, *Constructive Quantum Shannon Decomposition from Cartan Involutions*, 2008-06-25 | [arXiv:0806.4015](https://arxiv.org/abs/0806.4015)。QSDを対合から構成。 | 「AIIIとAIを交互」は不正確。AIIIとブロック交換の対合を再帰し、最後の2-qubit部分でAIを使う。2025年論文Appendix BではAIII+Aと整理される。 |
| Tucci, *An Introduction to Cartan's KAK Decomposition for QC Programmers*, 2005-07-18 | [quant-ph/0507171](https://arxiv.org/abs/quant-ph/0507171)。線形代数による2-qubit分解の教育的解説と実装。 | 小さな閉じたユニタリ部分回路を扱うときの資料。任意1-qubit回転を使える設定の分解費用を、そのままKickMix費用と同一視しない。 |

補足の一次資料は [Vatan–Williams, Optimal Quantum Circuits for General Two-Qubit Gates](https://arxiv.org/abs/quant-ph/0308006)。最大3 CNOTという結果は、その論文の1-qubit回転を含むゲート集合についての結果である。

## 2. KickMixの構造を正確に分ける

測定・reset・初期化を除いた、ユニタリ命令だけの区間は `U|x> = exp(i phi(x)) |pi(x)>` というmonomial unitaryとして扱える。全monomial unitaryの群は `U(1)^(2^n) ⋊ S_(2^n)` であるが、許されたゲート、精度、補助ビットの条件を無視してKickMixの生成集合と等しいとは言わない。

HMR/Rと古典分岐を含む回路全体はユニタリ部分群ではない。Googleの原論文も測定記録ごとのKraus作用とisometryで記述する。一般のゴミをHMRだけで消すのではなく、測定が生じさせる位相の補正が必要である。

[Google原論文 arXiv:2610.23832v2](https://arxiv.org/html/2610.23832v2) は、1 coreで6.0×10^10 instructions/sを報告している。これは64〜512のtrajectoryをまとめるSIMD実装に基づく測定値であり、Python走査や任意角Z_POWに一律に適用する実行時間予測ではない。Z_POWの位相累積は個々のtrajectoryを処理する例外である。

命令の一次資料：[Qualtran KickMix instruction reference](https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_instructions.md)。単独のHや一般のRyを任意に提出できる命令集合ではない。

## 3. 採点式に届く変更を選ぶ

現在参照しているpinned verifierの `dfthcsos/scoreinfra/costs_prepare.py` は、Givens費用を

`T_givens = 2 * (N - 1) * (2 * brot - 1)`

で数える。`dfthcsos/verify.py` の `heuristic_costs` はbeta=brotを設定し、ANGLEローダーの実測費用と合わせる。したがって、GivensのCX実装だけを短縮しても、この採点項は変わらない。整数角度の精度、brot、ローダーの非線形演算数、量子ビット数まで変化させる必要がある。

採点コードの確認元は共有作業領域の `official_sources/Inzainos/verifiers`。プロジェクトの検証記録と同じpinned資料を使い、最新の外部WSLファイルを読めたことにはしていない。

| 対象 | 主な採点費用 | 今回の研究を使う場所 |
|---|---|---|
| invsqrt | Q × Toffoli等価費用。回転の合成誤差予算も関係する。 | 計算したBoolean関数上の位相の共有・相殺、演算ビット幅、区分近似。Walsh展開のCX削減だけを点数改善とは数えない。 |
| dqi | 誤り率による係数 × Q² × 実行Toffoli数 | GF乗算の共有積、AND数、作業ビット、測定位相補正。誤り率を一定と仮定しない。 |
| dfthcsos | lambda_eff × T_total × Q_total | 同じ物理演算を表す角度・木の自由度、整数量子化、XAG/ANGLEローダー合成を合わせて評価。 |

dqi/dfthcsosはZ_POWを禁止するため、任意角の位相回路への置換をそのまま提出できない。ANGLE 1回路の128-qubit制限も残る。以前の「303まで作業ビットを自由に増やせる」という解釈は使わない。

Walsh–Hadamard変換で古典的に位相関数を解析することと、提出回路に量子Fourier変換を挿入することは別の操作である。DQIアルゴリズム全体にはFourier変換が関わるが、今回最適化している提出対象は復号の部分回路である。

## 4. 回路パターンに直接対応する論文

### XOR–AND / 共有積

[Meuli, Soeken, Campbell, Roetteler, De Micheli, The Role of Multiplicative Complexity in Compiling Low T-count Oracle Circuits (2019)](https://arxiv.org/abs/1908.01609) は、AND/XOR/定数ネットワークからoracleを構成し、AND数とT-count、作業ビットの交換を扱う。今回の多出力ANGLE表には、この目的関数が直接対応する。論文の4 T/ANDという構成を、そのまま現在のToffoli数や128-qubit制約下の最適性と同一視しない。

### 測定による消去

[Gidney, Halving the cost of quantum addition (2017/2018)](https://arxiv.org/abs/1709.06648) はtemporary logical ANDの計算4 T、消去0 Tを示す。KickMixでは既知のANDに対するHMRと条件付きCZが対応する。測定前後で残る入力と位相を検証する必要がある。

### AIによる非Clifford最適化

[Ruiz et al., Quantum circuit optimization with AlphaTensor, Nature Machine Intelligence 7, 374–385 (2025)](https://www.nature.com/articles/s42256-025-01001-1) は、T-countをテンソル分解とgadget探索へ変換する。有限体乗算や量子化学の算術例を扱うため、一般のKAKより今回の重い算術ブロックに近い。ただし、その実験のT費用と今回のToffoli費用、補助ビット、測定契約を照合する必要がある。論文を根拠に「現在のGF(2^12)が54 CCXへ下がる」とは言えない。

現在の[DQI資源監査](resource_claims_v2_report.md)では単独GF(2^12)乗算は42 CCX、99-CCXの窓はGF(2^24)側の演算と区別されている。過去の「78→54を1477箇所」は採用根拠にしない。

## 5. このプロジェクトで実測できたこと

- [整数角度探索v3](chemistry_discrete_v3_report.md)：20表を実誤差評価。最良の数値適合案はrow908,col27の194→193、lambda_eff=46.90647745740767。手元基準との差は約0.000112であり、1 Toffoli/passの追加も支払えない。新ローダー費用は未確定で、提出しない。
- [affineローダーv3](chemistry_affine_loader_v3_report.md)：610語を変える具体例を4033 Toffoli/pass、最大128 qubitsで構成。正逆36,600遷移と全HMR位相の厳密検査、保存後の再検査、native 2 seedsが通過。これは構成法の成立であり、その例の化学精度改善ではない。
- [費用予算](chemistry_angle_search_v3_budget.json)：Q=427、非loader費用6662を維持し、整数化後もlambda=44.17を達成できれば、loaderは4489/passまで増えても基準費用を下回る。4033を絶対上限にしない。

角度の等価表現については、現在の木の最初のGivens角をπずらすと、初期ベクトルが全体として反転し、その後の線形回転でも `u -> -u` が保たれる。[符号対称性の実験](chemistry_gauge_v4_report.md)では先頭角のMSBを0にして613語を変更し、全1220ベクトルと公式数値条件を検査した。lambdaは完全一致、外積の最大差は6.11e-16だった。これは誤差を使わない同値表の生成であり、KAKを実行した結果やスコア改善とは呼ばない。

この変更は既存ローダーのbit6 XOR bit7タグを壊す。単純な定数MSB反転さえ既存wrapperの逆方向検証に失敗するため、同じローダーを再利用したり、MSBへの書込みだけを削除したりできない。batch0と次のタグ依存遷移を一緒に再合成するか、広い整数角度の符号・反射同値類からタグを維持する表を探す必要がある。

さらに[厳密なゼロ振幅の追跡](chemistry_gauge_v4_dontcare_report.md)で、1416個の角度が物理結果に影響しないと判明した。既存の高2bitを保持しても、8496個の低bit値を合成時に選べる。1349語の下位6bitを0にした一例は、公式の数値条件に適合しlambdaも変化しなかった。これは量子化誤差を使わない自由度であり、ANF/XAGのターゲット表を選ぶ際のdon't-careとして使える。ただし回路は選んだ表と厳密に一致しなければならず、loader費用の改善は別途必要である。

[既存積の削除実験](chemistry_dontcare_v4_report.md)では、2706 productを全1220 addressで検査し、単独削除の候補は0だった。k13/k14の出力寄与も、許された座標を除外した後のGF(2) rankが188/188のままで、同じバッチ内で既存積をまとめて消す候補はない。この結果は新しい積への再合成や複数バッチ間の補償を除外しない。必要条件に通る候補がなかったため、新NPZ/KMBの生成・提出はしていない。

## 6. 日本語ガイド

[forest1040氏のZenn告知](https://zenn.dev/forest1040/articles/4c00c70116953e) は2026-11-09公開で、101ページという記載も確認した。案内先は [技術ガイド](https://forest1040.github.io/google-verifiable-qcc-guide/)。解説の導入資料として使い、採点条件はpinned verifierと照合する。

本調査ではブラウザの新規タブを開いていない。今回の新しい数値候補・構成例はKaggleに提出していない。
