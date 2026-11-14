# invsqrt スコア改善の追加探索 — e46 維持

## 結果

**今回採用できるスコア改善回路は得られなかった。** 既存の e46 回路は変更していない。新しい KMB の生成、公式全件検証、Kaggle 提出は行っていない。

一方、位相処理の出口で 2 本の値を復元する小回路について、従来の「4 AND が見つからない」という状態から、**現在使う 6 入力に限定すれば 5 AND が最小**という完全列挙の結果まで進んだ。これは全回路の最適性でも、他の live 値を入力に加えた場合の下界でもない。

| 項目 | 今回の結果 |
|---|---|
| 採用回路 | e46 のまま |
| qubits | 46 のまま |
| スコア | 78,719.52914734723 のまま。上流の既存検証値 |
| 新たな公式検証 | なし。合格候補が得られなかったため |
| 45Q の affine 圧縮 | 最初のピークに rank 47 の反証を保存 |
| 非線形 retirement | 長い区間 24 件＋短くした区間 30 件で採用可能な式なし |
| 出口の 6 入力・2 出力を 4 AND で合成 | 完全列挙で該当なし。現行の 5 AND は同じ表で一致 |
| 7 本目の入力 q17 を追加 | 限定族は完了。広い探索は 60 秒で打ち切り、全体は未解決 |

既存スコアの出典は `results/2026-11-14/invsqrt_upstream_verification.json`。これは既存 e46 に対する上流の 200,540,928-shot 検証であり、今回の新規実行ではない。

## 1. 対象と採否基準

対象 KMB の SHA-256:

`e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6`

対象 KMX の SHA-256:

`69872bf5557a94e4a7425c9470b7a0451958e18276f2be178b5b0ee27dddb1b1`

公式ドメインは整数 x = 1,…,3,133,452。今回の Boolean 到達可能値の抽出は、この全入力を bitset で扱った。条件付きブロックは各 POP で入口と出口の全値が一致することを検査した。したがって、ここで抽出するデータ値は HMR のランダムな結果に依存しない。

目標は、CNOT 数だけでなく公式コストを下げることだった。Q を 46 から 45 にでき、位相の余裕を維持する場合は、約 38.03 Toffoli-equivalent 未満の追加コストなら改善し得る。しかし、1 箇所だけ幅を下げても最大幅 Q は下がらないため、全ピークを覆う実装が必要になる。

## 2. 45Q を妨げる最初のピーク

KMX の **2388 行目 `CCX q26 q27 q45` の直後**で、定数関数 1 と全 46 本の wire 値からなる 47 関数の GF(2) rank は 47 になる。

全ドメインの列消去から 47 個の合法入力を選び、その入力上でも rank が 47 である小さな witness を保存した。このため、この切断点にある全 wire 値を **45 本の Boolean 座標の affine 結合だけで表すことはできない**。少数のランダム入力だけの rank 推定はこの障害を見落とすため、採否に用いなかった。

この最初のピークは係数テーブルの loader 内にある。その後にも係数処理、積、除算、位相処理、逆算術に独立の幅ピークがある。単一 wire の単純な番号再割当てだけでは Q45 にならない。

証明ファイル:

- `score_invsqrt_peak_certificate.py`
- `score_invsqrt_peak_certificate.json`

この反証は affine な表現変更だけを否定する。非線形な符号化、位相誤差を許容範囲内で変更する算術設計、別の計算順序は対象外である。

## 3. 非線形 retirement の bounded search

検討した正しい測定プロトコルは、使わない値 q を HMR で測定して空け、その結果 m を保持し、再び必要になる前に q を正確に再生成して条件付き Z(q) を適用するものだった。この Z が測定の符号 (−1)^(m q) を返済する。測定結果を勝手に 0 と置く処理は使っていない。

検索した復元式は

`q = affine(other_live_values) XOR A(other_live_values) * B(other_live_values)`

である。A は現時点の wire 1 本または 2 本の XOR、B と加算する affine 項は任意の線形結合。候補が見つかった場合は全 3,133,452 入力で等式を検査する構成にした。

| パネル | ケース | 結果 |
|---|---:|---|
| 長い idle 区間を優先 | 24 | 復元式なし |
| 算術領域の境界で早めに復元する短縮区間 | 30 | 復元式なし |

短縮区間の終端は、KMX の配列インデックスで 2889, 3319, 4409, 7573, 8566, 14884, 16795, 17198, 19763, 20557 に固定した。自由な全区間の再探索ではない。

**否定の範囲:** A を 3 本以上の parity にした式、2 AND 以上での復元、値を他の wire に非線形に詰めてから測定する方法は含まない。全体の Q45 不可能性を意味しない。公開祖先にある h0 の flag への packing は、単純な再生成式とは別の操作なので、この検索から否定できない。

結果は `score_invsqrt_retire.json` と `score_invsqrt_short_retire.json` に記録した。公開時に gzip 化する場合も、実行時の生 JSON のハッシュを manifest に保持する。

先に行った 9 個の CCZ 位相関数の全 2 次 span 検査も `score_invsqrt_quadratic.json` に残してある。これは wire retirement と異なる問題であり、今回の 54 区間と同一視していない。

## 4. 出口の 2 出力を共同合成する問題

実 e46 の **8433〜8544 行目**は、位相処理の間に測定して空けた q19, q20 を再生成する。公開祖先の source では root の v9, v10 に相当する。現在は 5 CCX を使う。

全入力で次を取得した。

- 復元すべき値: 7599 行目の直前の q19, q20。
- 復元時の 6 入力: q18, q9, q34, q36, q30, q32。
- 到達する入力パターン: 64 通り中 **47 通り**。
- 同じ 6 入力パターンに対する出力は一意。

現行の 5 AND 式を代数的に書き下し、この 47 パターンすべてで一致することも別の Python evaluator で確認した。元の公開ソースは [Syed v12](https://www.kaggle.com/datasets/syed3000/vqcc-own-circuit-portfolio) の Apache-2.0 コードだが、今回の抽出器と列挙器は新規に作成したもので、元の生成器を実行する依存はない。

### 4.1 SAT の終了状態

まず Z3 4.15.4.0 で 4 AND、自由な XOR 因子、2 つの affine 出力を直接符号化した。120 秒で timeout、peak memory 約 45 MB だった。結果は **UNKNOWN** であり、この SAT 実行単独から下界は主張していない。

記録: `score_invsqrt_joint_k4_seed19.json`。

### 4.2 XOR span を使った完全列挙

次に、この小さな問題に専用の有限列挙を用いた。

1. 利用可能な関数の affine span を L とする。新しい AND 値は L を加えた違いまで同じものとして扱える。その差は後続の XOR と出力の式へ吸収できる。
2. 因子 A, B, A XOR B の 3 通りの非零線形形式を使う同じ 2 次元部分空間は、AND 値が L の項だけ異なる。最初の AND について、この正規化で **651 クラス**を漏れなく列挙する。
3. 2 個目の AND も同様に列挙し、同じ到達可能表で同じ coset になるものを統合する。全 first-two prefix は **1,524,950 クラス**だった。
4. 全 prefix で、2 出力の L に対する coset は線形独立だった。残りが 2 AND なら、その 2 個の coset はこの 2 次元出力空間を張らなければならない。
5. 従って 3 個目の AND は、出力 1、出力 2、その XOR の 3 方向のどれかになる。それぞれについて左因子の全 parity を列挙し、右因子を GF(2) 線形方程式として解く。最後の AND も同じ方法で判定する。

この最後の手順では、左因子を 1〜2 本に制限していない。利用可能な全関数の parity が対象である。

完全実行の結果:

| 指標 | 値 |
|---|---:|
| 最初の AND クラス | 651 / 651 完了 |
| 最初の 2 AND クラス | 1,524,950 |
| 出力 rank が 1 以下で未処理となるケース | 0 |
| 4 AND 解 | 0 |
| 実行時間 | 17.136 秒 |

この結果と、実在する現行の 5 AND 式を合わせると、**指定した 6 入力から指定した 2 出力を、この 47 パターン上で計算する Boolean XOR/AND 回路の最小 AND 数は 5**となる。17 個の未到達パターンを任意に使ってよい条件でも、4 AND にはならなかった。

これは他の live 値を無料の説明変数として追加する場合や、別の切断点、算術全体を変更する場合の下界ではない。量子回路全般の T-count 最適性を主張するものでもない。

### 4.3 陽性対照

列挙器に、同じ 47 入力パターン上で既知の 4 AND 回路が存在する別の 2 出力を与えた。列挙器は 4 AND 回路を返し、独立した Python の bit-vector evaluator が全パターン一致を確認した。比較対象を意図的に 1 bit 変えた場合は不一致を検出することも確認した。

ファイル:

- `score_invsqrt_joint_enum.cpp`: 専用列挙器。
- `score_invsqrt_joint_table.json`, `.txt`: 全ドメインから抽出した有限表。
- `score_invsqrt_joint_enum_all.json`: 完全列挙の終了状態。
- `score_invsqrt_joint_known_five.json`: 現行 5 AND の witness。
- `score_invsqrt_joint_positive_control.txt`, `.json`: 4 AND の陽性対照。
- `score_invsqrt_joint_audit.py`, `.json`: 独立評価。

## 5. 他の live 値を使う範囲

同じ復元切断点にある **40 本の非零 live 値**に対しても、2 出力が単純な affine 関数または上記の限定した 1 AND 式で表せるか検査したが、式は得られなかった。

さらに、6 入力へ 1 本ずつ追加した場合の到達パターン数を全ドメインで調べた。q17 を追加すると 63 パターンで、次に少ない q28 は 79、その他は最大 94 だった。このため q17 に絞って追加探索した。

| q17 を加えた 7 入力の探索 | 結果 |
|---|---|
| 最初の AND を現行と同じに固定 | 10,137 個の 2 段 prefix を完了、解なし |
| 最初の AND も変更 | 2,667 中 385 クラス、3,907,584 prefix を確認 |
| 終了条件 | 60.0104 秒で打ち切り |
| 全 7 入力問題の判定 | **未解決。UNSAT ではない** |

この結果を受け、追加探索を終了した。候補の KMB は存在しない。

## 6. 再現

作業ディレクトリはこの repository とする。Python 3.12 と NumPy、C++17 対応 g++ を使った。完全列挙と witness 評価には Z3 は不要。

```bash
python3 score_invsqrt_joint_synthesis.py --extract-only
python3 score_invsqrt_joint_live_probe.py
python3 score_invsqrt_joint_prepare.py
g++ -O3 -std=c++17 score_invsqrt_joint_enum.cpp -o /tmp/score_invsqrt_joint_enum
/tmp/score_invsqrt_joint_enum score_invsqrt_joint_table.txt all 60
/tmp/score_invsqrt_joint_enum score_invsqrt_joint_positive_control.txt all 15
python3 score_invsqrt_joint_audit.py
python3 score_invsqrt_peak_certificate.py
```

陽性対照を再生成して evaluator に読ませる場合は、列挙器の JSON 出力を `score_invsqrt_joint_positive_control.json` に保存する。q17 への bounded search は次の通りで、時間制限内に確認できる prefix 数は CPU によって変わる。

```bash
/tmp/score_invsqrt_joint_enum score_invsqrt_joint_extra17_table.txt
/tmp/score_invsqrt_joint_enum score_invsqrt_joint_extra17_table.txt all 60
```

区間検索の再現:

```bash
python3 score_invsqrt_retire.py --out score_invsqrt_retire.json
python3 score_invsqrt_short_retire.py
```

SAT timeout を再現する場合のみ `z3-solver==4.15.4.0` を Python 環境にインストールし、次を実行する。

```bash
python3 score_invsqrt_joint_synthesis.py --reuse-table --k 4 --seed 19 --timeout 120
```

入力・出力・source の SHA-256 と実行結果の対応は `score_invsqrt_manifest.json` にまとめた。生 JSON の実行ハッシュを正本とし、公開用 gzip の対応は総合 manifest で扱う。
