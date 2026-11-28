# DQI公式検証の低メモリ実行adapter

**最終結果：全102,400入力と公式費用の集計は完了、native depthはSIGKILLで未取得。`FINAL_VERIFICATION_JA.md` と `FINAL_VERIFICATION_RECEIPT.json` が最終票。**

V110の既存172batchを引き継ぎ、同じデフォルトsalt・公式task・測定seedで400batch/102,400入力を検証するためのadapterです。**完全に未改変の公式実行とは呼びません。**

## 採用方式

`run_dqi_exec_resume.py` は小さいsupervisorです。大きなKMBは読み込まず、`run_dqi_exec_worker.py` を逐次起動します。大回路を同時に保持するプロセスは最大1つです。workerは指定した少数のbatchを公式 `run_batch()` で検証し、結果をjournalへ書いて終了します。

最初に試したfork Pool方式は、probe3件と追加3batchを保存した後にexit137になりました。この記録は `v110_default_102400/` と `resume.stdout` にあります。採用結果は **`v110_exec_102400/`** です。fork方式の `run_dqi_resumable.py` は共通のハッシュ、公式モジュール読込、worker処理のhelperとしても使われるため、exec版と一緒に保持してください。

exec版はメモリ圧迫時のworker終了を検出し、保存済みのbatchを繰り返し計上せず、未完了の同じbatchから再開します。今回の実行は8batch/workerから開始し、メモリ変動に応じて1batch/workerへ縮小しました。

## 変更範囲と不変の内容

- 公式ソースの `verify()` と、その内部の `run_batch()` は変更しません。固定SHAの公式ファイルを実行時に読みます。
- `_circuit_sha256` は、既存のcanonical KMBとの全バイト同一性票を用い、現在の入力ファイル全体のSHAを再確認した値へ置換します。
- `_run_parallel` を実行分割・checkpoint収集用のadapterへ置換します。
- 公式のSeedSequence、デフォルトsalt、全400個のtask seed、入力生成、Simulatorの測定seed、batch検証、Clopper–Pearson上限、反復係数、平均有料数、幅、費用計算は同じです。

全batchが揃った後、**Simulatorを一度も生成しない新しいfinalizerプロセス**を起動します。公式 `verify()` は保存したbatchの結果を受け取り、公式の統計・費用・native `reaction_depth()` をそのまま計算します。

基準回路SHA：

`50b687bc142d9fe709e161404e169e7f00ee95edfdc2b6c0753b1c38c62b633a`

公式ソースSHA：

`f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65`

## 既存prefixの照合

既存172batchには `value_errors`、`phase_errors`、`paid_total` が保存されています。batch0、85、158、171を同じ公式taskで再生して、これらが元票と完全一致することを確認しました。入力は公式生成器を2回独立に呼び、シンドローム・MBUCメモリ・期待位相のSHAをそれぞれ照合しています。

元prefixは入力指紋を保存していないため、「元の保存指紋と一致」とは主張しません。公式seedを変えず再生成した指紋と、元prefixの有料数・誤り数の一致を残しています。

## 欠損するopcode内訳

元prefixには `operation_counts` のopcode別内訳がありません。再生したprobe以外の継承batchについて、この内訳は欠損します。最終 `result.json` の `shot_operation_counts` は `null` とし、`adapter_receipt.json` で **`opcode_count_breakdown_complete=false`** と明示します。得られた部分内訳は `observed_opcode_counts` に保存し、全体の内訳とは扱いません。

これは平均有料数・誤り率上限・反復係数・費用の計算には影響しません。これらに必要な値は、全batchについて元票または新しい再生から揃います。

## 再現

```bash
python run_dqi_exec_resume.py \
  --circuit /path/to/V110/dqi.kmb \
  --verifier /path/to/verify_submission_dqi.py \
  --canonical-proof /path/to/dqi_streaming_hash_102400_hash.json \
  --prefix /path/to/dqi_streaming_hash_102400_batches.jsonl \
  --output /path/to/verification_output \
  --chunk-batches 1
```

先行するfork試行で保存済みの結果も利用する場合は `--reuse-journal /path/to/v110_default_102400/batches.jsonl` を加えます。同じ引数で再実行すれば、入力回路・公式ソース・検証条件のidentityを照合してjournalから続行します。別の回路・saltへ結果を流用しません。

全batch完了後にfinalizerだけ再実行するコマンド：

```bash
python run_dqi_exec_worker.py --config /path/to/verification_output/identity.json --finalize
```

## 新しいdefault失敗の保存

`capture_default_failure.py` は、指定したbatchだけを同じ公式taskで再実行します。公式入力生成器へ渡すRNGを透過的に記録し、各shotの重み・位置・値を保存します。実際の `run_batch()` に入ったシンドローム・MBUC・期待位相との全配列一致を確認します。

```bash
python capture_default_failure.py \
  --config /path/to/verification_output/identity.json \
  --batch 158 --output /path/to/failure_capture_158
```

返されたシンドローム、全量子値、補助線、実位相、入力のE/S、誤り位置・値・重み、task seed、global shot番号を保存します。この追加再生は、全パネルに重ねて計上しません。

## 解釈上の注意

元stdoutは150batch時点で0エラーでしたが、172行のJSONLにはbatch158（start40448）の値エラー1が記録されています。44,032shot時点を0エラーと報告してはいけません。

今回のV110 defaultの失敗は、先にκ3257まで局在させたV109由来の保存回帰入力とは別のサンプリング系列です。同じ原因かどうかは未確認です。

この検証のdefault seedはV110 KMBのSHAから得ています。等価圧縮版V111の別SHAから生成されるdefault入力を新たに検証した票とは区別してください。