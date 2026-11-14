# DQI gauge: 実測maskを候補にする古典選択器

**小型化版 `72b3525cc40397c595061d466a48241d65bd47f794d2aeac428b26829a8a2229` の公式default全検証はPASSしたが、採点費用は旧e986より悪かった。** 同じ入力での追加Toffoli削減は確認できたものの、現提出はe986のまま維持することを推奨する。下に残した初回の `e25a29…` は最終集計前にプロセスが終了し、正式な検証結果が出なかった。小型化版は数学的な選択規則を変えていない。

## 公式全検証と採用判断

小型化版をseed未指定・salt空・公式default102400ショット・`log2_delta=-128`で1回検証した。

| 項目 | 結果 |
|---|---:|
| 公式検証 | PASS |
| 値エラー / 位相エラー | 1 / 0 |
| 平均Toffoli | 382110.46802734374 |
| Q / reaction depth | 889 / 40891 |
| 反復係数 | 1.1967314991687559 |
| 資源費用 | 361400858314.11945 |
| 検証時間 | 379.115秒 |
| peak RSS | 4,781,564 KiB |

旧e986のdefault結果は値エラー0、反復係数1.1912604648115832、費用359753461767.22644だった。新候補の費用は **0.4579237511%悪い**。default入力は回路hashごとに変わるため、この失敗数の差だけから新gaugeが真の失敗確率を増やしたとは判断できない。ゲートの小さな削減に対し、今回の1件の失敗が信頼上限・反復係数を引き上げた影響が大きい。

### 同じ入力での再生比較

新候補の失敗区間20バッチを再生して、失敗を絶対shot26808（batch104、batch内184、サンプルerror weight31）へ特定した。その前後4バッチ、計1024入力を旧e986へ同じ入力seed・simulator seedで再生した。

**旧e986でも同じ入力が同じ値エラーとなった。** 1024入力すべての出力syndrome、ancilla、phaseのハッシュは新旧で完全一致し、失敗の詳細記録も一致した。新候補はこの1024入力で **5,181 Toffoli、平均5.0595703125 / shot** を削減した。各バッチの差は追加ゼロmaskの費用式に従い11の倍数だった。

これは実在するゲート削減である。ただし、今回のdefault採点費用は悪化したので、スコア改善として採用することは推奨しない。回路hashやsaltの引き直し、追加のfull検証、Kaggleへの提出は行っていない。全検証JSONと比較記録は `dqi_gauge_dynamic32_compact_full102400.json` と `dqi_gauge_dynamic32_paired_comparison.json` に保存した。

## メモリ問題の修正と公式smoke

初回KMBは68,322,101命令だった。1024ショットの全バッチで値・位相エラー0だったが、最終集計の前にexit137で終了した。途中結果は `dqi_gauge_dynamic32_incomplete_smoke.json` に保存し、PASSとは扱っていない。memory不足が疑われるが、kernelのOOM記録は取得していないため、終了原因を断定しない。

12bit比較の実装を、各bitの差を別のbitへ計算する方法から、入力wordをprivateな候補copyで一時的にXORし、ゼロ判定してから元へ戻す方法へ変更した。比較1回が49命令から37命令へ減る。候補をprivate copyへ保持するため、比較対象word自体が候補元の場合にも情報を失わない。この操作は元の比較と全入力で同じ結果を返す。

小型化版も同じ108ケースでnative検証PASSとなり、selector命令数は20,197,186へ減った。完成KMBは66,729,389命令・555,327,382 bytesで、Q889・静的Toffoli382934を維持している。パスは `dqi_inputs/gauge_dynamic32_compact/dqi_ccx480_gauge128_dynamic32.kmb`。

小型化版の公式1024-shot smokeは最終JSONまで **PASS、値エラー0・位相エラー0**。reaction depthは40891、平均Toffoliは382108.3720703125で、初回版の同じ入力・seedでの全バッチ平均と一致した。seedは事前固定20261115、`log2_delta=-8`なので、これは競技の公式信頼度を満たす検証結果ではない。peak RSSは4,782,436 KiBだった。

実行時のallocator設定は `MALLOC_ARENA_MAX=2`、`MALLOC_TRIM_THRESHOLD_=65536`。公式検証コードは変更していない。回路の選択規則も変えておらず、回路hashを選別する目的の変更ではない。小型化後の回路について、seed未指定・salt空・102400ショット・`log2_delta=-128`の公式default検証を1回だけ実行した。

## 得られた改善

既存の固定128候補をすべて保持した上で、正規化された入力maskの先頭32個の値を候補に追加する選択器を実装した。各maskは12bitなので、新しい候補は0〜4095全体に届く。元の128候補を先に評価し、7で飽和させた頻度が厳密に大きい場合だけ置き換える。

16,384組の同一の古典mask入力で、既存gauge128に対する追加ゼロmask数は平均0.472290、これに対応するscanの追加Toffoli削減予測は **5.195190 / shot** だった。これは物理モデルに沿う古典選択器の比較であり、全decoderの実測スコアやKaggle Public Scoreではない。

native Kickmixで新選択器を検証し、108ケースすべてで独立な整数頻度oracleと一致した。32個の動的候補位置をそれぞれ勝者にするケース、高位bit、飽和、同点、定数mask、乱数maskを含む。入力maskは不変、作業bitはすべて0、量子位相は不変だった。量子bit数0、Toffoli数0、古典命令数21,789,898、実行65.225秒、peak RSS約316.96 MiB。

別候補のKMBも生成済みである。

| 項目 | 値 |
|---|---|
| パス | `dqi_inputs/gauge_dynamic32/dqi_ccx480_gauge128_dynamic32.kmb` |
| SHA-256 | `e25a29f427204113175678804ac6d56276ca2798bcee6facc96e4feebc940a32` |
| ファイルサイズ | 563,289,358 bytes |
| 量子bit / 古典bit | 889 / 155,441 |
| 命令数 | 68,322,101 |
| 静的Toffoli-like数 | 382,934（e986と同数） |
| 構築・境界検証 | 91.552秒、peak RSS約1,042.05 MiB |

元e986のprefix/suffixと既存gauge128部品を、全10個のバイナリ命令列で完全一致確認してから置き換えた。decoder本体はbyte-for-byteで保持した。新gauge側には量子Toffoliがないため、静的Toffoli数は変わらず、削減は実行中に0になるmaskが増えることで発生する。この表は初回の大きい実装の記録であり、全検証が完了したのは上記の小型化版である。

## 固定候補数を増やす場合との比較

すべて同じ16,384組のmaskで比較した。乱数seedは20261115と事前に固定し、回路hashや採点seedから選んでいない。

| 選択方式 | 平均ゼロmask数 | gauge128比の予測Toffoli削減 |
|---|---:|---:|
| 固定128 | 4.349182 | 0 |
| 固定256 | 4.732239 | 4.213623 |
| 固定512 | 5.108643 | 8.354065 |
| 固定1024 | 5.487671 | 12.523376 |
| 固定4096 | 6.194092 | 20.294006 |
| 固定128＋実mask32 | 4.821472 | **5.195190** |
| 固定128＋実mask64 | 5.082825 | 8.070068 |
| 固定128＋実mask128 | 5.379333 | 11.331665 |

固定256はhistogram部分だけで約25.76M古典命令を必要とする。動的32版の全selectorは約21.79M命令で、上のモデルでは固定256より大きい削減を得た。出現済みの値を候補に含めるため、1回以上出現する値へ探索を集中できる。

1つ追加でmaskが0になるたび、既存scanで11個のToffoliが不要になる。これは元ソース `adaptive_gauge64.py` の `emit_scan` が持つ `11 times the nonzero selected masks` という費用式に基づく。今回そのscan自体は変更していない。

## 点ごとの悪化がない理由

元128候補が選んだ値の真の頻度をa、新候補の頻度をbとする。置換条件は `min(7,b) > min(7,a)` である。この条件が成立するとaは7未満なので、必ずb>aとなる。同点では元候補を残す。したがって、候補値が入力maskに依存していても、任意の入力に対して最終的なゼロmask数は減らない。

virtual pivotの1回分はlabel0の頻度だけに加算する。動的候補が0、既存候補と同じ値、または別の動的候補と同じ値でも、同じ頻度を再評価するだけであり単調性は保たれる。

選択器は測定後の古典maskだけを読み、量子bitへ触れない。新しいlabelの高位5bitも使うため、回路へ組み込む際はshift、syndrome位相補償、unshiftのすべてを12bitへ拡張する。補償は各入力・各測定結果について成立するgauge恒等式であり、labelを入力依存にしても、その枝で成立する。

## この方向の上限

古典maskモデルは、4,025個の独立一様な4096値と固定zero pivot1個である。このモデルで、全4096候補へ拡張しても今回の平均追加削減は約20.3 Toffoliだった。38万Toffoli規模のDQI全体に対する改善は小さい。

さらに、全ラベル頻度の最大値Mについて

`P(M >= k) <= min(1, P(N0 >= k-1) + 4095 P(N1 >= k))`

をkごとに足した有限union boundを、整数による二項分布の確率計算で求めた。`E[M] <= 6.34684186648` となる。固定label0の平均頻度は `1+4025/4096` なので、固定zeroからの改善でも48.00593436 Toffoli未満であり、既存gauge128からの改善もこの値以下である。この上限は独立一様maskモデルでの期待値の上限であり、任意の1入力の上限ではない。

従って、単一gaugeパラメータの候補追加だけで数千Toffoliの改善を得ることは、このモデルでは期待できない。今回は低コストな動的32候補だけをnative実装した。4096候補の巨大なhistogramは生成していない。

## ファイルと再現

- `dqi_gauge_candidate_study.py` / `dqi_gauge_candidate_study_results.json`: 同一入力での8方式比較と整数による上限。
- `dqi_gauge_dynamic.py`: 古典選択器、native検証、検証済みe986への厳密なprefix/suffix置換。
- `dqi_gauge_dynamic32_native.json`: 108ケースのnative選択器検証。
- `dqi_gauge_dynamic32_build.json`: 別候補の組立結果。全decoder検証の代わりにはならない。

```bash
python gvqcc_repo/dqi_gauge_candidate_study.py --output study.json

python gvqcc_repo/dqi_gauge_dynamic.py \
  --source-root official_sources/Syed_v12/source/dqi_source/src \
  --output native.json

python gvqcc_repo/dqi_gauge_dynamic.py \
  --source-root official_sources/Syed_v12/source/dqi_source/src \
  --output build.json --build-out-dir gauge_dynamic32_new \
  --baseline dqi_inputs/821_ccx480_gauge128.kmb \
  --reference-pieces dqi_inputs/gauge128
```

元のe986回路とworkerは変更していない。別候補の公式全decoder検証はPASSしたが、費用が悪いため現提出を維持することを推奨する。採点seed、salt、回路hashを狙う調整やKaggle提出は実施していない。
