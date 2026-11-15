# DQI ancilla 縮約：whole-tape 解析、hybrid tail 実装、残る条件

## 判定

今回のbranchで新たに成立したのは、**同じToffoli数でforwardの16stageからrolling flagを外す、検証済みの局所controller**である。whole-decoderのQ/T減少や競技スコア改善は成立していない。残るquantum-control依存と24-helper kernelを以下で区別する。

## whole-tape の確認結果

### CNOT縮約後の追加CCX検索

入力はCNOT縮約済み `dqi_cpr_compact.kmb`、SHA-256は `3dfa80eb777a55659dcc143466d22427ccf278e198b720f24009cc921747bbcc`。既存の厳密なinput-side CCX factorizationをwindow512で適用した。363,694個のCCX、42,439個の4-qubit候補pairを調べ、barrier-free pair1,627個のうち適用可能な新規mergeは **0**。出力コピーは同じSHAであり、Toffoli改善候補ではない。詳細は `score_ancilla_postcpr_ccx.json`。

### coherent uncomputation を含めた symbolic value 解析

`score_ancilla_semantic.cpp` は、同じcompact tapeの全 **49,477,357 instruction** を処理した。q0〜839のABI inputと初期classical storageは任意、q840〜888だけを初期0とした。qubit値をcanonical XOR式とhash-consed Boolean積で追跡し、過大な式はfresh atomへ保守的に抽象化する。CNOTや同じCCXのcoherent uncomputationは検出可能。測定出力はfreshなclassical atom、conditional resetは条件つき代入として扱う。

- clean transitionを **31,138** 検出。
- possibly-nonzero scratchの最大値は依然 **49**、最初のcompact KMB indexは **17,621,207**。
- 除去またはCliffordへ置換できるToffoli-like gateは **0**。
- symbolic式のoverflowによる抽象化は3,141,738回。末尾にも6線のunknownが残るため、これは厳密な最小必要widthやcleanlinessの否定ではない。
- coherent linear/nonlinear uncomputation、同値値のCSWAP、classical condition、HMR maskを含む9つの小回路を別のexhaustive basis checkerで検査しPASS。

ここで49は**保守的に残った上界**である。以前のreset-separated interval clique49と同じ数だが、同じ解析ではない。どちらもglobal Q889の最小性を証明していない。詳細は `score_ancilla_semantic_result.json` と `score_ancilla_semantic_check_result.json`。

## 今回できたこと

`score_ancilla_hybrid_tail.py` に、forward の node18〜33 では rolling flag を選択操作の直後に HMR し、最後の node34 の flag だけを seed まで保持する controller を実装した。HMR の位相は、reverse にもともとある zero(head) query へ集約する。Toffoli は追加しない。

これにより、forward の16個の arithmetic stage から、生きた rolling flag を実際に取り除けた。単なる reset 区間の再色分けではなく、測定と位相返済の順序を変えた source-level の寿命短縮である。ただし、最後の forward と reverse の flag、および他の24-helper箇所は残る。**全decoderのQ減少やスコア改善はまだ成立していない。**

元のdecoderやKMBは変更していない。whole-decoder candidate は生成していない。

## 位相の厳密な式

tail の選択後の pair を `(u_j,v_j)`、unit による正規化後の保存 head を `p_j=v_j/u_j` と置く。採用元の `rolling_tail_early.py` / `rolling_tail_deferred.py` の不変条件は

\[
h_j=[v_j=0]=[p_j=0]=f_{j-1}\oplus f_j,\qquad f_{17}=0.
\]

これは OR ではなく XOR である。したがって

\[
f_j=\bigoplus_{i=18}^j h_i.
\]

`raw_query_extractor.query_step` は以前の head を一時的に `node_view` へ変換するが、最後に同じ involution を戻す。head 自体は更新しない。unit normalization と invertible な node view は zero 判定を変えない。そのため `h_i` は対応する reverse slot まで利用できる。

forward で `f_j` を HMR した結果を `m_j` とすると、付く位相指数は

\[
\bigoplus_jm_jf_j
=\bigoplus_i c_i h_i,\qquad
c_i=\bigoplus_{j\ge i}m_j.
\]

`score_ancilla_prefix_phase.py:PrefixPhaseLedger` は、reverse を降順に進むとき一つの classical accumulator に `m_j` を XOR して `c_i` を作る。既存の query が `h_i` を出した時点で `CZ(c_i,h_i)` を実行する。追加の量子線も Toffoli も不要である。最初の slot では `h_18=f_18` なので、その時点の既存 current flag を使い、zero query を追加しない。

最後の `f_34` は測定せず保持するため、元の seed prefix/return と reverse の quantum-controlled SWAP はそのまま使える。reverse の `f_j` は各24-helper arithmetic の間も保持する。この点を変更済みと扱ってはいけない。

## native 検証と証明の範囲

`score_ancilla_prefix_phase_result.json`:

- 17×17 の bilinear coefficient 全289成分の一致を検査。この恒等式は head predicate17bitとHMR mask17bitの全 `2^34` 割当を覆う。
- head predicate の全 `2^17=131,072` 割当を native Kickmix で3 seed検査。任意の対角probeを挟み、入力保存・scratch0・位相一致を確認した。すべてエラー0。

`score_ancilla_hybrid_tail_result.json`:

- 17slot の「隣接するtrue flagが無い」全4,181列を検査。各列の nonzero field-word representative はseedごとに変えた。
- source と同じ24bit zero query、24bit controlled swap、HMR位相補正、12bit seed seamを使用した。
- 24-helper arithmetic の寿命を模した可逆placeholderを各slotへ挟んだ。field division 全体はこの検査の対象にしていない。
- 元controllerと変更controllerを、それぞれ3固定HMR seedで検査。入力保存・scratch0・対角probeを含む位相がすべて一致。
- isolated controller のstatic Toffoliは双方 **1,984**。このpanelでの測定平均もseedごとに一致。
- forward arithmetic の controller線数は元が全17slotで1、新版が node18〜33で0、node34で1。reverseは双方1。

このpanelはflag列を網羅するが、全24bit field値・全測定分岐・全decoderを網羅したものではない。phase恒等式と元primitiveの契約によって一般化する部分と、nativeで実行確認した部分を区別している。

## actual tape 上の consuming product 数と予算

`score_ancilla_sites.py` は、既存のexact-template証明 `theory_bilinear_full_build.json` と、actual KMB のqubit mappingを使って数えた。対象input SHAは `e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7`。

1,376個のrank99 GF24 accumulatorのうち、出力24線がすべて q864〜888 にある consuming 型は192個。内訳は direct prefix63、direct return63、他のmiddle66。rolling flag と同居する direct型だけを選ぶと次のとおり。

| stage | 元controller | hybrid controller |
|---|---:|---:|
| forward adjoint consume |17|1|
| forward input scale |16|0|
| reverse head restore |17|17|
| reverse next-word adjoint consume |16|16|
| 合計 |66|34|

元の `T=382115.5671582031, Q=889` からQ888へ下げるとき、R一定で許される平均追加Tは

\[
T\left[(889/888)^2-1\right]=861.1052304502.
\]

したがって、他の変更費用を0と仮定した1siteあたり予算は、元の66siteなら **13.0470T**、hybrid後の34siteなら **25.3266T** になる。

もし23-helper consuming multiplierを+24Tで実装できれば34siteで+816Tとなり、残る予算は45.105T。ただし、これは未実装kernelを仮定した上限計算である。実際のスコア改善ではない。

### consuming GF24 product だけでは global Q は下がらない

hybrid後も、rolling flag と次の24-helper kernelが同居する。

| kernel | 呼出数 | width の理由 |
|---|---:|---|
| inverse norm |18|norm12 + nested inverseの最大12helper。最終returnのretained-child variantを含む |
| scalar half consume |17|保持したreciprocal norm12 + temporary12 |
| 上記half consume内のGF12 product |34|各callで二つの12bit halfを順に消費 |

さらにmiddleの66 consuming block、first-three chart、seed/converterのpeakを別に検証・縮小する必要がある。62T/22helper→63T/18helperというquotient-phase単体の交換は、この表の24-helper productを変更しない。

## 全flagをHMRする案との違い

位相返済を集約しても、reverseのcontrolled SWAPに使う`f_j`を量子的に再取得する必要が残る。すべてのreverse flagをarithmetic前にHMRし、arithmetic後にheadのzero predicateのprefix XORから再計算する具体的なscheduleは、seed再計算も含め追加zero query154回、追加 **3,542T** になる。このscheduleはQ−1予算を超える。これは全アルゴリズムに対する下界ではない。

今回のhybridは最後のforward flagと全reverse flagを保持するため、この再計算を避ける。その代わり34個のconsuming product siteなどが残る。

## active Nzero / Dzero 例外への適用範囲

既存 `dqi_rare_chart_v2_report.md` にある node13のNzero、node2のDzero例外は、今回のtail不変条件をそのまま満たすとは限らない。

一般のnonjoint-zero pairでは `fN=[N=0]` と `fD=[D=0]` は独立したorientation情報で、選択後に分かるのは `h=fN XOR fD` だけである。位相も

\[
m_Nf_N\oplus m_Df_D=m_Dh\oplus(m_N\oplus m_D)f_N
\]

となり、head-zeroだけでは最後のorientation項を返済できない。tailでは `fD_j=fN_(j-1)` がその不足情報を与えている。

swap chart は `(0,a)` と `(a,0)` を同じ選択pair `(a,0)` へ写す。一般additive wrapperではさらに `(a,a)` も同じpairへ入る。したがって今回のclassical suffix-XORだけで、general projective headの逆変換に必要なorientationを復元したことにはならない。新しいprojective表現にaffineなhistory関係が証明できれば、このphase ledgerはその測定位相の圧縮に利用できる。

## 再現

```bash
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python /workspace/scratch/7f542e06b7cf/gvqcc_repo/score_ancilla_prefix_phase.py
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python /workspace/scratch/7f542e06b7cf/gvqcc_repo/score_ancilla_hybrid_tail_check.py
python3 /workspace/scratch/7f542e06b7cf/gvqcc_repo/score_ancilla_sites.py
```

source hashes、全siteのKMB区間とwire mapping、各native seedの検査結果は対応するJSONに記録している。新規ファイル・直接依存・native import inventory・入力hashは `score_ancilla_manifest.json` にまとめる。baseline、既存source、他branchのrare-chart wrapperとsubmission receiptは変更していない。
