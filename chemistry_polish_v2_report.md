# 固定角度 chemistry 最適化の独立再計算

## 結論

共有環境の公開 Asterios 基準から、`W` と `H2_I` の最適化を独立実行した。角度表 91,500 要素は変更していない。ユーザーが報告した `lambda_eff=45.308766` の実配列は共有環境に存在せず、その数値は再現できていない。報告された `error_2=20.396 mHa` は公式許容値 20 mHa を超えるため、その時点では採用できない。

今回の基準は `lambda_eff=46.906589508624`、chemistry cost `294988786.87084424`。ユーザーの別基準 `46.905894137` と同一の配列であるとは扱わない。

## 最終数値検証

| C | 最良 lambda_eff | error_1 (mHa) | error_2 (mHa) | E_gap | T | Q | cost変化 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 44 | 46.906578536058 | 19.999999000 | 19.999999000 | 3.914898001000 | 14728 | 427 | -0.000023392% |
| 45 | 46.897594667538 | 19.999999006 | 19.999999000 | 3.914898001000 | 14807 | 427 | +0.517114334% |

数値は変更していない公式 `evaluate_dfthc_angle_words` で再評価した。回路の完全検証やKaggle提出は行っていない。C45は `lambda_eff < 46.65632810717013` に達しなければ、追加Toffoliを含めた総費用でC44基準を上回れない。

## 実装と監査で確認した点

- 公式変数は `d = H2_I - sum_b(W)`。自然変数 `(W,d)` で探索し、保存時に `H2_I=d+sum_b(W)` へ戻した。
- `angle_words/128` から公式Givens木で再構築したベクトルを使用し、保存されている連続 `U` を評価に代用していない。
- 公式FeMoCo参照、固定シフトの公式丸め、両誤差上限0.020 Ha、厳密な `E_gap>3.914898`、`Lambda>49` を維持した。
- 基準Wには7,349個の厳密なゼロがあり、`sqrt(W^2+eps^2)` は評価値を上側へずらす。最終評価・近接法は厳密な絶対値を使用した。
- `hprime` には約−1.69e-6、−9.62e-7、+5.05e-6の固有値があり、`Tr|hprime|` の折れ点をまたぐと通常の滑らかな最適化が不安定になり得る。3次元Schur補行列を保持する探索も実施した。
- 既存の `inverse_v2_chemistry_refit.py` は誤差の目標を0.01999998、gapを3.91489802としたため、公式では合格の基準を内部では不可行と判定した。最適化失敗を最適性の証明とせず、復元の受理条件と境界幅を修正した。
- 解析勾配の有限差分照合は3方向で相対誤差最大2.48e-6。二体残差は対称ペアGramと基準残差の差分式で計算し、反復中のN^4テンソル再構築を避けた。

## チェックポイントの復元

GitHub保存用チェックポイントはW/H2_Iだけを含む。`chemistry_polish_v2_restore.py` はsummary内の基準ファイルSHA256、チェックポイントSHA256、復元後の全配列の正規化SHA256を照合する。現在の環境では全配列同一を確認し、ZIPバイト同一の検査結果もJSONに保存した。異なるNumPy/zlibではZIPバイトが変わる場合があるため、配列SHA256を内容の基準とする。

```bash
python3 gvqcc_repo/chemistry_polish_v2_restore.py --base dqi_inputs/chemistry_4033/submission_asterios_full.npz --weights gvqcc_repo/chemistry_polish_v2_best_c44_weights.npz --summary gvqcc_repo/chemistry_polish_v2_summary.json --out restored_submission.npz
```

## 再現

システムPythonのNumPy/SciPyを使う。既存 `inverse_v2_chemistry_refit.py` と固定公式参照が必要。BLASは1スレッド。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -u gvqcc_repo/chemistry_polish_v2_prox.py --seconds 300 --label schur --tight --schur
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -u gvqcc_repo/chemistry_polish_v2_rank45_optimizer.py --start gvqcc_repo/chemistry_rank_extension_v2_init_1p0.npz --seconds 480 --label rank45 --tight --schur
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -u gvqcc_repo/chemistry_polish_v2_rank45_preconditioned.py --start gvqcc_repo/chemistry_rank_extension_v2_init_1p0.npz --seconds 360 --label rank45_scaled --tight --schur --boost 200
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -u gvqcc_repo/chemistry_polish_v2_collect.py
```

探索ログと結果JSONは同じ `chemistry_polish_v2_` 接頭辞で保存される。試した手法で改善が小さいことは大域最適性の証明ではない。
