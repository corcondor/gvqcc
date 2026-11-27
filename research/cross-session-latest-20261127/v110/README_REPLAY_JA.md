# V110確認・追加圧縮の再現と独立検証

このZIPは、提供V110を基準に得た **化学301,675命令、InvSqrt27,533命令、DQI61,700,935命令** のコードと証拠である。完成18ファイルは別ZIPにある。DQIの既知失敗は残り、有料期待費用と幅の改善は主張しない。内部のV111という名前は、このタスクの作業名であり、他のV111/V112版との統合を意味しない。

## 内容

- `report/`: 結果・数学・保証範囲の日本語報告。
- `audit/`: V110実体と追加版のSHA/計数、V110独立ANF再検査、期待費用の厳密比較。
- `official_v110/`, `official_v111/`: 成功票と実行ログ。exit137/−9の票はメモリ停止であり回路FAILでもPASSでもない。
- `dqi_verify_resume/`: 公式run_batch/統計式を用いた省メモリ実行分割とcheckpoint。完全未改変の公式実行とは区別する。
- `baseline_evidence/`: 提供V110の局所合成器・独立ANF・証明ストリーム。既存成果の再現用であり新規として加算しない。
- `chemistry/`: 今回のアフィン・位相圧縮、終端二次閉包証明、独立チェッカー、検査結果。
- `dqi_compaction/`: 定数・古典liveness圧縮、別実装の独立検証、3seedの64合法入力比較。
- `invsqrt_replay/`: 完成版をV110からbyte-identicalに再生成する可搬構成。
- `angle_research/`: 固定位相関数の双対証明、角度・追加特徴探索、全入力特徴の再生成コード。
- `coefficient_research/`: 固定角度語表の直交ゲージ探索。採用した改善なし。
- `dqi_diagnosis_and_kernels/`: 失敗の局在、測定位相反例、独立検査、零判定・座標切替KMB。全体DQI修復は未完成。

`MANIFEST.json`はZIP内の全ファイル（manifest自身を除く）のサイズとSHA-256を記録する。

## 依存

Linux/POSIX、Python 3.10以上、NumPy、C++17のg++を用いる。KickMixを使う検査は配布版`kickmix==1.0.0`で実行した。角度・係数の数値研究にはSciPyも必要。独立C++チェッカーはassertを検査に使うので **`-DNDEBUG`を付けない**。

公式検証器・既存パーサ・V110合成器は元のコードとして収録する。新しい独立実装として再計上しない。

## まず小さな独立証明を確認する

以下では完成18ファイルを`/path/to/extended/`、提供V110の18ファイルを`/path/to/V110/`へ展開したとする。

```bash
python angle_research/check_rotation_margin_dual.py /path/to/extended/invsqrt.kmb angle_research/angle_fit/exact_rotation_margin_dual.json --out rotation_dual_checked.json
python invsqrt_replay/invsqrt_joint/check_eight_input_fiber.py --input /path/to/extended/invsqrt.kmb --out eight_inputs_checked.json
python chemistry/check_tail_certificate.py /path/to/V110/dfthcsos chemistry/bank0_tail_closure_certificate.json --out tail_checked.json
python dqi_diagnosis_and_kernels/check_confluent_failure.py --fixture dqi_diagnosis_and_kernels/inherited_batch345_shot195.npz --corpus dqi_diagnosis_and_kernels/dqi_64_legal_inputs.npz --out dqi_confluent_checked.json
python dqi_diagnosis_and_kernels/prove_zero_chart_kernels.py
```

DQI局在チェッカーの既定fixture/corpusは研究時の配置を参照するため、上記のように同梱ファイルを明示する。他の小さな証明書はスクリプト自身のディレクトリから読む。

## InvSqrtを完全再生成する

可搬配置と全依存を`invsqrt_replay_manifest.json`に記録した。基準InvSqrtも小さいため収録している。

```bash
cd invsqrt_replay
bash invsqrt_joint/replay_v111.sh v110/all_tasks/invsqrt.kmb extracted/evidence/invsqrt/prior/live_product_reuse_fast.py v110/evidence rebuilt/invsqrt
python exact_invsqrt_expected_cost.py v110/all_tasks/invsqrt.kmb --out rebuilt/invsqrt/expected_baseline.json
python exact_invsqrt_expected_cost.py rebuilt/invsqrt/final/invsqrt.kmb --out rebuilt/invsqrt/expected_candidate.json
```

完成SHAは`0dd56a108a82391b8d5ebfcb908df0285c961d3cf89b1b1b7dae0ce882ac0e56`。再生成driverは8入力証明と局所carry試作品の検査も実行する。局所carry試作品は全体37Qかつ+2有料のため、完成回路へ取り違えない。

期待有料`11237/8`、T`11/2`、一般回転`33`は基準・追加版で一致する。期待費用スクリプトは既に全入力検証した位相余裕定数を使っており、その余裕自体の独立再検証ではない。

## 化学を再生成する

`chemistry/README_Chemistry_V111_JA.md`のコマンドを、入力ディレクトリを提供V110の`dfthcsos/`へ置換して実行する。`affine_care_general.py`、`phase_coset.py`の順で301,675版を得て、`vendor/verify_native.py`で全正逆入力・HMR位相係数を検査する。`submission.npz`は同じファイルをコピーする。

終端閉包証明は固定C、即時二次訂正、非線形生成なしという限定の下で必要十分である。詳細な仮定は報告書に記載した。固定終端から任意回路全体の下界へ拡張してはいけない。

## DQIの命令削減を再生成する

`dqi_compaction/README_DQI_Classical_JA.md`の順に、`constant_sweep`→`dead_classical`→`classical_constants`を実行する。各段は別の`check_constants`または`check_dead`で確認する。大きなKMBはmmap/ストリーム処理し、Python命令オブジェクトへ全展開しない。

完成SHAは`8010980d566e6b16d255bfa7f00b37fb0d00c62978cd8bd3932b1981adc05841`。有料イベント・HMR・位相・全最終古典ビットを保存する。既知失敗の修復にはならない。

## 角度研究を再生成する

`angle_research`には、研究時と同じ中間InvSqrt KMB、33特徴の記録、LP結果、厳密双対証明を収録した。巨大な全入力特徴配列は再生成可能なので省略した。

研究コード中の旧作業環境の絶対パスだけ、配布時に`vendor/`と`angle_data/`への相対パスへ変更した。これらの変更は`PACKAGING_PATH_ADAPTATIONS.json`に原SHAと配布SHAを記録している。アルゴリズムの変更はない。

```bash
cd angle_research
mkdir -p angle_data
python prepare_angle_features.py
g++ -O3 -std=c++17 extract_angle_features.cpp -o extract_angle_features
./extract_angle_features angle_fit/ops.bin angle_data 0
./extract_angle_features angle_fit/ops.bin angle_data 1
python prepare_angle_targets.py
python fit_rotation_angles.py
```

C++抽出器の引数形式は先頭usageを確認すること。追加特徴の探索は`scan_phase_features.py`、C++抽出器の追加specs引数、`sweep_rotation_features.py`の順。全入力配列を生成すると数百MBの作業領域が必要である。

角度の双対は固定33特徴・固定巻き数の上限である。KMBの128bit角度と公式最終64bit丸めを区別し、整数格子上の最適性を一般KMB角度の最適性と読み替えない。

## 公式検証の扱い

化学の新回路は未改変公式・2salt各78,016shots。InvSqrtの新回路は未改変公式・全合法3,133,452入力×1shot。既定64shots/入力は未実施。

DQIの大規模検査はハッシュI/Oと実行分割を省メモリ化しているため、必ず最終集計票の`adapter`/`scope`と報告書を参照する。元の172batchにはoperation-count全内訳が保存されていない。値/位相失敗数と有料総数は保存され、統計と費用の計算に使えるが、欠損内訳を捏造していない。

観測平均の微差を期待費用削減へ計上しない。大規模標本がPASSしても、全合法入力で誤りがないことや、保存された失敗が修復済みという意味にはならない。