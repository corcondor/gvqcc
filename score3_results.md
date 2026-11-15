# score3: 公式全検証を通過した回路削減

2026-11-15。逆平方根の積キャッシュと、DQI の全4096ラベルからのゲージ選択を採用した。両候補の公式全検証は PASS。化学成分は既存の検証済み score2 family を保持する。提出 ZIP は完成・保存済みだが、Kaggle への送信と新 Public Score の確認は未完了。

## 実測の改善

| 項目 | 比較元 | score3 | 差 |
|---|---:|---:|---:|
| invsqrt 量子ビット | 46 | 46 | 0 |
| invsqrt 平均 Toffoli | 1479.7500405453395 | 1478.7506100300882 | −0.9994305152513334 |
| invsqrt 公式コスト | 78719.52914734723 | 78673.55534364567 | −0.058402030855% |
| DQI 量子ビット | 889 | 889 | 0 |
| DQI 平均 Toffoli | 382115.5671582031 | 382095.68779296876 | −19.879365234344732 |
| DQI 公式コスト | 359753461767.22644 | 359734745778.9876 | −0.005202448406% |
| DQI 反復係数 R | 1.1912604648115832 | 1.1912604648115832 | 0 |

化学成分を同一にして公式の幾何平均式へ代入すると、比較元に対する総合スコア倍率は **1.0002120947396507**、改善率は **0.021209473965%**。これは固定したローカル比較元との計算であり、新しい Kaggle Public Score の実測ではない。各回路のデフォルト検証乱数はハッシュに依存するため、有限ショット平均の差を完全な同一入力比較とは扱わない。

比較の元データ:

- `results/2026-11-14/invsqrt_upstream_verification.json`
- `results/2026-11-14/v2_candidate_full102400.json`
- `score3_invsqrt_full_verification.json`
- `score3_dqi_full_verification.json`
- `score3_cost_comparison.json`

## 1. 逆平方根: 同じ積の再計算を除去

q21 が測定でリセットされた後の未使用区間を利用し、q10 と q11 の積を保持した。最初の CCX の前後で dirty target q13 を q21 へ XOR すると、q21 には q10 AND q11 が残る。区間中に制御ビットは一時的に変化するが、2回目の使用時には形式的に元の値へ戻る。このため2回目の CCX をキャッシュからの CX に置き換えられる。

最後に q21 を HMR し、新しい測定結果 b387 による条件付き CZ で測定位相を補正する。各測定分岐の符号が相殺することを確認した。全 Z_POW 命令は同一で、数値近似の精度を変更していない。

- 変更: CCX −1、CX +3、HMR +1、CZ +1。
- 静的 Toffoli-like: 1551 → 1550、Q46。
- 数学的な期待 Toffoli 削減は正確に1。有限ショットで観測した差は上表の値。
- 公式検証: **200,540,928 shots PASS**。
- 最大 error/tolerance: **0.9986660009092673、x=159**。元回路と同じ。
- 独立レビューでは、局所パッチの全命令差分、補助ビットの初期化、制御ビットの帰還、測定位相補正、KMB/KMX の一致まで確認した。

回路 SHA256: `684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a`。

実装・証明: `score3_invsqrt_product_cache.py`、`score3_invsqrt_cache_proof.py`、`score3_invsqrt_ancilla_report.md`、`score3_independent_candidate_review.json`。

## 2. DQI: 最頻ラベルの厳密選択

従来は128候補の範囲でゼロマスクが増えるゲージを選択していた。新候補は全4096ラベルについて正確な最頻値を求める。入力4025語と仮想ゼロ1語を13ビットの古典ワイヤへコピーし、70個の sentinel 4096 を足して4096語とする。Batcher の odd-even merge network で整列し、最初の4026語だけを12ビットの正確な run count で集計する。同数の場合は最小ラベルを保持する。

元論文の odd-even merge 再帰と比較器数を照合した。p=12 のネットワークは `(p*p-p+4)*2**(p-2)-1 = 139263` 比較器。比較交換を81命令に縮めたため、全候補を調べる selector の古典命令数は12,336,839となり、旧固定128候補の12,887,775より少ない。

この selector はすべて古典ビット上の計算で、追加の量子ビットと Toffoli は0。選択した12ビット全部を既存のシフトと位相補償へ渡す。元のデコーダ本体はそのまま保持する。全候補の最頻値を選ぶため、選択によるゼロマスク数は旧候補範囲の選択以上になる。全回路の平均 Toffoli の改善は公式検証で別途実測した。

- Q889、58,869,042 operations。
- 静的 Toffoli-like 382934 は同じ。実行時の平均を削減した。
- 公式検証: **102,400 shots、value errors 0、phase errors 0、PASS**。
- デフォルト seed、salt、信頼水準を保持。
- ネットワーク・比較器・カウンタ・sentinel 除外・入出力保存は単体検証し、最終生成物のハッシュと公式結果を結び付けた。

回路 SHA256: `9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1`。

実装・証明: `score3_gauge_sort.py`、`score3_gauge_sort_proof.md`、`score3_gauge_sort_native.json`、`score3_independent_candidate_review.json`。

参考文献: K. E. Batcher, *Sorting networks and their applications*, AFIPS Spring Joint Computer Conference, 1968, pp.307–314. [DOI](https://doi.org/10.1145/1468075.1468121)、[著者の公開本文](https://www.cs.kent.edu/~batcher/sort.pdf)。今回参照した箇所は odd-even merging、sorting networks、および Appendix A。

## 3. 化学: 今回は検証済み family を保持

score2 family の公式78,080 shots PASSを各 member のSHAへ結び付けた。lambda_eff=46.906472675810164、T14728、Q427、cost294988052.12610483。今回の総合改善へ化学の新規改善は加算しない。

今回の探索記録も保存する。B143からB142への単純なprefix削減では、残したprojector spanへの緩和問題でも error_2 の下限が27.380151645 mHaとなり、20 mHa制約を満たせない。これは同じ残存prefixについての否定結果であり、別の角度テーブル全般を否定するものではない。

整数角度の ±1/2/4/8/16 候補を実際に変更した探索と再フィットも実行したが、採用基準を満たすものは得られなかった。連続変数の良い目的値を、丸め後の有効な提出改善として数えない。詳細は `score3_chemistry_*` に記録する。

## 提出物と状況

ZIP は root に `invsqrt.kmb` と `dqi.kmb`、`dfthcsos` に `submission.npz` と15個の ANGLE KMB、合計18 member。全memberのSHA・CRC読み戻し検査を実施し、3成分の公式PASSへ結び付けた。各 ANGLE 回路については公式の128量子ビット上限を守る。

- サイズ: **63,552,631 bytes**。
- ZIP SHA256: `5a3011d3f208a0bae3b1e1bfb9b763ac8c7201f4de35a74d772699949b971882`。
- 再現用 builder: `score3_submission_build.py`。
- manifest: `score3_submission_manifest.json`。
- [保存済み提出ZIP](https://chatgpt.com/library?file_id=libfile_fde3_f-5777877931508191aa220046e9195296_e9171c3d17a08191be76d9438ecb9078&account_id=personal)。

Kaggle画面で確認した既存最高値は27.30683、直近の旧候補は27.27654。新しいscore3のPublic Scoreは未取得。自動アップロード用に保存ファイルを取得するブラウザー操作は、`chatgpt.com` に対するホストのセキュリティ制限で拒否された。制限を回避せず、Kaggleの提出画面へ説明文を入力してファイル選択待ちにしている。

この作業ではKaggleへ新規送信していない。公開スコアの改善を主張する前に、この固定ZIPを提出し、その結果を確認する必要がある。
