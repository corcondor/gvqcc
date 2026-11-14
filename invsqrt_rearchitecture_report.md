# invsqrt の構造変更実験 — e46 を維持

## 結論

今回の追加実験から採用できるスコア改善は得られなかった。現行の `e46d90c36d1b…` は変更していない。新しい回路の Kaggle 提出、公式 200,540,928-shot 検証は実行していない。

既存の 77 件の位相 LP、1,551 ゲートに対する到達可能値の affine 検索は再実行していない。今回は **算術結果の精度を変える 7 件の数値プローブ**と、**位相処理から外れている 2 本の値を測定・再生成して作業領域を空ける解析**を行った。

## 1. 現回路と原生成器の関係

対象バイナリの SHA-256:

`e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6`

対象 KMX の SHA-256:

`69872bf5557a94e4a7425c9470b7a0451958e18276f2be178b5b0ee27dddb1b1`

公開の [Syed v12 原生成器](https://www.kaggle.com/datasets/syed3000/vqcc-own-circuit-portfolio)の `invsqrt_source_zip` を取得した。2,563,106 bytes、561 ファイルで、付属 SHA256SUMS の 560 項目すべてが一致した。アーカイブの SHA-256 は `7d9801ae20e942dba2211a656bba6014a0a16d57da534c0b60328d1c5d9d8254`。

ただし、この生成器が再現するのは公開祖先 **321aff836362…** であり、現行 e46 そのものではない。[ahoirg の提出ノート](https://www.kaggle.com/code/ahoirg/qcc-submit-verify-and-package)は、次の 64 行テーブル版を非公開カーネル `ahoirg/qcc-invk6-k6c` で作ったと明記している。その非公開生成器は取得していない。

系譜は以下のとおり。

1. Syed の凍結生成器＋13 patch: 48 → 46 qubits、値の測定・再生成、回路全域の機械的縮約。
2. ahoirg の 64 行版: 6 アドレスビット、13-bit 切片＋7-bit 傾き、2 つの loader を 27＋29 AND に変更。
3. Atakan の角度 refit。
4. Asterios の dirty-target CCX/HMR → 早い HMR と条件付き CZ。これを含むものが現行 e46。

今回の数値実験は、祖先生成器から作った別回路ではなく、**実 e46 の KMX**を直接用いた。

### 判明した算術構造

公開祖先の emitter と実 e46 の対応箇所から、主系は次の形である。

- 指数を取り出す正規化。
- 入力を消費して 12 本の root 値と 10 本の残差に変える整数平方根。
- テーブル係数と残差の算術。
- 非復元型の除算と、途中の商符号の保持。
- 26-bit の環状 permutation と Z 回転による位相付与。
- 測定による片付けと、残りの算術の逆計算。

**これは QFT 回路ではない。** 位相処理には Z 回転があるが、その前段は Boolean 算術と controlled swaps である。公開祖先の成分別コストを現 e46 の削減可能量として転用していない。

## 2. 最後の除算結果・carry 精度を変える数値プローブ

全 3,133,452 入力について、次の変更が作る Boolean 位相基底を抽出し、既存 33 個の一般角度を局所的に refit した。変更は算術構造の候補を早く棄却するための **分析用 intervention** である。変更に合わせた逆計算や測定の位相補正を実装した回路ではない。

| 変更 | refit 後の最小余裕 (turns) | 最大誤差 / 許容誤差 | 判定 |
|---|---:|---:|---|
| 位相入口で q41 を 0 に固定 | −3.99766e−12 | 1.11729 | 不合格 |
| 同 q41, q40 を 0 に固定 | −2.55316e−9 | 74.5338 | 不合格 |
| 同 q41, q40, q43 を 0 に固定 | −1.95693e−8 | 578.878 | 不合格 |
| 最後の carry 鎖の最初の CCX を省略 | −1.68564e−11 | 1.49441 | 不合格 |
| 同 2 番目の CCX を省略 | −2.38079e−11 | 1.69761 | 不合格 |
| 同最初の 2 個を省略 | −2.62339e−11 | 1.76869 | 不合格 |
| 同最後の CCX を省略 | −4.79781e−11 | 2.34749 | 不合格 |

元の KMX の対象 CCX は 1 始まりの 7548, 7554, 7559 行。位相入口の intervention は 7601 行直前に置いた。

**この結果の範囲:** 既存の位相処理と、各角度の変化を ±1e−5 turns に制限した局所 LP に対する結果である。全体の大域最適性、別の丸め方式、係数表も変更する設計まで否定する結果ではない。位相計算には long double、LP にはスケール補正した float64 を用いた。公式整数 oracle による採用判定ではない。いずれも余裕が負なので、測定補正や native emitter を実装する前に棄却した。

これらの分析用 KMX は scratch 復元を満たさない。`analysis_only_` と明記し、提出用のメンバーとして扱っていない。

結果: `invsqrt_rearchitecture_phase_results.json`

## 3. 位相で読まれない q42 / q45 の測定・再生成

実 e46 で **q42 と q45 は 7573〜8567 行の位相処理中に一度も参照されない**。この 2 本をその間だけ測定して空けられれば、位相処理の保持用アンシラに回す、または幅を下げる候補になる。

ただし、参照されないからといって任意にリセットしてよいわけではない。測定の位相を払い、出口で元の値を再生成する必要がある。そこで入口の全到達可能値を求め、保持される他の live 値からの **任意の 2 次 Boolean 式**を検索した。

検索した関数クラスは

`constant XOR Σ a_i q_i XOR Σ b_ij (q_i AND q_j)`

で、特定の 1〜2 個のゲート形に限定していない。q21 はこの区間の入口で消費されるキャッシュなので、復元の説明変数から除外した。

| 復元対象 | 追加除外 | 使用できる live 値 | GF(2) 特徴行列の rank | 結果 |
|---|---|---:|---:|---|
| q42 | q21 | 42 本 | 896 | 2 次式なし |
| q45 | q21 | 42 本 | 895 | 2 次式なし |
| q42 | q21, q45 | 41 本 | 854 | 2 次式なし |
| q45 | q21, q42 | 41 本 | 854 | 2 次式なし |

各ケースで 1,024 個の合法入力に制限した段階ですでに矛盾した。その中から **396〜400 個の入力行**を選び、次の反証を保存した。

- 選んだ行を XOR すると、定数・全一次項・全二次項の値はすべて 0。
- 復元対象の値だけは 1。

従って、どの 2 次式もこの合法入力集合に一致できない。これは、その入力集合を含む全ドメインでも一致する 2 次式がないという厳密な反証である。別実装の NumPy uint8 ゲートシミュレータで、合計 715 個のユニークな witness 入力を再計算し、4 件とも反証を確認した。

**否定しているのは、この切断点・この保持値を用いた 2 次復元だけ。** 3 次以上の関数、別の切断点、関数の共有を伴う再生成まで否定していない。また、これは以前の「各 CCX の積が affine か」という検索とは違う。

証明: `invsqrt_rearchitecture_retire_results.json`

別実装の確認: `invsqrt_rearchitecture_retire_audit.json`

## 4. 次に進めるなら

### 候補 A: 45-qubit 化を複数のピークで同時に成立させる

公開祖先には、残差 h0 の情報を指数 flag に詰め、seed の後で **2 CCX で再生成**する具体的な式がある。`patch_w47_body.py` の `PACK` と `unpack_h0_after_seed` が対応箇所である。これは第一 loader 付近の 1 本を空ける設計材料になる。

ただし、第一 loader だけ下げても全体 Q は下がらない。位相処理では保持する積を減らす schedule、第二 loader と逆算術では別の所有者の再利用が必要になる。現 e46 の 64 行 generator と統合し、各ピークを同時に検査する必要がある。

参考として、現在の総 Toffoli-equivalent を約 1711.294 とすると、位相余裕を保ったまま **46 → 45 qubits** にできる場合、追加の Toffoli-equivalent が **約 38.03 未満**ならコストは改善する。これはコスト上の予算であり、45Q 回路が完成したという意味ではない。

### 候補 B: 係数表と末尾除算の丸めを同時に最適化する

今回は現在の係数表を固定したまま末尾の値を粗くしたため、不合格だった。次に精度を下げるなら、6-bit address の係数表も同時に変更し、各区間の必要位相範囲から逆向きに整数係数を fit する方が筋がよい。33 角度だけの再調整とは別の問題になる。

この方向は今後の設計候補で、改善量は未計算。現在 e46 を作った 64 行 fork の生成器を得るか、対応するテーブルと算術仕様を実バイナリから再構成するところから始める必要がある。

## 再現

ワークスペースの `gvqcc_repo/` の親で実行する。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python gvqcc_repo/invsqrt_rearchitecture_phase_screen.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python gvqcc_repo/invsqrt_rearchitecture_phase_refit.py drop1 drop2 drop3 carry1 carry2 carry12 carry3
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python gvqcc_repo/invsqrt_rearchitecture_retire_probe.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python gvqcc_repo/invsqrt_rearchitecture_verify_certificates.py
```

`phase_screen.py` は既存の `invsqrt_structural_extract.py` を bit-packed シミュレータとして利用する。LP の依存は NumPy と SciPy、抽出器のコンパイルには g++ が必要。全 200M shots や GPU は使っていない。

取得ソースのハッシュ、対象回路、公開祖先と非公開 fork の区別は `invsqrt_rearchitecture_provenance.json` に記録した。上流のソース・現提出用回路・既存実験ファイルは変更していない。
