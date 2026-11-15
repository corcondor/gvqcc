# invsqrt 追加改善探索 — score2

## 結果と採否

**今回も採用できる invsqrt のスコア改善回路は得られなかった。** e46 は変更していない。新しい KMB、公式全件検証、Kaggle 提出はない。既存スコア **78,719.52914734723、46 qubits** を維持する。

今回は、前回未完了だった q17 を加える 4-AND 合成を完了したうえで、**別の時点に位相回転を移して、そのためだけの 1〜2 AND を削除する方法**まで実装して検査した。固定した 6 入力だけの下界を、全回路の最適性と取り違えていない。

基準 KMB SHA-256:

`e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6`

基準 KMX SHA-256:

`69872bf5557a94e4a7425c9470b7a0451958e18276f2be178b5b0ee27dddb1b1`

前回の `score_invsqrt_manifest.json` にある **30 成果物のハッシュは全件一致**し、凍結した成果物を維持した。

## 1. 既計算値を使う出口再合成

対象は前回と同じ q19/q20 の復元で、現在 5 AND を使う。定数・XOR は無料として、4 AND にできれば公式コストの改善につながる。

| 検査 | 結果 |
|---|---|
| 高速列挙器の基準再現 | 6 入力の 651 first-AND、1,524,950 prefix が以前の完全結果と一致 |
| q17 を加えた 7 入力 | **2,667 first-AND、27,031,886 prefix を完了、4 AND なし** |
| 上記の未処理 rank ケース | 0 |
| q17 全列挙の実行時間 | 91.9089 秒 |
| 他の live wire を 1 本ずつ追加 | q17 を含めた **34 本すべてで 4 AND を排除** |
| 全 live 値の任意 XOR から得る無料中間関数 | 6 入力だけに依存する部分空間は定数＋6 入力の 7 次元のみ |
| 直後の v11 復元も含む 3 出力 | 6 入力・47 パターン上で 6→5 AND を完全列挙、解なし |

単独 wire の追加を効率的に調べるため、次の制限を使った。追加 bit を 0 または 1 に固定しても 6 入力の全 47 パターンが残るなら、その bit を使う 4-AND 回路も既存の下界に矛盾する。この方法で 25 本を直ちに除外できた。残る q28, q16, q15, q35, q14, q33, q13, q31 は、追加 bit を固定した 41〜46 パターンについて完全列挙を行い、4 AND を排除した。q17 は 63 パターンの 7 入力問題を直接完了した。

無料中間関数の検査は、全 3,133,452 入力上で「40 本の retained live 値の affine span」と「6 入力の同じパターンでは値が一定になる関数空間」の交差を計算したもの。6 入力以外の wire を非線形に利用する可能性までは否定しない。

**複数の追加 wire は別問題。** q17/q28 と q17/q16 の 2 組は、各 95 到達パターンで 4-AND SAT 合成を 60 秒ずつ試した。いずれも timeout で、判定は UNKNOWN。2 本以上を同時に使う解を排除したとは主張しない。

主な結果:

- `score2_invsqrt_extra17_complete.json`
- `score2_invsqrt_extra_restrictions.json`
- `score2_invsqrt_free_functions.json`
- `score2_invsqrt_joint_three_results.json`
- `score2_invsqrt_pair17_28_sat.json`, `score2_invsqrt_pair17_16_sat.json`

## 2. 2-AND の位相 feature を 1 AND に置換

位相 feature 4 個について、個々の CCX を消すのではなく、**compute → 回転 → 測定による消去**のまとまり全体の Boolean 述語を再合成した。これにより、既存の single-CCX affine 検査が扱っていない縮約を対象にした。

- 任意の 1〜2 本を左因子にし、右因子と affine 加算項に全 live 値を使う検索: 4 件とも式なし。
- 関連する制御・保持中の swap 差分 10 本の全 parity を左因子にする検索: 4 件とも式なし。
- 左右の因子を全 44〜45 本の live 値から自由に選ぶ SAT: 4 件とも 30 秒で timeout。**こちらは UNKNOWN**。

この結果は、任意の 1-AND 置換が不可能だという証明ではない。

結果: `score2_invsqrt_feature_oneand.json`, `score2_invsqrt_feature_dense.json`, `score2_invsqrt_feature_sat.json`。

## 3. 同じ位相述語を別の時点で使う

基底状態のデータ値が測定結果に依存しない切断点で、回転の Boolean 述語 f(x) を既存 wire の parity として作れれば、回転をそこへ移し、末尾の専用 compute/erase を削除できる。同じ f(x) であることが必要で、測定の符号を無視したり結果を 0 に固定したりする方法ではない。

### Affine な位相移動

1〜2 AND を使う feature 8 個を対象にした。条件付きブロック内と、各 feature 自身の compute/erase 区間内を除外して、全回路の **2,554 切断点、20,410 affine クエリ**を検査した。該当なし。

結果: `score2_invsqrt_phase_relocation.json`。

### 1 AND を使う位相移動

2-AND feature 4 個を、別の切断点で 1 AND と affine 項から作る専用検索器を作った。追加 qubit は使わず、その時点で全入力に対して 0 である scratch を一時的に借りる候補だけを調べた。

検索した左因子は 2,163 種類で、任意の 1〜2 本の parity、または指定した q22,q23,q24,q25,q7 の任意 parity に任意の 1 本を加えたもの。右因子と affine 加算項は、その時点の全 wire から自由に選ぶ。

| 範囲 | 切断点 | クエリ | 結果 |
|---|---:|---:|---|
| 位相処理内 | 133 | 1,129,224 | 該当なし |
| 全回路 | **2,048** | **17,369,732** | 該当なし |

全回路の検索は約 38 秒で完了した。512 個の合法入力上ですでに式が存在しなかったため、列挙した左因子の族については全ドメインの解もない。正のモデルが出た場合には、元の切断点を全 3,133,452 入力で再計算し、述語一致を検証する bridge を実装したが、実際の feature では正の候補は出なかった。

**範囲:** 任意の左因子すべてを調べたわけではない。全回路について任意の 1-AND 位相移動を排除した結果ではない。

結果: `score2_invsqrt_relocate_oneand_results.json`, `score2_invsqrt_global_oneand_results.json`。

## 4. 検証と終了状態

`score2_invsqrt_audit.json` は以下の PASS を記録する。

- 高速化後の 6 入力列挙が、独立レビュー済みの以前の完全結果と一致。
- 既知の 4-AND 陽性対照を高速列挙器が発見し、独立 Python evaluator で一致。
- 既知の 5-AND・3 出力陽性対照を新しい列挙器が発見し、同様に一致。
- 位相移動用 1-AND 検索器の非 affine な陽性対照を、**全 3,133,452 入力**で確認。

陽性対照は実装を試すための合成問題であり、ベンチマーク改善候補ではない。実候補がないため、公式検証へ渡す KMB はない。45Q 化は複数の幅ピークで同時に成立させる変更が必要で、短く完結する候補がなかったため、ここから新たな広い再探索には進まなかった。稼働中の探索プロセスはない。

## 5. 再現と保存

Python＋NumPy、g++ の C++17 を使う。SAT の再現にだけ `z3-solver==4.15.4.0` が必要。実際の陰性結果の時間制限は再現環境の性能に依存する。

```bash
g++ -O3 -std=c++17 score2_invsqrt_joint_fast.cpp -o /tmp/score2_invsqrt_joint_fast
g++ -O3 -std=c++17 score2_invsqrt_joint_three.cpp -o /tmp/score2_invsqrt_joint_three
g++ -O3 -std=c++17 score2_invsqrt_relocate_oneand.cpp -o /tmp/score2_invsqrt_relocate_oneand
export SCORE2_ENUM_BINARY=/tmp/score2_invsqrt_joint_fast
export SCORE2_ONEAND_BINARY=/tmp/score2_invsqrt_relocate_oneand
/tmp/score2_invsqrt_joint_fast score_invsqrt_joint_extra17_table.txt all 600
python3 score2_invsqrt_restrict_extras.py
python3 score2_invsqrt_free_functions.py
python3 score2_invsqrt_prepare.py
/tmp/score2_invsqrt_joint_three score2_invsqrt_joint_three_table.txt all 180
python3 score2_invsqrt_phase_relocation.py
python3 score2_invsqrt_relocate_oneand.py --global-cuts
python3 score2_invsqrt_audit.py
```

陽性対照の JSON を再生成する場合は、各列挙器に `score_invsqrt_joint_positive_control.txt` または `score2_invsqrt_three_positive.txt` を渡し、既存の対応 JSON と同じ名前に stdout を保存する。

2 本追加と feature SAT の再現はそれぞれ `score2_invsqrt_pair_tables.py` → `score2_invsqrt_pair_search.py`、`score2_invsqrt_feature_sat.py`。限定した因子族は `score2_invsqrt_feature_oneand.py` と `score2_invsqrt_feature_dense.py`。

ハッシュと公開するファイルは `score2_invsqrt_manifest.json`。約 12.9 MB の全回路 sample 入力と約 0.9 MB の位相領域 sample 入力は、bridge が生成する中間ファイルで、公開必須ファイルから除外した。manifest にはそのハッシュと生成方法を残した。
