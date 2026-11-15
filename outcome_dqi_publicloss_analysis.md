# DQI Public27.27705の損失診断

## 実測結果

同じ有効入力と測定seedで821と9a82の完全回路を比較した。独立16,384入力は両方ともvalue error0、phase error0。既知の2つの失敗を含む512入力では、両方が同じ2入力でvalue errorを再現した。新しい失敗入力は検出されていない。

|比較|結果|
|---|---:|
|総入力数|16,896|
|syndrome出力ハッシュ一致|66/66batch|
|ancilla出力ハッシュ一致|66/66batch|
|復元したMBUC出力ハッシュ一致|66/66batch|
|phase出力ハッシュ一致|65/66batch|
|独立sampleの平均T、821|382599.971618652|
|独立sampleの平均T、9a82|382095.347167969|

phaseの差は、すでにvalue errorとなるweight31の1入力だけ。821はfalse、9a82はtrue、期待phaseはtrue。公式採点はvalue errorを先に数え、同じ入力のphaseを重複加算しない。全入力で完全同値と主張する結果ではない。

## 具体的な共通失敗

|入力|weight|最初の例外node|N modq|D modq|
|---|---:|---:|---|---|
|batch104内184|31|13|(0,0)|(1013,2476)|
|batch349内121|33|2|(1103,3094)|(0,0)|

どちらもactive quadratic chartでNまたはDがzeroになる例外。halfprofileは17,16,…,0でdegreegapがなく、cutoff18に届かない低weight入力でもない。これは既存の公開ソースclassifierによる分類と完全回路の失敗再現を結びつけた結果であり、サーバー内部traceの取得ではない。全70syndromeと4095MBUC word、測定seed、出力差は`outcome_dqi_publicloss_counterexamples.json`へ保存した。

## Publicスコアとの関係

親agentがKaggleUIでscript369719696、COMPLETE、27.27705を確認した。既知のe46逆平方根費用と5f8d化学費用、公式102400shot/-128confidenceが同じなら、DQI失敗0件では必要な平均Tが**383850.16**となり、静的最大**382934**を上回る。失敗0件で得られる総合Publicの下限は**27.29878587**で、27.27705を説明できない。表示丸めを含めても同じ結論。

1件と仮定した必要平均Tは**382095.33**で、既存のlocal fullverify382095.69と整合する。ただし、サーバーが失敗1件を開示したわけではなく、2件以上をこの上限論だけでは排除していない。

## 乱数と追加検証の意味

公式seedはcanonical回路SHAから作られ、salt指定時はSHA文字列+saltを再hashする。回路変更はdefaultの入力集合も変える。serverのseed/saltは不明。以前のlocal default102400shotをそのまま再実行しても同じ入力を試すため、今回は候補hashと無関係な1本の固定独立streamを事前に決めて比較した。candidateやsaltの探索はしていない。

今回の結果は「9a82が新しい稀な失敗を起こした」ことを示していない。一方、既存の例外2件を修復していないことは反例で確定した。次の修正対象はこのzero/infinity chartを正しく扱う一般decoder構造である。seedや無意味な回路変更による採点sample選別を改善策として扱わない。

## 再現ファイル

- `outcome_dqi_publicloss_plan.json`：事前固定した比較計画。SHA256`5ef376ae53935211601c301d3cf3d3c2eb0075092a90aea923bdd39cf4c788aa`。
- `outcome_dqi_publicloss_paired.py`：同入力、同測定seedでの全回路比較runner。
- `outcome_dqi_publicloss_821.json`、`outcome_dqi_publicloss_9a82.json`：各66batchの入力・出力hash、各失敗の入力と差。
- `outcome_dqi_publicloss_counterexamples.json`：共有入力をまとめた2反例。
- `outcome_dqi_publicloss_analysis.json`：比較結果とスコア境界の機械可読記録。

これは有限sampleの診断であり、全入力同値証明・サーバー失敗数の確定・新しい提出候補ではない。
