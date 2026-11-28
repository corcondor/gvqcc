# GVQCC Research / セッション横断ナレッジ

2026-11-20時点。過去の実装・失敗・採否と、次の探索を引き継ぐための**追記型インデックス**です。新しいセッションでは、研究開始前に下記2ファイルを確認してください。

- [2026-11-20 横断研究ノート](2026-11-20_cross_session_synthesis.md): DQI / GF(4096) / invsqrt / chemistry、HMR位相、ベンチマーク、反例、学習・テンソル再合成・幅削減の次の実験。
- [実験・スコア台帳(JSON)](2026-11-20_evidence_ledger.json): 10個の比較スナップショット、12種の探索、6つの次の実験、採用必須ゲート。
- [スコア感度の計算ツール](score_sensitivity.py): Q²×平均Toffoli×反復費用と幾何平均で、幅・T・他タスクのコスト交換を定量比較。

- [会話・Kaggle・成果物のアーカイブ](archive/README.md): 取得可能な会話本文、ノートブック・提出の版、ZIPと検証原票の索引。

- [2026-11-20 GF(2)入力部分空間と化学H2再学習](2026-11-20_dqi_subspace_and_chemistry_refit.md): DQI 2651組の3族分類、共有入力211組、化学H2係数によるλ_eff 46.920883857→46.898706508の物理式改善、既知の失敗・検証範囲・採否理由。
- [部分空間スキャナ](dqi_pair_input_subspace_scan.py) / [化学H2再学習コード](chemistry_h2_constrained_refit.py) / [機械可読実験台帳](2026-11-20_dqi_subspaces_chemistry_refit_receipt.json): 再現・親SHA・成果物SHA・公式検証未実行の区別。

**2026-11-20 厳密採点仕様訂正**: [化学H2係数再学習](2026-11-20_dqi_subspace_and_chemistry_refit.md)で報告された λ_eff 46.898706508 は E_gap=3.9097475 が公式の厳密下限 3.914898 に届かず **不採用**。`H1_I`/`Hsym_lower` は公式Verifierで固定値に上書きされるため、この変更での救済は不可。E_gap、Λの上下限、20mHa、KMB契約を同時に満たす前にはスコア向上として記録しない。現時点でこの再学習による有効スコア更新は0。

- [2026-11-20 スコア厳密追試と縮約陰性結果](2026-11-20_scoremax_strict_counterexamples.md): 固定S/βによる再採点、H2改善候補のE_gap下限違反、zero-eigen/zero-H2の局所KKT、ANGLE+invsqrtの3〜6 CCX計7,878窓を整理。
- [化学採点の固定シフト・厳密floorガード](chemistry_fixed_shift_score_gate.py): `H1_I`/`Hsym_lower` の提出値上書きを再現し、Lambda>49とE_gap>3.914898を必ず判定する読取専用CLI。


## 2026-11-23: 構造パターン台帳（追記）

- [ANGLE/FeMoCo 5系統の構造パターン](patterns/README_JA.md): ゼロ振幅Givens、連続バンク・ワード更新、辞書行置換、出力GF(2)基底、無効アドレス補完。
- [決定的ID付き163件の台帳](patterns/ledger_20261123.jsonl) / [4構造の集計](patterns/summary_20261123.json) / [7件の固定シフト公式数値クロスチェック](patterns/official_crosschecks_20261123.jsonl)。
- [実行可能な探索コード](patterns/structural_pattern_library.py) / [7つの単体テスト](patterns/test_structural_pattern_library.py) / [全SHA-256固定](patterns/manifest_20261123.json)。
- **現時点の区別:** 独立FeMoCo数値評価64/64 PASSでも、保存済み公式scoreinfraでの代表7件は4 PASS・3 FAIL（公開C46とR18/C23は基準から境界違反）。**新規KMB・公式KickMix PASS・スコア更新はない**。
- 同一変換の重複再実験はIDで排除し、陰性結果を保持する。別セッションではこの台帳を最初に照合する。

## 継続するときのルール

1. **原票優先**。親・候補SHA、実KMB、検証器、使用した入力/マスク/seed/salt、時間、元の費用と実行平均を実験記録に保存する。会話中の数字だけで「再現済み」にしない。
2. **スコアと正しさの二軸**で判定する。28.32145634975は記録された最高の名目ローカル値だが、固定DQI反例と化学任意標的XORが失敗しており、厳密採用候補ではない。28.5の達成も未確認。
3. **局所改善を最終回路への改善として数えない**。実際の全18ファイルZIPのQ、静的/平均T、HMR/条件処理、回転誤差、物理誤差、固定反例、両公式パネル、CRC/SHAが揃って初めて採用する。
4. **局所スキャンで0を一般的な最適性と呼ばない**。演算の束ね方、複数出力テンソル、測定因果とレジスタlive range、再計算ペブル配置、整数角度の共同学習まで候補とする。
5. **修復の例外を全て残す**。9固定症例に加え、weight 1/3/15、double-zero、degree-gap 3、ゼロ剰余、MBUCマスクの加法性と位相を検証する。後日見つかった反例を前の「PASS」報告で上書きしない。
6. **誤った二重計上を防止**。同じSHAのドナー改善を再計上しない。Local ScoreとKaggle Public/Private Scoreを分ける。Product Retention（待機補助線への積保持）の過去の禁止方針に反する新規変形は行わない。

## 記録すべき1候補の情報

- 名前、日付、親ハッシュ、候補ハッシュ、実装/再現ファイル
- 機能契約（入力、出力、dirty ancilla、HMR位相、公開メモリ、条件）
- 変更した領域、比較可能な静的/平均Toffoli、Q、C/R/J、回転本数とeps
- 公式の全パネル結果、固定反例、化学標的XOR、全てのゼロ/測定枝、反証fixture
- 参照費用、候補費用、スコア計算式、採用/不採用理由
- 提出ZIPの18ファイルハッシュとKaggleに実際に提出したか

既存の研究資料はルートREADMEと、research_anthropic_dqi.md、research_chemistry_qrom.md、research_dqi_ibm_microsoft.md、chemistry_affine_loader_v3_report.mdを参照。今回の横断ノートはこれらの代替ではなく、検索可能な入口として整備したものです。

## 2026-11-23 ANGLE multiple compiler families

Four distinct constructive 7-bit/J5 ANGLE compiler families, 240 all-address-proved circuits, per-file SHA registry, and complete negative-results ledger are stored in [the Japanese experiment memo](2026-11-23_multiangle_results.md) and [v2 experiment archive](data/multiangle/2026-11-23/v2/README.md). Reusable code: [compiler](multi_angle_synthesis.py), [KMX exporter](export_all_kmx.py), [tests](test_multi_angle_synthesis.py). **No competitive KMB or new official score**. The research remains on draft PR #18.

## 2026-11-23: multiangle v3 35-pattern 2100-circuit study

Constructed 35 ANGLE synthesis variants across 4 actual 7-bit angle tables and all 15 banks (2100 KMX in a separately hashed bundle). See [source and methodology](multiangle_v3/README_JA.md), [v3 data registry](data/multiangle/2026-11-23/v3/README.md), and [full Japanese report](multiangle_v3/REPORT_JA.md). New: 3/5/6-bit low address partitions with GF(2) multi-output basis, structural HMR + conditional CZ cleanup, affine low-coordinate variants, and exhaustive 462-way low6-wire selection for C46. All-address symbolic checks PASS; native real-input KickMix verification and new official score **not performed**. The result remains on Draft PR #18.

## 2026-11-23: v4 mathematically constrained cross-high ANF synthesis

[Full Japanese mathematical report](multiangle_v4/REPORT_JA.md), [generator sources](multiangle_v4/), [independent 780-circuit evidence](data/multiangle/2026-11-23/v4/README.md). Three structural classes: global high-invariant parity factors, disjoint high-selector pair matching, and arbitrary high-selector pairs with two-CZ HMR correction. C46 generic KMX cost 10,038 → 9,607 CCX/one pass, 127Q; other C45 candidates improve 12–25 CCX; no official KickMix score. 780 constructed KMX but only 150 distinct byte hashes, recorded explicitly. Official FeMoCo numerical scoreinfra checks pass on the unchanged input tables. Native real C46 KMX parser + KMB roundtrip exercised in PR CI.

## 2026-11-23: v5 complete high-group GF(2) bases

[Mathematical report](multiangle_v5/REPORT_JA.md) · [Full v5 experiment ledger](data/multiangle/2026-11-23/v5/README.md) · [Generator](multiangle_v5/high_group_basis.py) · [Cross-20 negative experiment](multiangle_v5/global_20_basis.py). The emitter changes the basis of up to eight high-address cofactors, enumerates up to 255 candidates per fixed-high-factor group, and solves a **minimum-weight linear-matroid basis** with exact per-candidate conditional-emitter CCX prices. One-way C46: previous generic 9,607 CCX/127Q → new 9,301 CCX/127Q; no comparison to official 3,357T is claimed. 24 controlled settings × 15 banks (360 in-memory symbolic oracle proofs); 90 emitted KMX across C46 and 3 C45 sources plus cross-20 ablations, all independently verified for real addresses, dirty-target outputs and each HMR phase coefficient. C45 remains equal/worse to v4, and globally mixing 20 high states is worse because selector bilinear rank rises. Native KMX→KMB smoke is tested in PR CI; no full official KickMix verifier or new Kaggle score. All artifacts retain source hashes and negative cases.

## 2026-11-23: v6 cross-group GL(20,2) + rank-r HMR

[Mathematics and status](multiangle_v6/README_JA.md) · [source code](multiangle_v6/global20_rank_hmr.py) · [15-bank evidence](data/multiangle/2026-11-23/v6/summary.json). This explicitly replaces rank-2/3 selector inverse CCX with HMR and rank-r conditional CZ phase corrections and applies exact-cost elementary basis exchanges **across** the previously fixed 8-high-state partitions. C46 9,301→9,253 one-way CCX, 127Q, 24 accepted exchanges (21 cross-group), 15 exact all-address/phase KMX proofs and adversarial deleted-CZ negative tests. Native HMR/CX/CZ parser acceptance is tested in CI. No official full verifier/Kaggle score; original 3,357T loader is substantially lower.
