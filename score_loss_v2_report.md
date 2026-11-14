# Public Score 27.27654 の数値的説明

## 観測と推論を分ける

rootがKaggle画面から確認した新Public Scoreは27.27654、既存表示値は27.30683。新しい2提出で27.27654が一致したとの記録がある。ここでは画面を再閲覧していない。新候補DQIのローカルnative平均Toffoliは382115.5671582031、比較用旧値は382599.9932617188、Q889。新chemistryの公式ローカルlambda_effは46.906589508623554、旧値46.905894137はユーザーのログによる。

**新しい採点で合計1 failureが出たと仮定すると、公式metricの計算は27.2765361506になり、表示27.27654と一致する。これは失敗数をKaggleが開示したという意味ではない。** 集計スコアだけからvalue error/phase errorの別や失敗入力を特定できない。

また、元の27.30683提出ZIPは未取得。17メンバー保持の確認対象は今回のv1からv2であり、27.30683の元ZIPと全メンバーを厳密比較済みではない。従って以下の説明は有力な整合性検査で、ファイル差分の監査を置き換えない。

## 公式の式

Kaggle公式competition overviewのEvaluationは、3課題の基準比の幾何平均:

`Score = (Π_b cost_ref_b / cost_b)^(1/3)`

DQIの費用は `R(eps_plus) * Q² * T`。eps_plusはvalue_errors+phase_errorsを合算したClopper–Pearson片側上限、信頼度1−2^−128。公式Python `verify_submission_dqi.py` 130–174行が上限とR、385–388行が失敗分類、406–420行が集計と費用を定義する。

公式出典: https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/

## 条件付き比較

仮定は旧DQIが0 failure、Q不変、chemistryのT/Q不変、invsqrt費用不変、102400ショット、ローカルT平均が非公開採点T平均の近似、旧lambdaがログ通りというもの。旧Score自体も表示5桁しかないため細桁には不確実性がある。

| 仮定した新failure数 | eps_plus | R | 予測総合Score | 表示5桁 |
|---:|---:|---:|---:|---:|
|0|0.0008660587301657926|1.1912604648115832|27.3182295214175|27.31823|
|1|0.0009104197583220583|1.1967314991687559|27.276536150619396|27.27654|
|2|0.0009488155716079551|1.2013880602795501|27.24124938012213|27.24125|

使用した式:

```text
new_score = 27.30683 * [
  (382115.5671582031 / 382599.9932617188)
  * (R_new / 1.1912604648115832)
  * (46.906589508623554 / 46.905894137)
]^(-1/3)
```

今回のT削減は0.1266142478%。0→1 failureによるR増加は0.4592643271%。従って1件分の信頼上限ペナルティは小さいゲート削減を上回る。

同じQで本当に1件分のfailureを無くせる場合、Tを約1754.92増やしてもこの一回の比較では損益が釣り合う。ただし、有限サンプルでの1件を修正すれば真の分布でも1件分だけ改善する、という保証ではない。修正対象の失敗クラス全体で正しさを確かめる必要がある。

## 既存の失敗fixture

`dqi_gauge_dynamic32_paired_comparison.json` は、入力weight31、absolute shot26808、batch104内184について旧e986とdynamic32の両方が同一のvalue errorを起こしたことを記録する。比較1024入力のsyndrome/ancilla/phase出力hashは全一致。失敗時のancillaは全0で、syndromeが多数bit変わり、期待phase=Trueに対しactual=False。value errorが優先分類されるのでphase_errorsには加算されない。

別の既存 `dqi_inputs/paired_failure_replay_summary.json` でもweight33、shot89465の失敗が元821と最初のgauge候補で再現されている。このため、元decoderに含まれる稀な入力クラスの失敗を修正する方向には具体的な検査対象がある。新しい回路hash/saltの探索を行う必要はない。

このfixtureが新しいKaggle Public採点で失敗した入力と同じかは不明。追加監査で、weight31はnode13のactive N剰余zero、weight33はnode2のactive D剰余zeroと特定した。両方half-profileは正常。具体的な分類・source/case SHAは同名JSONのknown_regression_classificationとdqi_rare_chart_v2_report.mdに保存した。

## 再実行

```bash
kickmix_venv/bin/python gvqcc_repo/score_loss_v2_compare.py
```

この小さなスクリプトは公式CP/R関数だけを呼ぶ。回路はロードせず、シミュレーションもしない。各数値は引数で上書きでき、仮定と結果をJSONへ出力する。既定値で実行したJSONを `score_loss_v2_report.json` に保存した。
