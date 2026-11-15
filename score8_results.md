# score8: 27.32784 の検証済みローカル候補

**採用版のローカル総合スコアは 27.32784222155277。score6 の
27.324751494620457 から +0.0030907269323137143。28には未到達です。**
Kaggleへの提出は行っていません。新しいPublic Scoreではありません。

## XOR/ANDだけという大会ルールではない

前のXOR–ANDの下界は、固定した局所窓・入出力境界を解析するためのモデルです。
それを一般の量子回路の最適性と解釈してはいけません。

実際のインターフェースにはX/CX/CCX、Z/CZ/CCZ、SWAP/CSWAP、HMRによる
測定・リセットと古典条件付き操作があります。invsqrtでは任意角のZ_POWも
使用できます。DQIと化学のZ_POW禁止は公式検証器の明示的な制約です。
現在のkickmixパーサは通常のH命令を受け付けないため、任意のClifford+T回路を
そのまま提出することもできません。

位相多項式、ZX、等価書換え、測定によるuncompute、別の算術手順を探索することと、
最終的に受理される命令・位相・誤差・補助量子ビットの条件を満たすことを区別します。
論文のT-countと、この大会のCCX/CCZ/CSWAPや任意角回転の課金は同じではありません。
そのインターフェース実験とCCCZの厳密な再実装は[score7の記録](score7_results.md)にあります。

## 今回採用した改善

| 項目 | score6 | score8 |
|---|---:|---:|
| 化学ローダー、1 passのToffoli | 4033 | **4030** |
| 化学、全体Toffoli | 14728 | **14722** |
| 化学、Q | 427 | 427 |
| 化学、lambda_eff | 46.90647039844889 | 46.909667503120325 |
| 化学費用 | 294988037.80410767 | **294887961.3668603** |
| 総合ローカルスコア | 27.324751494620457 | **27.32784222155277** |

6 Toffoliの差はmaoxin123の公開4030ローダーと対応する角度表の導入によるものです。
独自に6個削ったという主張ではありません。公開一式の16ファイルを既存の固定SHA256と
照合し、未変更の公式検証器で78,080 shotsのPASSを再現しました。

さらに、H2_Iの独自の制約付き最適化で、公開版の費用294888332.1042627を
294887961.3668603へ370.73740243911743だけ削減しました。
近ゼロ固有値の非滑らかさに対し、小固有空間を固定する零空間法を実装し、
その後3×3対称Schur補行列の6等式へ緩和しました。方向微分チェックを通したうえで、
最終候補の公式78,080 shotsもPASSしています。

公開v27の宣言angle_wordsと実際に回路から復元する表には473要素の差があります。
最適化には全1220 addressesについて復元した実表を使用しました。
最終NPZで実際に変えた配列はH2_Iだけです。表とローダーを取り違えた合成ではありません。

| 最終化学制約 | 実測値 |
|---|---:|
| error_1 | 0.019999998000010073 Ha |
| error_2 | 0.01999998805240961 Ha |
| E_gap | 3.9148980019999726 Ha |
| Lambda | 283.0014128704472 |

誤差・gapの余裕は小さい値です。合格は固定したNPZ・回路・公式実装に結び付けており、
途中の連続最適化値を採用結果には含めません。

- [公開一式の再検証](score8_v27_chemistry_verification.json)
- [最終化学の公式検証](score8_chem_v27_full_verification.json)
- [化学の詳細と再現手順](score8_chem_report.md)
- [H2_Iパッチからの復元器](score8_chem_v27_restore.py)

## 採用版の検証と配布

| 課題 | 採用した費用 | 公式検証の結び付け |
|---|---:|---|
| invsqrt | 78673.55534364567 | 200,540,928 shots PASS、既存684106f1の同一バイトを維持 |
| DQI | 359707293756.04297 | 102,400 shots PASS、値0・位相0、既存e4e11043の同一バイトを維持 |
| 化学 | 294887961.3668603 | 今回の78,080 shots PASS |

変更していないinvsqrt/DQIの全検証は重複実行せず、完全な回路ハッシュと以前の
公式receiptで結び付けています。独立レビューでもZIP内18ファイルをすべてハッシュ検査し、
公開版と最適化版のNPZ差分、公式費用式、総合スコアを別に再計算しました。

配布物: **score8_local_candidate.zip**、63,604,196 bytes、18 members。

```text
ZIP SHA256
4eceac6db61991bf238de0533110369ddf4ef298a6bc726bcd4af8471f9c1a48

最終化学NPZ SHA256
da30619d4a668d663adc9f7f0462cfd52ba8684cc5523980f5119dc3ef90302e
```

[scorecard](score8_scorecard.json)、[全メンバーmanifest](score8_package_manifest.json)、
[独立した組み込みレビュー](score8_assembly_review.json)、
[ZIP組立器](score8_pack_portfolio.py)を保存しています。

DQIには既知のnode13 numerator-zeroの失敗が残っています。有限のdefault検証のPASSは
全入力での正当性を意味しません。この既存の限定はscore8でも変わりません。

## XOR/ANDの局所探索以外に実装したもの

### DQI: 二つの古典gaugeから選ぶ構成

69固定零点を持つ既存多項式gと、零点69を70へ置き換えたhを比較し、各maskで
より多くのゼロを作る方を選択します。h/g=(x+70)/(x+69)を使う変換、正確なmode数の
比較、CZによる位相補償、新しいpoint69 scan cell、逆変換まで実装しました。Q889です。

同じ2560入力の比較では実行Toffoliが合計12184、平均4.759375減りました。
独立GF(4096)実装による49,152基底積、全4095点、69種類のmask fixtureでも
位相恒等式と実行cell数の非増加を確認しました。既に復号が失敗する入力では位相が
異なることがあるため、全入力で旧回路と等価という主張ではありません。

公式default実行は102,400入力分の進捗で値誤り2・位相誤り0、平均Toffoli
382062.92126953125を観測しましたが、最終集計前にexit137となり通常の公式JSONは
出力されませんでした。公式PASSとして扱いません。保存された累積値に公式の
Clopper–Pearson上限とR関数を適用した復元費用は362761948064.14136で、
採用中のe4より0.84921%高い値です。誤りペナルティが小さなT削減を上回るため、
完成版ZIPには入れていません。seed/saltを変えた再採点はしていません。

失敗した2つのbatchを同じseedで旧e4と新候補に再生したところ、2件とも旧e4に
存在する同じ値の失敗でした。512入力のsyndrome・ancilla・復元maskの出力ハッシュは
一致しています。一方、weight30の失敗入力では実際の位相が変わるため、失敗領域まで
含む位相等価性は主張しません。旧e4の保存済みdefaultと新候補defaultは回路ハッシュが
異なり、入力集合も異なります。復元費用の悪化は観測された標本の結果であり、2件を
新実装による退行と解釈する根拠はありません。

[実装・検証の詳細](score8_dqi_twochart_report.md)、
[独立レビュー](score8_dqi_twochart_independent_review.json)を参照してください。

### invsqrt: 近似位相と測定補正の全体的な最適化

33一般回転をClifford/T格子に移す近似フィット、新しい中間述語・任意のlive-wire parity、
測定位相補正全体のZ/CZ化と移動を実装しました。6,194 coarse LP、14個の
全3,133,452入力での疎な位相フィット、5個の全域候補を評価しましたが、採用できる
公式費用の改善はありません。浮動小数点上だけの微差も改善に数えていません。

[invsqrtの詳細とモデルの範囲](score8_invsqrt_report.md)に結果を残しています。

### 群をまたぐ位相の再合成

三つのレジスタを混ぜた任意の線形parityをCCZの三つの引数にできるSAT合成器を
実装しました。低次の差は無料のZ/CZで補正します。GF4の例は全64基底状態で位相一致。
GF8を5 CCZ、GF16を8 CCZにする照会はそれぞれ90秒・60秒でUNKNOWNでした。
不可能という下界にも、実回路の削減にも数えていません。

## 28へ必要な変更を公式式から切り分ける

score8から28へは、三課題の費用の積をさらに約7.03019%削減する必要があります。
化学のlambda_effだけを下げる方向には、固定した対称性shiftから導かれる普遍下界があります。

Pをh1_primeの正固有値の和、Nを負固有値の絶対値の和、dを公式offsetとすると、
三角不等式から lambda_h2 >= ||d||²/4。
E_gap=c+2N+||d||²/2、Lambda=P+N+lambda_h2 より、

```text
2 Lambda - E_gap >= 2P-c >= -c
lambda_eff² >= -c E_gap > -c × 3.914898
c = -559.1324731485038
lambda_eff > 46.78617959252637
```

これは固定したXOR/AND窓の下界ではなく、公式の固定shiftと定義から得られる、
factorization形状・角度表によらない下界です。score6のT,Qと他課題費用を固定すれば、
lambdaだけを理想的に改善しても総合スコアは27.348149454261073未満です。
したがって28には、ゲート数・量子ビット数・算術手順・factorization構成の変更が必要です。
全体の回路が最適だという意味ではありません。

[計算コード](score8_target28.py)、[数値と証明のreceipt](score8_target28.json)、
[独立レビュー](score8_assembly_review.json)に前提とハッシュを保存しています。

## 出典・credit

- maoxin123, [QCC chemistry 4030-Toffoli loaders](https://www.kaggle.com/datasets/maoxin123/qcc-chemistry-4030-toffoli-loaders), CC0。
- [公開v27 notebook、固定scriptVersionId 369706978](https://www.kaggle.com/code/maoxin123/qcc-v27-4030-toffoli-coded-word-chemistry?scriptVersionId=369706978), Apache-2.0。元のchemistry、invsqrt、DQIのcreditを継承。
- Google Quantum AI / Qualtran, [公式大会・検証器](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/)。このリポジトリのreceiptは使用した検証器SHA256を固定。
- Lynn Langit, [固定shiftでのlambda_eff下界](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/discussion/753633)。公式コードから独立に導出・再計算。
- Syed Asad AliのDQI、既存のscore3 gauge実装とその出典を継承。新しいtwochartのphase変換・比較・逆変換は今回の実装。
- Nakanishi–Todo, [CCCZの測定付き6T構成](https://arxiv.org/abs/2410.00910)、前回score7で厳密再実装。
- Mazumder, [Exact T-counts of CCZ layers from an isotropy bound, v3](https://arxiv.org/abs/2610.01024v3)。Hadamard-freeで測定なしのT-count下界の範囲を確認。大会の一般回路やnative CCZ数の下界には転用していません。

