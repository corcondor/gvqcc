# GVQCC — DQI 回路の解析・計算

[Google Quantum AI — Verifiable Quantum Circuit Compilation](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/) の DQI 課題に向けた、回路解析と有限体演算の検証コードです。

大きい KMB 回路を全展開せずに調べる監査ツール、EEA の共有積を式に起こす解析器、GF(2¹²) 逆元回路の生成・全入力検証をまとめています。**実際の競技用 `dqi.kmb` は同梱していません。現在の提出回路への組み込みや、公式検証器でのスコア改善は未確認です。**

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

Python 3.12で動作確認しています。Pythonコードは標準ライブラリだけで動きます。KMB監査とそのテストには C++17 コンパイラ（`g++`）も必要です。Linux、WSL、Kaggle CPUでの利用を想定しています。

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

全4096入力について、入力保存・出力・空き領域のゼロ・各HMR測定結果の位相補正を検証しました。測定結果を独立した記号変数として扱い、全測定分岐を確認しています。これらは無条件の算術部品であり、公式KickmixパーサーやDQI全体の検証結果とは区別しています。

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
