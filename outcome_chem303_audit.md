# DFTHC の303作業量子ビットは何を変えると減るか

## 結論

303 は、提出回路の測定値ではなく、公式の `SpinFreeData_V1` が計算する `inner_state_prep` の推定値。提出できる回路は `ANGLE_k` ローダーだけなので、inner QROM を独自に書き換えて303→176にするインターフェースはない。公式 verifier の変更は行っていない。

もう一つの制限は `ANGLE_k.num_qubits <= 128`。現行の11選択ビット＋5×8出力ビットでは作業領域は最大77ビットであり、303ビットまで自由にローダー合成へ投入できるわけではない。

## 提出物から動かせる変数

- `W.shape=(R,B,C)`、`H2_I`、回路が読み出す整数角度、`tree_edges` を変更できる。R/B/Cは回路アドレス数と因子分解を整合させ、公式の二つの20mHa条件等を再検証する必要がある。
- `brot` とバッチ数 `J` は回路のwordレジスタから決まる。NPZに同名変数を加えるだけでは変わらない。75角度を `ceil(75/J)` 回路で読み、最後の未使用出力は0にする。
- N=76、chi=10は固定。提出した`H1_I`と`Hsym_lower`は固定基準値で上書きされる。QROAMのブロックサイズや`optimize_qubits`は提出物から指定できない。

## 公式式で計算した境界

基準は公開v27のR=8、B=143、C=44、brot=8、J=5、片道ローダー4030 Toffoli、総T=14722、Q=427。以下の「ローダー上限」はlambdaが基準と同じ場合に基準コストを下回る条件であり、候補の実測値ではない。

| 変更 | inner作業Q | 総Q | ローダー以外のT | 改善に必要な片道ローダーT |
|---|---:|---:|---:|---:|
| 基準 | 303 | 427 | 6662 | <4030 |
| J=4 | 303 | 419 | 6662 | <4170.544 |
| J=3 | 303 | 411 | 6662 | <4316.560 |
| J=6 | 303 | 435 | 6662 | <3894.625 |
| brot=7 | 303 | 422 | 6362 | <4267.216 |
| brot=6 | 303 | 417 | 6062 | <4506.523 |
| brot=3 | 152 | 251 | 8178 | <8433.498 |
| C=43 | 303 | 427 | 6584 | <4069 |
| C=40 | 303 | 427 | 6348 | <4187 |
| B=128 | 575 | 698 | 5495 | <1755.576 |

精度を8→7/6に下げても303の段差は越えない。3bitで152になるが、精度を維持できる候補は生成していない。B/R/Cの減少でQが必ず減るとも限らない。公式の自動QROAM選択により、B=128では575へ増える。

## 実装候補として残るもの

同じ整数角度の **J=4再バッチ化** は、物理的誤差とlambdaを変えずに試せる有効な方向。使用可能なローダー作業量子ビットは85になり、全19回路合計の片道Toffoliを4170以下にできれば改善する。元の4030から許される増加は140程度しかないため、単純分割による共通中間項の再計算がこの余裕を使い切る可能性がある。実際の再合成と全入力検証が必要であり、現段階で改善達成とはしない。

J=6は13回路になる代わりに作業領域69ビット以下が必要で、片道Toffoliを3894以下に下げる必要がある。どちらも単にレジスタ名を変える修正ではない。

以前のB142固定プレフィックス実験は、許容20mHaに対する必要誤差下限27.380mHaが既に計算済みで再実行しなかった。C43の固定角度局所最適化も21.122mHaで失敗済み。ただしこれは新しい整数角度を使うC43因子分解まで否定する結果ではない。

## 根拠ファイル

- `official_sources/Inzainos/verifiers/dfthcsos/verify.py`: `load_inputs`, `angles_costs`, `heuristic_costs`, `score_from_metrics`
- `official_sources/Inzainos/verifiers/dfthcsos/scoreinfra/costs_prepare.py`: `SpinFreeData_V1`
- `official_sources/Inzainos/verifiers/dfthcsos/scoreinfra/circuits.py`: `register_layout`, `recover_words_from_circuits`
- `official_sources/Inzainos/verifiers/dfthcsos/SCORING_README.md`: Scoring節
- `score3_chemistry_b142_span_bound.json`, `score_chemistry_c43_whiten_converged.json`: 既実施の失敗条件とその適用範囲

`outcome_chem303_resources.py` と `outcome_chem303_resources.json` に27設定の再現可能な計算を保存。新しい有効回路・提出ZIPはこの監査では生成していない。
