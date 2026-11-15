# 第三pivotのゼロ分母を、最大Toffoliを減らしながら修復する候補

## 変更と範囲

`outcome_dqi_chart_norm_dqi_9a82_third_projective.kmb` は、9a82の第三pivotの正方向・逆方向の2ブロックだけを置き換える。SHA-256は `ebfb770f6fc8abc7f48287a0fa4ee6404a2e32a9facdd38449b4f7b73be05d0e`。

この変更は、第三pivotで queried denominator が0、queried numerator が非0になる場合を正しく扱う。第三pivotの numerator が0になる場合や、他のpivotの例外を一般に修復したものではない。既知のweight33反例はこの対象に入り、weight31のnode13 numerator-zero反例は対象外である。

元の第三pivotは1274 static Toffoli、新しい部品は1260。全体の最大Toffoliは382934から382920へ14減る。Qは889のまま。もともとclassical HMR maskで半分の確率で省略される22Tの位相補正が消えるため、理論平均の差は約−3Tである。実際の全体平均と検証結果は別のreceiptを参照する。

## 直接計算式と最小反例

共通GF(2^24)において、先行する2個のheadをA、B、第三raw residueをYと置く。公開定数はp=20、q=18。二つのqueryを直接まとめると

```
D = 1 + A*Y
N = p*Y + B*D
H = q*D/N
```

となる。ここで加算はXORであり、有限出力の契約はN≠0。このMöbius行列の行列式はq*p≠0なので、NとDが同時に0になることはない。

元の実装は `inv0`、加算、`inv0` を重ねる過程で、真の無限遠を0と同一視する。例えばA=B=Y=1ならD=0、N=20で正しいHは0だが、旧実装は18を返す。これは入力の識別番号や乱数に依存しない代数的反例である。

実際のweight33反例では、第三pivotの残差がN=(1103,3094)、D=(0,0)。保存されたphysical roots/valuesから独立の多項式計算を行うと、新しい正しいheadは0、旧実装のheadは9513431となる。head0を許容して多項式更新を続けると、全33段を正しい終端まで実行できる。

## 一つのinfinity flagで正しく表す

1個のflag fを使い、有限値aを(a,0)、無限遠を(0,1)で表す。

- 逆元は `a <- inv0(a); f <- f XOR [a==0]`。0と無限遠を交換し、非0有限値は通常の逆元になる。
- 非0の公開定数によるスケールはaだけに作用し、fを保つ。
- headの加算はf=0のときだけ行う。f=1なら無限遠を保つ。

これを旧実装と同じ3回の逆元・2回のhead加算へ適用すると、射影直線上のMöbius写像そのものになる。N≠0なら最後のfは必ず0なので、prefixの境界でHMRリセットしても位相は発生しない。returnはf=0から逆順に操作し、初期のYが有限なので最後のfも0に戻る。

逆元の前後で `[a==0] == [inv0(a)==0]` が成立するため、returnのzero toggleを逆元の内部へ移しても同じ可逆写像になる。

## 23Tのzero判定を既存normへ統合

初版は24bitのAND ladderでzeroを判定し、1回23Tを使っていた。現在の逆元はすでにGF(2^24)→GF(2^12)→GF(2^6)→GF(4)のnormを計算している。体のnormは入力が0であるときだけ0になる。既存の `cubic_inverse130.inverse_six_cubic` は、計算中の2bit GF(4) normを利用して、任意のdirty flagへzeroを1CCXでXORする `zero_flag` 引数を備えている。

`outcome_dqi_chart_inverse_norm.py` は元のmatched inverseの局所的な派生版で、引数をこの既存APIまで通す。借用flag以外の補助量子ビットは追加しない。6回のzero判定が23Tから1Tへ変わるので、初版から132Tを削減する。

各逆元の6bit child-norm HMR maskは、正方向で作ったものを対応する逆方向の同じ値で支払う。新しいflagは一貫してdirty targetとしてXOR更新される。既存normの消去と位相補正はそのまま使用している。

## 部品検証

`outcome_dqi_chart_norm_component_report.json` に記録した検査は次の通り。

- 4,098組の独立classical例で、逐次射影演算と直接の行列式を照合。
- そのうち有限出力域の3,074入力を、4個の固定HMR seedでnative KickMix実行。
- prefixのhead、未変更データ、全scratchの復元を確認。
- prefixとreturnの間へ入力ごとに異なる24bit位相probeとCCZを挿入し、閉じた回路の期待phaseを独立oracleで照合。
- value error、phase errorは全て0。実測Q889、prefix624T、pair1260T（検査用CCZを除く）。

初版に対する別agentの境界検査は `outcome_dqi_chart_review.json` と `.md`。norm統合版への追加レビューは別receiptに記録する。有限sampleの検査だけを全入力の証明と呼ばず、上の射影写像とzero-norm不変条件を一般的な根拠として用いる。

## KMBへの組み込みとmask所有権

`outcome_dqi_chart_norm_splice_report.json` に全チェックを記録する。

1. 元のprefixとreturnは、unmodified公開部品のKMBに対し、opcode、量子operand、古典operandの単射対応がそれぞれ1か所だけ完全一致する。
2. 旧3本の6bit saved child maskと1bit zero maskは、prefixとreturnで同じphysical bitへ対応する。中間bodyはこれら19bitを一度も参照しない。
3. 削除したscratch bitの次の残存コードによるアクセスは、無条件上書きか未使用である。削除した書き込みが後続の読み取りへ影響しないことを確認した。
4. heads、current、24bit bankは両側で同じphysical qubitに対応する。補助qubitとfresh return flagは境界でcleanなので、各側の元の割り当てに対応させる。
5. 新しい古典bitは全て既存範囲の後ろ、b208087からb208166へ割り当てる。正方向と逆方向は同じ割り当てを共有し、3本の6bit deferred maskが確実につながる。
6. 元のregister宣言と、この2ブロック以外の全operand columnはそのままコピーする。量子bitの追加はない。

## 全decoderの判定

norm統合版を完全DQI回路に組み込み、同じ入力を使うpaired検査と、公式default102400-shot検証を完了した。

|検査|結果|
|---|---|
|固定した独立16,384入力|value error0、phase error0、MBUC差0。9a82と全出力hash一致|
|既知weight33、batch349内121|9a82のvalue error1件を修復。新回路はvalue/phase error0|
|既知weight31、batch104内184|未修復のvalue error1件が残る。この失敗入力の位相は9a82と異なるが、両者ともvalue errorに分類|
|公式default102400-shot|PASS、value error0、phase error0|
|全体Q|889|
|全体最大Toffoli|382920|
|全体実測平均Toffoli|382092.5565332031|
|公式DQI費用|359731797766.2993|

公式defaultはseed未指定、salt空、log2_delta=-128。9a82の旧default平均382095.68779296876との数値差は−3.13125976565T。ただしdefaultの入力集合は回路SHAごとに変わる。共通の独立16,384入力での差は−2.8095703125Tで、理論平均−3Tと整合する。これらの数値差を正確な全入力差として扱わない。

結果とSHAの結び付けは `outcome_dqi_chart_norm_paired.json`、`outcome_dqi_chart_norm_paired_comparison.json`、`outcome_dqi_chart_norm_full_verification.json` に記録する。

local defaultのseedは回路SHAから定まる。今回の候補更新は、同じ写像の資源削減に基づくものであり、seed、salt、表示スコアを探すための変更ではない。Publicスコアが上がったとの主張は、実際に採点が完了するまで行わない。
