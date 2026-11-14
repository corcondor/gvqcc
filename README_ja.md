# DQI 計算・解析ツール

この文書は2026年11月14日のローカル計算・検証記録を基にした詳細説明です。リポジトリの入口と実行手順は [README.md](README.md)、GitHub上の実行状況は [Actions](https://github.com/corcondor/gvqcc/actions/workflows/validate.yml) を参照してください。

添付された `gvqcc_dqi_opt.py`（v4）の問題を修正する独立した低メモリ監査と、GF(2^12) の逆元回路を実際に生成・全入力検証した結果です。既存の別プロセスの v5/v6/v7 と区別するため、監査ツールは `gvqcc_dqi_audit.py` と命名しました。

**実際の `dqi.kmb`、現在の回路生成コード、最新の v6/v7 ゲートダンプは、この計算環境にはまだ届いていません。実 DQI の削減量や Kaggle スコア改善を確認した成果物ではありません。** 添付 v4 の SHA-256 は `ce18eda70b1d84e03b4555e44b74973759bbb03f52c6c3a33e9a28aab77ac460` です。

## 1. 今すぐ使う入口：巨大回路の監査

必要なのは Python 3 と C++17 コンパイラ（通常は `g++`）。`kickmix` の import は不要です。次の3ファイルを同じフォルダに置きます。

- `gvqcc_dqi_audit.py`
- `dqi_audit_scan.cpp`
- `kmb_profile.py`

Kaggle CPU または WSL で、実際の入力パスを指定します。

```bash
python3 gvqcc_dqi_audit.py \
  --circuit /path/to/dqi.kmb.xz \
  --index-mode legacy-v4 \
  --scratch-start 840 \
  --scratch-initial zero \
  --snapshots 10500000,10530000,10539000,24000000 \
  --window 10529430:10534531 \
  --window-limit 20000 \
  --region 22500000:27350000 \
  --out-dir dqi_audit_run1
```

`--circuit /path/to/submission.zip --member dqi.kmb` も使えます。`--circuit` を省略すると `/kaggle/input` を検索しますが、候補が複数ある場合は選択肢を表示して終了し、任意の一つを選びません。出力先は新しいディレクトリ名を指定してください。

`--scratch-initial zero` は、課題が q840 以降をゼロ初期化するという外部の前提を指定します。既定の `unknown` はゼロを仮定しません。ウィンドウと区間は **始点を含み、終点を含みません**。

### 出力

| ファイル | 内容 |
|---|---|
| `run_summary.json` | 入力パス、展開後KMBのSHA-256、解析設定、コードのハッシュ |
| `profile.json` | ヘッダー、命令ヒストグラム、明示的な条件付きゲート数、形式検査 |
| `scan.json` | 保守的な scratch 状態、区間最大値、条件スタック、命令数 |
| `events.jsonl` | 指定区間の全命令、スナップショット、PUSH由来の条件、KMBと旧v4の両インデックス |
| `compile.log` / `scan.log` | コンパイル・走査ログ |

`events.jsonl` では **CX、古典命令、PUSH/POP、INFO/DEBUG も保存**します。G1/G2 の依存解析で CX を落とすと、共有積のファンアウトを見失います。条件スタックには PUSH 時の命令位置と参照した古典ビットIDを記録します。ビットの値を実行時シミュレーションしているわけではありません。

### v4 からの修正

元コードは「最後の R/HMR 後に触れた量子ビット」を生存と呼んでいました。制御・位相だけでも生存扱いにし、条件付き R/HMR でも消去済みとしていたため、過大評価と過小評価が混在します。

新しい `possibly_nonzero` は、ゼロ／非ゼロかもしれない、の保守的解析です。条件付きリセットでは非ゼロの可能性を残し、制御の参照や位相ゲートだけではゼロを非ゼロ扱いにしません。SWAP によるゼロの移動も扱います。一方、XORの相殺や古典分岐の相関は追いません。**正確な生存期間、必要量子ビット数の下界、再利用の証明とは別です。**

全回路のオブジェクト化と KMX 全体への変換を廃止し、KMBの列を固定バッファで読みます。XZ/ZIP は一時KMBへストリーム展開するため、展開先のディスク容量は必要です。

## 2. EEA の G1/G2 を調べる際の判断

ユーザーの v6 報告では、G1へのCCX結果をCXでG2にも配る、共有された積の構造が見えています。この場合、G2が一時的にG1の6ビットを読むというだけでは、G2全体が「開始時の6ビットの関数」だとは言えません。G1はブロック内で外部入力により更新されます。

分析対象は **G1とG2を作る compute 部分全体**です。次に確かめるのは、入力量子ビット、ゼロ初期化された出力、共有積、24出力の係数の階数、およびSWAP/HMR後の旧値・位相補正への依存です。単純な直列化で共有積を再計算すると、Toffoliが増える可能性があります。

`symbolic_block_analyze.py` は、独立入力を変数とする疎な Boolean 多項式（ANF）を伝播し、全入力列挙をせずに出力の係数とGF(2)ランクを調べるためのツールです。未宣言の外部入力、測定、条件付き命令を黙って無視しません。入口の値と対象の切り出しは周辺回路から確認してください。まず `--help` を参照してください。

`boolean_block_analyze.py` は独立入力が12個以下の純粋な小ブロック向けで、全4096入力以下を直接検証し、真理値表・ANF・位相・出力のアフィン次元を出します。実際のG1/G2ブロックの検証結果はまだありません。

出力の線形変換によって一部の量子ビットをゼロにできても、それだけでは元の計算途中のピークは下がりません。圧縮した出力を直接計算する再合成と、後続の利用・消去を含む検証が必要です。

## 3. 実際に計算・検証した逆元カーネル

体は `x^12 + x^6 + x^4 + x + 1`（`0x1053`）。0の逆元は0へ拡張しています。

### 専用二次べき乗

入力を保存して出力へ `y^(2^a+1)` をXORする回路を生成しました。入力12量子ビット＋出力12量子ビットだけを使います。

| a | 値 | CCX | CX | 入出力以外の量子作業ビット |
|---:|---|---:|---:|---:|
| 1 | y^3 | 51 | 532 | 0 |
| 2 | y^5 | 36 | 577 | 0 |
| 3 | y^9 | 35 | 702 | 0 |
| 4 | y^17 | 27 | 559 | 0 |
| 5 | y^33 | 51 | 644 | 0 |

全4096入力・入力の復元・2種類の出力初期値・HMR位相補正を検証済みです。位相補正は測定マスクに線形なので、12個の独立マスク基底を確認することで全測定マスクをカバーします。

### 完全な逆元ゲート列

beta_k = x^(2^k-1) の保存・再計算・消去を有限状態探索で選び、一般の乗算も含めてすべて実際のCX/CCX/HMR/条件付きZ/CZへ展開しました。

| 使い方 | 入力以外の12-bitレジスタ数 | 入力を含む全Q | CCX | 命令数 |
|---|---:|---:|---:|---:|
| 逆元を出力に残し、中間値を消去 | 4 | 60 | 276 | 7,293 |
| 同上 | 5 | 72 | 240 | 6,237 |
| 逆元の最下位ビットを位相に使用し全消去 | 3 | 48 | 327 | 8,829 |
| 同上 | 4 | 60 | 267 | 7,850 |
| 同上 | 5 | 72 | 240 | 6,780 |

入力以外のレジスタ数には出力も含まれます。「48 scaffold」とは異なる数え方です。位相使用版は利用方法の一例で、DQIのForney計算全体ではありません。

全4096入力をビット並列シミュレーションし、各HMR結果を独立な記号変数として、その位相係数が全入力で相殺されることを確認しました。データ更新は測定結果に依存しないため全測定分岐をカバーします。入力保存、出力、空きレジスタのゼロも全段階で確認しました。

公式の一般乗算63 Toffoliを5回使う前進315 Toffoliのチェーンに対して、専用回路の組み合わせは240 Toffoliになります。ただし、現在の公開DQIが既に別の最適化を使っている可能性があります。これらは無条件の算術カーネルであり、量子制御付きの場合の費用は別途確認が必要です。

### 再実行

```bash
python3 inverse_specialized.py
python3 pebble_search.py
python3 full_inverse_verify.py --export-kmx
```

最終の完全回路の検証は、この環境で全5候補・参照値準備・KMX出力を含め約1.54秒、最大RSS約12.6MiBでした。GPUは使っていません。`*_results.json` に実際の計算結果、`inverse_*.kmx` にゲート列があります。

**公式Kickmixパーサー／検証器によるロード・採点と、実DQIへの組み込みは未実行**です。ここでのPASSは独自の全入力・全測定分岐ゲート検証です。

## 4. 量子ビットとToffoliの交換条件

ユーザー報告の基準値 Q=889、T=382600、総合スコア27.30683を使うと、他2課題と失敗率係数Rを固定した場合は、

`new_score = 27.30683 * ((889 / Q_new)^2 * (382600 / T_new))^(1/3)`

となります。Q=877、T据え置きなら総合スコアのモデル値は27.55535846。悪化しないTの上限は393141.87165で、追加予算は10541.87165 Toffoliです。これは公式採点結果ではありません。

```bash
python3 compare_dqi.py --new-q 877 --new-t 382600
```

基準と候補のTは同じ公式検証方法から取得してください。Rが変わった場合は `--r-ratio 新R/旧Rの数値` を指定します。

静的ヒストグラム `364174 + 7000 + 12240 = 383414` と、以前の報告382600は同一の指標・同じ回路か未確認です。条件付き実行の集計方法、入力ハッシュ、キットの版を合わせて比較します。

## 5. GitHub Actions

`.github/workflows/validate.yml` は、このフォルダをリポジトリのルートに置いた場合の実行設定です。手動実行とPull Requestで、形式・scratch状態・小ブロック解析のテストと逆元の全入力検証をCPUで実行し、3つの計算結果JSONをartifactとして残します。Kaggleの認証情報は使いません。

ローカルで同じテストを実行できます。

```bash
python3 -m unittest discover -p 'test_*.py' -v
python3 test_boolean_block_analyze.py
python3 test_symbolic_block_analyze.py
```

反映先は [corcondor/gvqcc](https://github.com/corcondor/gvqcc) です。Actions画面から手動実行できます。実行の成否は各runで確認してください。`verification_summary.json` はGitHub反映前のローカル検証記録であり、そのGitHub関連のフラグは記録時点の状態です。

## 6. 検証範囲と出典

- KMB profiler：公式4例と破損データなど23テスト。
- scratch監査：制御／位相だけの参照、条件付きHMR、PUSH内R、SWAP、CSWAP、旧／新インデックス、先頭リセット前の区間最大値を独立ケースで確認。
- PythonとC++のopcodeヒストグラムを照合。
- 基礎profilerの合成200万CCX・26MB KMBで約0.74秒／19.23MiB。これは実DQIや監査全体の計測ではありません。
- 逆元カーネル・スケジュール・完全ゲート列の検証範囲は各JSONに記録。

一次資料：

- [Kaggle competition](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/)
- [公式論文](https://arxiv.org/html/2610.23832v2)
- [KMB binary format](https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_binary_format.md)
- [Kickmix instructions](https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_instructions.md)
- [GF inverse generator](https://github.com/quantumlib/Qualtran/blob/main/kickmix/src/kickmix/gen/gf_arithmetic/gen_gf_inverse.cc)
- [GF multiplier generator](https://github.com/quantumlib/Qualtran/blob/main/kickmix/src/kickmix/gen/gf_arithmetic/gen_gf_mul.cc)

公式仕様由来の小さなhex fixtureの出典とライセンスは `NOTICE.md` と `third_party/Qualtran_Apache_2.0.txt` を参照してください。実際の競技入力データやユーザーの提出回路は同梱していません。
