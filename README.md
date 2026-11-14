# GVQCC — DQI 回路の解析・計算

[Google Quantum AI — Verifiable Quantum Circuit Compilation](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/) の DQI 課題に向けた、回路解析と有限体演算の検証コードです。

大きい KMB 回路を全展開せずに調べる監査ツール、共有積を式に起こす解析器、有限体演算の検証コードをまとめています。2026-11-14には、実際の公開 `821bf8d157c0` 回路を改良し、公式DQI検証コードの102,400ショット検証まで実施しました。大きい回路ファイルは再現スクリプトで取得・生成します。

## 今回の実測結果

**ゲート数は減りました。Kaggleでのスコア改善はまだ確認されていません。**

| 変更 | 確認できたこと |
|---|---|
| 同制御CCXの可換移動と置換 | 8ブロック×12組で毎ショット96 Toffoliを削減。Q=889を維持 |
| 古典gauge候補64→128 | 同じ入力の256ショット比較では、さらに平均3.8242 Toffoliを削減。量子ビット増加なし |
| 全回路検証 | 102,400ショット、公式信頼度設定でPASS。値エラー1、位相エラー0 |
| 元回路とのエラー比較 | 失敗した同一入力を元回路で再実行し、同じ値エラーを確認。該当5バッチの全量子出力・位相が一致 |

続いて全102,400入力を固定した比較も完了しました。元回路 `382599.91934570315` → 候補 `382499.49657226563`、平均 **100.4227734375163 Toffoli削減**です。両方とも値エラー1・位相エラー0、反復係数も一致し、同じ入力集合での資源コストは **0.0262474633%改善**しました。記録は [dqi_gauge_expand_results.json](dqi_gauge_expand_results.json) にあります。

併合候補のSHA-256は `aafed8b0fa2bbfde21f47672a5e548a84a6d42d735e800557efbb2c04c310f09` です。平均Toffoli数は `382499.49657226563`、ローカルDQIコストは `361768802303.6398` でした。公開元回路の別サンプルでのコスト `360209905486.0156` より悪化しています。今回の1件のエラーによる信頼上限・反復係数の増加が、小さなゲート削減分を上回ったためです。同一入力集合での比較と、異なるハッシュから生成された採点サンプルの比較は区別してください。

詳しい変換証明・入力固定比較・出典は [dqi_ccx_peephole_report.md](dqi_ccx_peephole_report.md)、[dqi_gauge_expand_report.md](dqi_gauge_expand_report.md) を参照してください。過去worker v13の非CCX行を消す不具合も再現し、バイナリの非変更部分を保持する実装へ置き換えています。

## 実回路の再現と検証

Python 3.12、CPU、約5 GB以上の空きメモリが必要です。今回の102,400ショット実行は約327秒、最大RSS約4.53 GiBでした。ハードウェアによって時間は変わります。GPUは使用していません。

```bash
python -m pip install kickmix==1.0.0 numpy==2.5.4
python reproduce_dqi_candidate.py --work-dir dqi_run_1
```

公開の元回路・生成ソース・検証コードをSHA-256で固定し、改良回路を生成してから全ショット検証します。元ソースの証明書は変更せず、新しい結果を別に記録します。既存ディレクトリへの上書きは拒否します。

元の提出ZIPがある場合は、検証後にDQIだけを差し替えられます。

```bash
python reproduce_dqi_candidate.py --work-dir dqi_run_2 --baseline-zip ORIGINAL_SUBMISSION.zip
```

`invsqrt`とchemistryの全ファイルをバイト単位で保持します。すでに生成・検証したDQIを使う場合は [replace_dqi_submission_usage.md](replace_dqi_submission_usage.md) のコマンドを使ってください。これらの処理はKaggleへの提出を自動では行いません。

## Chemistryの追加計算

正確なFeMoCo参照データと実際の4033ローダーを照合し、7bit・6bit化、C44→43、列の直交回転を調べました。採用できる改善は得られませんでした。

既存の角度を単純に丸めて固定した場合、重みを任意に変えられる緩和問題でも、最良の `error_2` は7bitで **0.207501108 Ha**、6bitで **0.303254552 Ha**です。許容値は **0.020 Ha**。この6通りの固定表に対してW/H2_Iの再フィットだけを長く続けても合格しません。角度・Givens treeを変える案は、この結論の対象外です。

詳細と再現コードは [chemistry_report.md](chemistry_report.md)、全数値は [chemistry_experiment_summary.json](chemistry_experiment_summary.json) にあります。現在の全回路が大域最適であるという主張はしていません。

## 使うツール

| 入口 | 目的 |
|---|---|
| `gvqcc_dqi_audit.py` | KMB/XZ/ZIP の形式・条件付き命令・scratch状態・指定区間を低メモリで調べる |
| `symbolic_block_analyze.py` | compute区間全体を疎なBoolean多項式へ変換し、出力の式・次数・GF(2)ランクを求める |
| `boolean_block_analyze.py` | 独立入力12個以下の純粋な小ブロックを全入力で検証する |
| `inverse_specialized.py` | 入出力以外の量子作業ビットを使わない専用べき乗回路を生成・検証する |
| `pebble_search.py` | 中間値の保存・再計算・消去の順序を探索する |
| `full_inverse_verify.py` | 探索した逆元回路を実ゲート列へ展開し、全入力・全測定位相を検証する |
| `compare_dqi.py` | 公式検証で得たQ・T・失敗率係数から改善条件を計算する |

詳しい仕様・測定結果・一次資料は [README_ja.md](README_ja.md)、KMB監査の説明は [kmb_profile_notes.md](kmb_profile_notes.md) を参照してください。

## ローカルでの検証

Python 3.12で動作確認しています。元の解析コードとKMB変換・ZIP差し替えは標準ライブラリだけで動きます。新しいgauge生成・公式全回路検証には上記のKickmixとNumPyが必要です。KMB監査とそのテストには C++17 コンパイラ（`g++`）も必要です。Linux、WSL、Kaggle CPUでの利用を想定しています。

```bash
python3 -m unittest discover -p 'test_*.py' -v
python3 test_boolean_block_analyze.py
python3 test_symbolic_block_analyze.py
python3 inverse_specialized.py
python3 pebble_search.py
python3 full_inverse_verify.py --export-kmx
```

最後の3コマンドは `*_results.json` を更新します。`--export-kmx` を指定すると、完全な逆元ゲート列も再生成します。

## 実回路の区間を取り出す

入力パスを実際のファイルへ置き換えて実行します。出力ディレクトリは新しい名前を指定してください。

```bash
python3 gvqcc_dqi_audit.py \
  --circuit /path/to/dqi.kmb.xz \
  --index-mode legacy-v4 \
  --scratch-start 840 \
  --scratch-initial zero \
  --window 10529430:10534531 \
  --region 22500000:27350000 \
  --out-dir dqi_audit_run1
```

- `events.jsonl` は CX・古典命令・PUSH/POP も含む全命令を保存します。
- `run_summary.json` に入力KMBのSHA-256と解析条件を残します。
- `--scratch-initial zero` は、対象課題でscratchがゼロ初期化されるという前提を明示します。
- 区間は始点を含み、終点を含みません。
- `possibly_nonzero` は保守的な推定です。必要量子ビット数や安全な再利用を証明するものではありません。

G1/G2の共有Toffoliを調べる場合は、両方を作るcompute区間全体を対象にします。途中で書き換わるG1を開始時の固定入力と見なしたり、依存関係を含むCXを省いたりしないでください。記号解析では入口の全入力とゼロ／1の作業線を明示します。

```bash
python3 symbolic_block_analyze.py --help
```

## 検証済みの逆元カーネル

GF(2¹²)は `x^12 + x^6 + x^4 + x + 1` を使用し、逆元関数を0では0に延長しています。

| 用途 | 入力を含む全量子ビット数 | CCX |
|---|---:|---:|
| 逆元を保持し、中間値を消去 | 60 | 276 |
| 同上 | 72 | 240 |
| 逆元の最下位ビットを位相に使い、作業領域を全消去 | 48 | 327 |
| 同上 | 60 | 267 |
| 同上 | 72 | 240 |

全4096入力について、入力保存・出力・空き領域のゼロ・各HMR測定結果の位相補正を検証しました。測定結果を独立した記号変数として扱い、全測定分岐を確認しています。これらは初期調査の無条件算術部品です。実際の821回路には、より効率のよい既存の有限体演算がすでに組み込まれています。この表を現在の提出の改善幅として使わないでください。

## GitHub Actions

[Validate DQI analysis tools](https://github.com/corcondor/gvqcc/actions/workflows/validate.yml) は手動実行とPull Requestに対応します。リポジトリの **Actions → Validate DQI analysis tools → Run workflow** から実行できます。

CPUでテストと逆元回路の全入力検証を実行し、次の3ファイルを `dqi-arithmetic-verification` artifactとして14日間保存する設定です。

- `inverse_specialized_results.json`
- `pebble_results.json`
- `full_inverse_verify_results.json`

Kaggleの認証情報は不要です。ここに含むActions設定は実競技の大きい回路を自動取得・提出するものではありません。実行の成否はActionsの各runで確認してください。

## 計算記録とライセンス

`verification_summary.json` はGitHub反映前に実施したローカル検証のスナップショットです。その中のGitHub関連の `false` は、記録時点の状態を表します。現在のリポジトリやActionsの状態を示すものではありません。

`file_manifest.json` は初期登録時のファイル一覧とSHA-256です。検証コマンドによって結果JSONを更新した場合は、ハッシュが変わります。

公式仕様由来の小さなKMB例の出典とライセンスは [NOTICE.md](NOTICE.md) と [third_party/Qualtran_Apache_2.0.txt](third_party/Qualtran_Apache_2.0.txt) を参照してください。
