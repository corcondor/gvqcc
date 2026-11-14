# invsqrt: Boolean 位相基底の構造探索（2026-11-14）

## 結果と採用判断

**実スコアを改善する候補は得られず、e46 を維持する。** ただし、実際に generic rotation を 33 個から **32 個へ減らした回路**を構築し、全 3,133,452 入力について公式と同じ整数 oracle で誤差許容を確認した。「この回路では回転を一個も削れない」という広い主張は成立しない。32 個に減らせても、残る誤差余裕が小さくなり、合成費用を含む目的関数では元回路より悪い。

追加の新 Boolean 基底では近似誤差余裕を約 44% 改善できたが、回転が 1 個増える費用を回収できなかった。

| 回路 | generic rotations | Q | 最小余裕（turns） | rotation 合成の Toffoli-eq | 推定総コスト Q C |
|---|---:|---:|---:|---:|---:|
| 元 e46 | 33 | 46 | 6.305754638065431e-12 | 231.2940713535 | 78,719.52914735 |
| 新基底 q42 を追加 | 34 | 46 | 9.055015418035772e-12 | 236.0230409431 | 78,937.06174847 |
| 既存 q30 回転を削除して再 fit | 32 | 46 | 2.708354916204636e-13 | 244.4307622811 | 79,323.81693001 |

コストは小さい方がよい。表の総コストは、変更していない算術部分の upstream 全検証平均 1479.7500405453395 Toffoli と、既存の T gate 1 個（0.25 Toffoli-eq）を利用した予測値。新しい回路の公式 64 shots/x、合計 200,540,928 shots は実行していない。Kaggle への提出、既存 baseline / worker / README の変更もしていない。

## 公式契約と旧 LP 主張の射程

参照した一次ソースは固定された公式 verifier:

- `official_sources/Inzainos/verifiers/invsqrt/verify_submission_invsqrt.py`
- [GitHub の固定 revision](https://github.com/Inzainos/quantum-circuit-compilation/blob/4277c767440df9efb8a90860ae2ce47028e46ba9/verifiers/invsqrt/verify_submission_invsqrt.py)

契約はすべての整数 `x = 1..3,133,452` に対し、入力 x と scratch=0 を復元し、位相を `1/sqrt(x)` turns へ相対精度 `2^-24` で近似すること。元回路は 46 qubits、23,877 命令、generic Z_POW が 33 個、T-class が 1 個、Clifford Z_POW が 4 個だった。したがって「33/34 基底」の数え方では、generic と T を分ける必要がある。

旧 `solve_full_zpow_lp.py` 本体や LP dual certificate は、この共有環境には存在しない。過去ログの「global optimal」は検証済みの定理として扱っていない。仮に固定 Boolean 基底に対する minimax LP が最適でも、次は別問題である。

1. 回転を削除した後も誤差許容内に入るか。
2. 異なる Boolean / Walsh 基底を使えば近似できるか。
3. 回転数と合成精度の合計コストが最小か。
4. 算術の次数・区間・ビット幅や qubit 数を変えて、より安く計算できるか。

今回、1 は実際に可能だと確認した。2 は真の追加基底 q42 で誤差余裕を改善できた。3 の改善はなかった。4 の算術アーキテクチャ再設計は今回の探索範囲外。

また、公式 verifier は回転合成誤差を等分し、`eps = pi * margin / n_rot` として採点する。個別回転に非一様 eps を指定する仕組みは提出形式にない。内部合成アルゴリズムの誤差配分だけを変更しても、この採点式には反映されない。

## フーリエ / Walsh 観点で実際に行った変換

既存位相関数を `sum_j theta_j f_j(x)` として抽出した。`f_j(x)` は、その Z_POW 命令の時点で対象 qubit が持つ Boolean 値である。異なる回転時点の値は、同じ qubit 番号でも別の関数になり得る。

3 箇所の挿入時点（元 KMX の 7705、8075、8189 行）で同時に存在する qubit の値を抽出し、`f_a XOR f_b` を候補にした。この Boolean parity は Walsh 符号 `(-1)^(f_a XOR f_b)` と定数の一次結合に対応する。回路には次の形で実装できる。

```
CX qa qb
Z_POW qb theta
CX qa qb
```

これは追加 qubit なし、追加 Toffoli なし、CX 2 個と回転 1 個の変更。汎用 QFT や H gate は追加していない。q21 が挿入点で恒等的に 0 である候補では、上の CX 2 個は省略でき、実質は片方の qubit の回転になる。

### 最終監査で判明した重複

保存ファイル名 `invsqrt_structural_walsh32` は探索中の識別名を残しているが、**新しい独立 Walsh 基底を使った 32 回転解ではない**。全 domain で 8189 行直前の q21=0 なので、追加候補 `q21 XOR q34` は既存の q34 回転基底そのものだった。

- 元 8075 行の q30 generic 回転（half-turns 約 2.9630e-11）を削除。
- 元 8189 行の q34 回転を一旦削除し、同じ Boolean 関数上の再 fit 角で置き換える。
- 残りの角度を再 fit。

実質的には「既存 q30 回転を削除し、残り 32 角を最適化した」回路である。一方、34 回転候補の q42 は既存の各回転基底と全 domain で一致せず、新しい位相情報を与える。

この区別を報告前に訂正した。回転削除可能性と、新基底が必要だったかを混同しない。

## 探索方法

1. KMB e46 を KMX へ書き出す。
2. C++ の 64 入力 bit packing で全 domain を走査。38 個の Z_POW 基底、3 箇所×46 qubit の状態、その他の Clifford 位相 parity を抽出。
3. HMR outcome がすべて 0 の枝で、全入力の x / scratch 復元を確認。
4. 既存位相誤差を基準に、`1e-11` turns 単位で LP をスケーリングする。
5. 決定的な小入力・等間隔入力・厳しい制約の active set で粗選別する。
6. 小さい LP と全 domain の分離 oracle を反復し、最悪入力制約を追加する。固定基底の同じ LP を無目的に再実行せず、候補基底または回転削除を変更する。
7. 選定角は dyadic な half-turns の `2^-80` 単位へ丸めて実 KMB を生成する。
8. 最終誤差は LP の浮動小数結果を信用せず、128-bit 整数の位相加算と公式の `isqrt(floor(2^130/x))` oracle に戻して全 domain を検証する。

最初の探索では 1,848 種類の新基底候補を粗評価し、18 本の追加・置換 LP を全 domain まで確認。削除後の残差へ目的を合わせ直した探索では、35 本の LP を確認した。追加の短い探索では、q30 削除 + 真の新基底 1 個、および既存 3 個削除 + 新基底 2 個を検討した。追加探索 20 件は 81.45 秒で完了し、採点改善はなかった。結果は `invsqrt_structural_pair_results.json` に保存した。さらに constant1 基底を `X q21; Z_POW q21; X q21` で作る 4 件も評価した（7.49 秒）。q21=0 は全 domain で確認済み。constant1 追加だけでは最大 margin は元回路とほぼ同じで、q30 削除 + constant1 でも margin は約 2.70836e-13 のままであり、費用を改善しなかった。公式目標の global phase はそのまま維持し、定数位相を無償として除外していない。

これらは有限候補の探索であり、すべての Boolean 関数・すべての算術回路についての最適性証明ではない。探索用 active set や LP に採点 seed / 回路 hash を利用していない。検証 seed の変更によるスコア探索もしていない。

## 位相の正しさと native 検算

挿入点までの条件付き命令を調べると、条件付き量子操作は Z / CZ / NEG のみで、X / CX / CCX / HMR はない。したがって、挿入する新位相の Boolean 値は、それ以前の HMR の測定結果によらない。CX→Z_POW→CX は量子ビット値を復元して入力 x だけに依存する位相を掛けるため、その後の既存 uncompute に新しい値依存を持ち込まない。

この構造上の理由に加え、元回路と 2 候補を、それぞれ **12,288 native shots**（4,096 入力相当 × 3 固定 seed）で確認した。

- x 復元違反: 0
- scratch 復元違反: 0
- 正確な整数モデルとの位相不一致: 0
- 同じ入力・測定 seed での Toffoli 総数: 3 回路とも **18,184,105**

これは公式 200M-shot 全検証を実行したという意味ではない。全 domain の整数位相検証と、測定枝を変えた native 検算を組み合わせた検証である。元 e46 については、upstream の 200,540,928-shot PASS が circuit hash に対応している記録を利用した。

## 合成費用の境界が示す次の目標

算術と Q を変えない場合、元回路より安くするために必要な最小位相余裕は次の通り。

| generic rotations | 元回路を下回るために必要な margin（turns） |
|---:|---:|
| 31 | > 6.3137025783e-13 |
| 32 | > 2.0673544999e-12 |
| 33 | > 6.3057546381e-12 |
| 34 | > 1.8028383056e-11 |
| 35 | > 4.8581597840e-11 |

一方、許容誤差が最小の入力での tolerance は約 3.3671974272e-11 turns。min margin はこの値を超えられない。したがって、**同じ Q と算術コストで 35 個以上の generic 回転を使う候補は、近似が完全でも元回路を下回れない**。これは当該採点式からの上界であり、探索打切りの根拠になる。

33 回転から 32 回転へ減らすだけでは足りず、margin を約 2.07e-12 以上確保する必要がある。今回の 32 回転解は 2.71e-13 で約 7.6 倍不足した。

算術コストは 1479.75 Toffoli、回転合成は 231.29 Toffoli-eq で、費用の大半は算術にある。今後大きく伸ばすには、位相基底の微調整だけでなく、正規化・近似関数のビット幅・算術回路・ancilla スケジュールを変更して Q または算術 Toffoli を減らす必要がある。この必要性は探索を尽くしたという意味ではなく、費用内訳と今回の有限候補結果からの優先順位判断である。

## 再実行

プロジェクト親ディレクトリを cwd とする。

```bash
python gvqcc_repo/invsqrt_structural_extract.py
OPENBLAS_NUM_THREADS=1 python gvqcc_repo/invsqrt_structural_search.py
OPENBLAS_NUM_THREADS=1 python gvqcc_repo/invsqrt_structural_replace.py
OPENBLAS_NUM_THREADS=1 python gvqcc_repo/invsqrt_structural_pair_search.py
OPENBLAS_NUM_THREADS=1 python gvqcc_repo/invsqrt_structural_constant_search.py
OPENBLAS_NUM_THREADS=1 python gvqcc_repo/invsqrt_structural_validate.py
```

`scipy` のある Python と `kickmix_venv/bin/python` を利用する。抽出の bit-packed バイナリや巨大行列は再生成可能な `invsqrt_structural_work` の中間生成物であり、証拠 JSON と小さいソース / KMB をリポジトリ側へ保存した。
