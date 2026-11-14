# DQIの稀な有限chart例外：特定と局所修復の検討

## 結論

既知の2つの失敗を、公開decoderソースの独立classical admission classifierに照合できた。両方ともactive quadratic chartの例外であり、低weight cutoff不足でもhalf-Euclidean degree gapでもない。

| fixture | weight | 最初の例外node（0始まり） | N mod q_i | D mod q_i | classification |
|---|---:|---:|---|---|---|
| shot26808、batch104内184 |31|13|(0,0)|(1013,2476)|FINITE_N、reason_mask1|
| shot89465、batch349内121 |33|2|(1103,3094)|(0,0)|FINITE_D、reason_mask2|

両方のhalf-profileは17,16,…,0で、drop2無し・half reason_mask0。

一般のN=0またはD=0を非zero pairへ切り替える**局所的に可逆な二flag回路は実際に作成し、native Kickmixで検証した**。ただし、それを現在の全decoderへ単純追加する案はQ/T予算を超え、後続のquery行列と逆synthesisも変える必要がある。新しい全decoderを生成・提出してはいない。

## 失敗入力の由来を再確認

元の保存済みfixtureから、記録された既知のRNG状態のそのbatchだけを再生した。全70syndrome、4095measurement mask、期待phaseを保存値と完全一致確認し、physical error位置・非zero値を復元した。さらに独立classifierのGF4096乗算で全70syndromeを再構成して一致させた。新しい乱数探索・hash/salt選別・量子シミュレーションはこの分類段階では行っていない。

出典classifier:

`official_sources/Syed_v12/source/dqi_source/src/controller_work/night_c27/census/reference.py`

`active_profile`（178–195行）が各nodeのN/D剰余のzeroを検査し、`half_profile`（198–218行）が別のdegree-gap条件を検査する。`classify`（221–234行）がreasonをまとめる。この公開ソースのclassifierは競技公式の採点器そのものではない。実際の既知failureと分類が一致したことを示す。

- shot26808 case SHA-256: `87c18965ac99615c6b1c20156350ac83acc398ead86fbe4a78bc2274c2c74433`
- shot89465 case SHA-256: `e92fab245e56346d002fdd3254466d3d98bc764a6db93596d46cb7b50da206ce`

case hashはcanonical JSONのphysical roots/valuesによる。元fixture、classifier、official verifierのSHAと具体的な多項式・node traceは `dqi_rare_failure_admission.json`、同じ分類内容は `score_loss_v2_report.json.known_regression_classification` に保存した。

## 既存のzero対応がなぜ十分でないか

1. `night_c27/arithmetic/gf24_arithmetic.py:inverse_deferred` はunitの逆数を前提とする。後のretained-norm inverseの実装にはinv0拡張があるが、これは0を0へ写す単体の逆元写像の拡張である。
2. 同ファイル `emit_closing`（298–305行）のconsuming productはsource≠0、またはsource=0かつ元target=0を合法domainとする。source=0に非zero targetを掛け、古いtargetをHMR消去した後では、0flagだけを追加しても消した情報は戻らない。guarded variantも同じdomainであり、任意のzero-source積を可逆にするfallbackではない。
3. `night_c27/controller/rolling_tail.py` 11–17行はactive zero headとactive zero numeratorを明示的にdomain外とする。`after_c5/extractor_width/rolling_tail_early.py` の1flag実装は `zero(v)=previous_flag XOR current_flag` というtail専用不変条件を利用して前flagを消す。active例外が混ざるとこの条件をそのまま使えない。
4. retained normを計算している途中ならN=0判定を12bit norm上で行える可能性はある。しかし元Nのnormと、chart修復後N+Dのnormは違う。両方を保持すると既存24helperピークを超えやすい。predicateの再利用には寿命・phase debt・古い値の所有関係の再証明が必要。

## 一般Möbius加算chartの局所回路

対象は(N,D)≠(0,0)。active互いに素な多項式の剰余が同じirreducible q_iで両方zeroになることはない。

```text
fN = [N == 0]
fD = [D == 0]
N' = N XOR fN*D
D' = D XOR fD*N'
```

これは非zeroの2wordを作る。逆変換は二つのcontrolled XORを逆順に適用し、元N/Dを復元してから、そのzero述語でflagをHMR消去・位相補正する。

- N,Dとも非zero：そのまま、flag00。
- N=0,D=a≠0：(a,a)、flag10。
- D=0,N=a≠0：(a,a)、flag01。

この3caseで局所データ写像の可逆性は全非joint-zero入力について証明できる。**(0,a),(a,0),(a,a)がいずれも(a,a)へ写るため、chartの履歴を捨てることはできない。** 素朴な実装は2flagを保持する。さらに良い符号化や別の不変条件があれば縮約できる可能性はあるが、ここでは証明していない。

### 実際のnative検証

`dqi_rare_chart_v2_local.py` に上の一般回路を実装した。

- N=0の4095ケース
- D=0の4095ケース
- N=D≠0の4095ケース
- 一般の非zero pair2048ケース
- 今回の実失敗剰余2ケース

合計14,335入力を4固定HMR seedで検査。prefixは選択pairとflagsを、roundtripは全入力・flag0・scratch0・phase0を確認し、すべてエラー0。これは局所部品の検査であり、全decoderや全測定分岐の網羅検証ではない。明示的な代数case分けは局所データ写像を全域でカバーする。

| 項目 | 値 |
|---|---:|
| prefix Toffoli-like |94|
| 往復static Toffoli-like |186|
| 往復の理論HMR平均 |164|
| 実測平均範囲 |163.74〜164.25程度|
| standalone peak Q |72|
| 入力data |48|
| retained chart flags |2|
| zero-query最大work |22|

回路cost内訳は、2個の24bit zero述語46T、前後4個のcontrolled24bit XOR96T、flag2個の返済static44T/平均22T。合計static186T、平均164T。初期の口頭見積もりstatic188Tは足算誤りで、native実測により186Tへ訂正した。

## 全decoderへ単純挿入すると採用条件を満たさない

### Q

standalone zero-queryはdata48+flag2+work22=72Qでよい。しかし直後のGF24 normalizerは24helperを使う。既存data864に2flagと24helperを同居させると **890Q** になり、現行889より1多い。各nodeのchartflagを逆変換まで保持する素朴な履歴なら、35node×2flagとdata864と24helperで **958Q** になる。これはこの素朴な設計の資源見積もりであり、最小Qの下界ではない。

### T

35nodeへこのwrapperを追加するだけで、平均 **35×164=5,740T**、static6,510T。採点の0→1 failure差に相当する今回の平均T予算は約1,754.92Tであり、単純追加はこれを超える。既存predicateとの融合で相殺できる場合の最適増分を計測したわけではない。

### 後続の数式

現在のquery_stepは係数head pと公開qから2×2行列

`M(p,q) = [[p/q,1/q],[1,0]]`

を未来の剰余pairへ適用する。途中でN→N+D、D→D+Nというchartを変えれば、そのshear行列も未来の各queryと逆のcoefficient synthesisへ伝える必要がある。pairだけ直して古いhead列の意味を保持したことにはならない。

一つのconditional shearを24bitごとにそのまま伝播する実装は、35×34/2=595個のold/new node組のそれぞれに最大24CCXを追加する。往復で28,560CCX/one-shearという素朴な規模になる。これは必ず必要な下界ではないが、既存99CCX productへの局所的追加だけでは済まない理由を具体化している。N-only修復・D-zeroを正しいzero headとして扱う統合や、行列積へshearを吸収する別設計が必要。

## 次の設計対象

既存テープへflagを挿入するより、projective headとcarryを同時に扱う合成単位へ広げ、zero/infinity chartの履歴を可逆に再取得できる表現を探す。その表現で未来queryと逆synthesisを一致させ、Q889と平均追加T約1755以内を両方満たして初めて全decoder候補になる。今回の局所wrapperは一般zero例外を可逆に扱う部品の実証と費用測定であり、スコア改善候補ではない。
