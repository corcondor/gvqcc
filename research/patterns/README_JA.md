# GVQCC 構造パターンライブラリ / 証拠台帳 — 2026-11-23

**ステータス：研究データ。新しいKMB・公式KickMix合格・スコア更新は無し。**

前段の `research/joint_word_feedback.py` で扱った単一角度ワード変更に対し、新たに**数学的に意味の異なる5パターン**をコード化した。既存の局所CCX削減を追加する研究ではなく、**同じ物理表現を保つ変換と、段間の中間表現の取り方**に着目する。

- `structural_pattern_library.py` — 5種類の構造生成・GF(2)計測・物理評価・追加書込型の重複防止台帳
- `test_structural_pattern_library.py` — 7個の独立数学テスト
- `ledger.jsonl` — 163個の決定的実験ID付きレコード（4基準＋64物理数値評価＋95代数的スクリーニング）
- `summary.json` — 4つの物理表現の結果集計
- `run_official_batch.py`, `crosscheck_cases.json`, `official_crosschecks.jsonl` — **別評価器**を用いた公式scoreinfraの物理数値照合7件（PASS 4、FAIL 3）
- `manifest.json` — 実装・台帳・参照入力・数値評価器のSHA-256

## 5パターンと、それぞれの数学的根拠

| ID | パターン | 保持する量・探索する自由度 | 今回の検査段階 |
|---|---|---|---|
| P1 | null_givens | Givensの回転前の親・子振幅が両方0なら角度変更後もそのベクトルが変化しない | 度数構造 + 独立FeMoCo |
| P2 | chained_word_run | 同じ行・ワード位置の連続バンクをXOR反転すると、差分ローダーへの効果が**区間の両端だけ**に残る | GF2段間境界 + 独立FeMoCo |
| P3 | within_rank_row_permutation | 同じrank内で角度ワード行とWの行を同時置換すれば、FeMoCoの二電子和は厳密に同一 | GF2全15段 + 独立FeMoCo |
| P4 | linear_output_basis | 5出力ビット間のCNOT相当の可逆GF2基底変更。合成器への入力表現は変わるが、最終出力を戻せる | GF2のみ、未合成 |
| P5 | invalid_address_padding | 16行ブロックの未使用末尾行（正規アドレス外）に対する合法的な自由設定 | GF2のみ、未合成 |

**注意：** P4の「各出力のランク和」は変動しても、全部の出力を縦に積んだGF2行列の総ランクは変わらない。これは実Toffoliの節約を意味しない。P5の端数の未使用行は公式検証器の選択範囲に入らないことを前提とし、生成器の境界処理とKMBで確認するまで採用不可。

## 4物理表現・同じスクリーニング上限での結果

各入力についてdead-wordとrun-lengthは各最大100件、swapは同rankの先頭4組×rank数、独立物理評価は各パターン上位5件＋swapで悪い対照1件を記録。

| 表現 | (R,B,C) | bit0混合ランク和 | P1有利/100 | P2有利/100 | P3有利/検査数 |
|---|---|---:|---:|---:|---:|
| 公開V8 C46 | (9,127,46) | 382 | 0 | 1 | 0/36 |
| C45/B130 | (9,130,45) | 1,121 | 17 | 18 | 14/36 |
| C45/B129 | (9,129,45) | 1,117 | 14 | 18 | 0/36 |
| C46→R18/C23 等価分割 | (18,127,23) | 455 | 0 | 0 | 0/72 |

**実験例（数値物理評価はPASSだが、Toffoli削減未確認）**

- C45/B130: 同rank内の辞書行 (rank4,b127)↔(rank4,b128) の置換で混合ランク和 **1,121→1,116**。Wを対応して交換し、元と同じ二電子テンソルを表す。
- C45/B129: ゼロ振幅Givensの (row332,col60) を1bit反転すると混合ランク和は **1,117→1,115**。公式scoreinfraの物理数値評価はPASS。
- C46: (row479,cols28,33) の2段ワード反転で混合ランク和 **382→381**。ただし**公式scoreinfraでは基準の段階からFAIL**。
- R18/C23: P4の出力基底操作で、slot3/bit0のある単一出力混合ランクは4→1。ただし総ランク不変で、実回路の利益は未立証。

### 厳密な数値PASSと独立評価PASSを区別する

保存済み `physical_verify.py` の独立FeMoCo計算では、選んだ64件はすべて`error_1`, `error_2`, `Lambda`, `E_gap`の制約をPASSした。

**しかし**、別途実施した保存済み公式scoreinfra + 固定シフト + 公式FeMoCo FCIDUMPによる7件の数値照合では以下となる。

| 入力 | baseline | 代表構造変更 |
|---|---|---|
| C46/B127 | **FAIL** | **FAIL** |
| C45/B130 | PASS | PASS |
| C45/B129 | PASS | PASS |
| R18/C23 | **FAIL** | 未照合 |

C46/R18のe1は約 **0.020000001582605 Ha**、E_gapは約 **3.91489779186304** で、厳密な境界を超えている。既存の実験で「独立PASSだから採用」と判断していたなら誤り。コードの版、固定シフト、入力ハッシュ、丸め差を調査するまで**不採用**とする（公開作者による合格済み回路の評価を否定するものではない）。

全7件について `official_crosschecks.jsonl` に公式scoreinfra関数のPythonソース・固定シフト・FCIDUMPそれぞれのSHAを記録した。`OFFICIAL_SCOREINFRA_PHYSICS_ONLY`は**KickMixのネイティブ量子回路検証・KMBの値位相テストと同義ではない**。

## 研究用の再現コマンド

```
OPENBLAS_NUM_THREADS=1 python -m unittest -v research/patterns/test_structural_pattern_library.py
OPENBLAS_NUM_THREADS=1 python research/patterns/structural_pattern_library.py \
  --seeds /DATA/c46_public_v8.npz /DATA/c45_original.npz \
          /DATA/c45_B129_JACOBI_OPTIMIZED.npz /DATA/candidate_R18_C23_split2.npz \
  --physical-module /DATA/physical_verify.py \
  --reference /DATA/chem_gpu_inputs.npz \
  --ledger /RUNS/journal.jsonl --summary /RUNS/summary.json \
  --budget 5 --max-screen-actions 100
OPENBLAS_NUM_THREADS=1 python research/patterns/run_official_batch.py \
  --cases /DATA/crosscheck_cases.json \
  --verifier-root /DATA/official_verifiers \
  --out /RUNS/official_crosschecks.jsonl
```

外部データは配布しない。添付の `manifest.json` に原本ハッシュを固定する。`crosscheck_cases.json`内の `/mnt/data/...` はこの実行環境の実際のパス。別環境では4つの原本NPZ配置に合わせて更新する。

## 蓄積・再実行ルール

- 各実験IDは `SHA256(schema version + seed SHA256 + pattern + canonical action)`。台帳が同じIDを含めば追加せず、上書きも行わない。
- 変更コードやアルゴリズムを変えた場合は `VERSION` を新しいものにする。厳密な再現性はソースSHAと入力SHAの双方に依存する。
- 生成器の候補数・探索打切り・失敗例を保存し、検証なしの「改善数」を成果にしない。
- 証拠の段階は「代数的スクリーニング → 独立物理数値 → 公式scoreinfra数値 → 新KMX/KMB全合法アドレス＋位相・作業線 → 公式KickMix → Kaggle提出」。段階を飛び越えない。
- 既存の `manwithacat` の `price_words` / padded-row / replan と重なる部分は先行手法とし、新規性を主張しない。

**次の具体的な不足:** P1–P5を実KMBへ変換する多出力XAG・生存期間・HMR対応の合成器。代理ランクはその入力を選別するだけで、今回の実験では競技スコアを改善していない。

## 追加：履歴検索とCSV

- [163件を表形式にしたCSV](pattern_catalog_20261123.csv)（UTF-8、LF改行）。元データの真実の所在はJSONL台帳で、CSVは再生成可能な派生物。
- [フィルタ付き検索CLI](query_pattern_ledger.py): `python research/patterns/query_pattern_ledger.py research/patterns/ledger_20261123.jsonl --family within_rank_row_permutation --rank-le 0 --top 10`
- 前バージョンと同じ実験IDの再実行はスキップする。新コード・新ソースはVERSIONおよび入力SHAで区別する。
