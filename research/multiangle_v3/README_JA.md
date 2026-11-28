# GVQCC ANGLE v3：構成的合成器、測定消去、アドレス再分割

2026年11月23日の **35方式×4実角度表×15ローダー＝2100回路** の研究索引。

- [方法と全結果の日本語レポート](REPORT_JA.md)
- [測定消去とHMR記号位相証明](hmr_patterns.py)
- [低位ANF座標変換・ブロックハイブリッド](affine_patterns.py)
- [低位3/5/6bitと多出力基底圧縮](partition_patterns.py)
- [低位6本選択の可逆コンパイラ](permutation_patterns.py)
- [最小実験テスト](test_new_patterns.py)、[全構造テスト・負の位相テスト](test_partition_and_permutation.py)
- [全2100回路の統合結果JSON](../data/multiangle/2026-11-23/v3/MASTER_SUMMARY.json)
- [462通りのlow6線選択探索](../data/multiangle/2026-11-23/v3/screen_c46_462.jsonl)

このリポジトリにはコードとJSONLの数値原票、KMXのSHA-256台帳を保存する。再現用の4つのNPZと全2100本のKMXは容量のため、同じ会話に保存したZIPに含める。原本のNPZ・KMX・公式KickMixの権利条件は上流のものに従う。

## 前提と実行

Python3.11以降、NumPy。`research/gvqcc_multiform/multi_angle_synthesis.py` は前回v2の**SHA固定コピー**であり、計測の再現性のためv3用コードと分けて保持した。実データNPZはユーザー保管ZIPから取り出す。

```bash
python research/multiangle_v3/test_new_patterns.py -v
python research/multiangle_v3/test_partition_and_permutation.py -v
python research/multiangle_v3/run_partitions.py \
  --seeds PATH/c46_public_v8.npz \
  --out PATH/NEW_OUT_DIR
python research/multiangle_v3/scan_permutations.py \
  --npz PATH/c46_public_v8.npz --start 0 --stop 462 \
  --out PATH/c46_screen.jsonl
```

## 必須の注意

- 全2100本はPythonビット並列で全合法アドレス・dirty target・scratchを検査済み。HMR版の各測定変数について位相多項式の係数ゼロを確認済み。
- ネイティブKickMixで**実データ全回路の公式チェックは未実行**。CIでは合成用fixtureのKMX→KMBパースをテストするのみ。
- 公式スコアは**未更新**。10038 CCX/片道は公開3357T/片道より高価。物理パラメータR/B/C/Jの同時再学習は未実装。
- `Q×CCX` はローダー間の単なる比較値で、全化学回路の正式な `lambda_eff*T_total*Q_total` ではない。
