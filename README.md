# GVQCC — DQI 回路の解析・計算

[Google Quantum AI — Verifiable Quantum Circuit Compilation](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/) の DQI 課題に向けた、回路解析と有限体演算の検証コードです。

大きい KMB 回路を全展開せずに調べる監査ツール、共有積を式に起こす解析器、有限体演算の検証コードをまとめています。2026-11-14には、実際の公開 `821bf8d157c0` 回路を改良し、公式DQI検証コードの102,400ショット検証まで実施しました。大きい回路ファイルは再現スクリプトで取得・生成します。

## QFTはどこで使うか

DQIアルゴリズム全体はQFTを使います。本競技のGF(2^12)上ではWalsh–Hadamard型の変換です。一方、提出する `dqi.kmb` はその前に必要な復号結果の位相補正を実装します。独立したH/QFTを提出回路に挿入することと、古典的な設計段階でフーリエ/Walsh基底を使うことは別です。[公式資料と提出範囲の説明](qft_scope_and_optimization.md)にまとめました。

## 最新の実測結果：v2（480 CCX + gauge128）

**Kaggle Public Scoreは27.27654で確定し、元の27.30683を下回りました。スコア改善を達成した提出としては採用しません。** 2026-11-15（日本時間）に同じノートブックversionの2行がともにComplete・27.27654になったことを確認しました。最良提出として選択されているのは元の27.30683です。[採点完了の記録](results/2026-11-15/kaggle_v2_submission_complete.json)を参照してください。

[費用差の再計算](score_loss_v2_report.md)では、今回のToffoli削減、化学lambdaの小差、DQIで新たに合計1件の失敗があったという仮定を入れると、27.27653615となり実表示と一致します。採点側の課題別結果は未取得なので、1件の失敗は有力な推定です。v1からの17メンバー保持は確認済みですが、元27.30683のZIPとは直接照合できていません。過去の[提出受付](results/2026-11-15/kaggle_v2_submission_pending.json)と[採点待ち再確認](results/2026-11-15/kaggle_v2_submission_recheck.json)は履歴として残しています。

**追加の384件のCCX削減を組み合わせたv2が、ローカルとKaggle競技添付環境の両方で、公式DQI検証コードの102,400ショット検証にPASSしました。値エラー・位相エラーはともに0です。** 従来の96件の削減と合わせて、構造変換による削減は480 CCXです。量子ビット数は889を維持しています。

| 項目 | v2の実測値 |
|---|---:|
| 検証ショット数 | 102,400 |
| 値エラー / 位相エラー | 0 / 0 |
| 量子ビット数 | 889 |
| 平均Toffoli数 | 382115.5671582031 |
| 反復係数 R | 1.1912604648115832 |
| ローカルDQIコスト | 359753461767.22644 |
| 信頼度設定 / salt / seed | `log2_delta=-128` / 空文字 / 既定値 |

候補SHA-256は `e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7` です。検証結果の原本コピーは [v2_candidate_full102400.json](results/2026-11-14/v2_candidate_full102400.json) にあります。公式検証コードは変更せず、ローカルのKickmix 1.0.0で実行しました。

**同じ102,400入力で元回路と比較する計算も完了しました。** 両回路とも値エラー・位相エラーは0、反復係数Rも一致しています。元回路の平均Toffoli数382599.9932617188に対し、v2は382115.5671582031で、平均 **484.426103515625 Toffoli削減、DQIコスト0.1266142478%改善**です。内訳は無条件のCCX削減480と、gauge変更による平均4.426103515625です。比較にはv2の通常の回路ハッシュ由来seedを使い、seedの探索はしていません。[入力を固定した比較結果](dqi_combined_v2_paired_comparison.json)と[元回路の検証記録](dqi_baseline_v2_paired_verification.json)を参照してください。

2026-11-15に、[Kaggle CPU notebook](https://www.kaggle.com/code/geocpuresearch/gvqcc-verified-480ccx-gauge128)のversion 1（scriptVersionId `369627280`）が **SUCCESS** で完了したことを確認しました。ノートブック全体の実行時間は408.2秒。競技添付Kickmixと公式verifierで102,400ショットPASS、値エラー0・位相エラー0、平均Toffoli `382115.5671582031`、DQI費用 `359753461767.22644`を再現しました。[Kaggle v2の実行記録](results/2026-11-15/kaggle_v2_full_verification.json)を参照してください。これはノートブックの検証結果であり、競技提出・Public Score取得の完了を示すものではありません。

提出用の完全ZIP `submission_v2_full.zip` もローカルで組み立てました。18メンバー・50,321,865 bytes、SHA-256 `fbc5b37a1cfda9ac5e5277e0b16fb6c2d7b99d691a1bd3f4ce8a992ca2d9892f`。DQIは検証済みe986、他の17メンバーは実行済みv1 workerの全入力pinと一致し、全メンバーを読戻してCRC/SHAを確認しています。[構成と検証記録](results/2026-11-14/submission_v2_full_reconstruction.json)には、Kaggle実出力ZIPを直接比較したものではないことと、重い回路検証を再実行していないことを明記しています。

v1は別途、Kaggleの競技添付Kickmixと公式検証コードでも102,400ショットPASSし、ローカルと同じ数値を再現しました。[Kaggle v1の実行記録](results/2026-11-14/kaggle_v1_full_verification.json)はノートブック実行の証拠であり、競技リーダーボード採点の結果ではありません。v1の回路・workerと以下の計算履歴は保持しています。

### v2を再現する

依存パッケージと計算資源は後述の「実回路の再現と検証」を参照してください。

```bash
python reproduce_dqi_candidate.py --work-dir dqi_run_v2 --variant 480gauge128
```

まず従来の96件削減＋gauge128候補 `aafed8…` を正確に再現し、384件の入力側CCX因数分解を追加します。16ブロックの多項式証明・削減数・最終SHAを確認してから、変更後の全回路を新しく検証します。`dqi_input_factor384.json` に変換の証明と数値を保存します。variantを省略した場合は従来の `96gauge128` を実行します。

既存の提出ZIP内のDQIだけを更新する場合：

```bash
python reproduce_dqi_candidate.py --work-dir dqi_run_v2_zip --variant 480gauge128 --baseline-zip ORIGINAL_SUBMISSION.zip
```

`invsqrt`とchemistryの各メンバーはバイト単位で保持し、全回路検証が通った場合だけ新しいZIPを作ります。Kaggleで使う自己完結版は [kaggle_score_worker_v2.py](kaggle_score_worker_v2.py)、埋め込みの確認結果は [kaggle_score_worker_v2_audit.json](kaggle_score_worker_v2_audit.json) です。これは実行用コードの静的・統合監査であり、Kaggleでのv2実行結果ではありません。

### 追加：Kaggle v1出力からv2へ進める小型worker

[kaggle_promote_v1_to_v2.py](kaggle_promote_v1_to_v2.py) は、検証済みv1ノートブックの出力を再利用する52,597 bytesのオフラインworkerです。埋め込みを含む全行を166文字以下にし、編集画面で巨大な1行を処理せずに済む形にしました。必要な入力は競技データと、`geocpuresearch/gvqcc-verified-96ccx-gauge128` の **version 1（scriptVersionId 369610226）出力**の2件です。

旧 `submission.zip` 全体のSHA-256 `2f5c27607830431425889289c5d59c3f39fc006add37711db345ee4b26016ebf` と、そのDQI `aafed8…` を確認してから、384件の追加置換を適用します。最終 `e986d4…` のハッシュと16ブロックの証明を照合し、競技添付engine・公式verifierで102,400ショットのPASSを要求します。seedは既定値、saltは空、信頼度は `log2_delta=-128` です。

PASS後に、その他17メンバーの非圧縮内容をバイト単位で保持して `/kaggle/working/submission.zip` を作ります。変換証明・全検証JSON・メンバー別ハッシュも出力します。`invsqrt`とchemistryの検証は、この昇格処理では再実行しません。Kaggleへの競技提出を行うコードは含みません。

[ビルド記録](kaggle_promote_v1_to_v2_build.json)と[静的・合成ZIP監査](kaggle_promote_v1_to_v2_audit.json)では、埋込コードのハッシュと構文、17メンバーの保持、元ZIP不変、上書き・重複拒否を確認しました。これはworkerの監査結果であり、Kaggleでの実行完了記録ではありません。既存v1/v2 workerは変更していません。

### 一次資料から次の実験へ

- [Claude研究の実装・探索手順・公開範囲](research_anthropic_method.md)：Anthropic/Harvardの原著、公開コード`andigu/uncompute`、独立評価と複数設計の保存、今回の競技へ適用する運転案。
- [Claude研究のDQIと現回路の比較](research_anthropic_dqi.md)：論文のBM設計、現821系の出自、費用の定義差、履歴復元を移植する際の条件。
- [Claude研究の化学・数値回路と現タスクの比較](research_anthropic_chemistry.md)：Fe2S2とDFTHCの違い、表の重複、制御された二次位相、量子化を含む近似設計。
- [IBM・MicrosoftのDQI関連研究](research_dqi_ibm_microsoft.md)：可換性を使ったパターン照合、入力側CCX因数分解、依存関係と作業領域の交換条件。
- [NTT・富士通の研究と適用条件](research_ntt_fujitsu.md)：QROMのデータ順序探索、整数加算、制御回転の合成。本競技の費用との違いを整理。
- [化学・QROMの研究対応表](research_chemistry_qrom.md)：現4033ローダーの符号、許される因子ラベル変更、SelectCopyなどを実費用で比較する条件。

[4033ローダーの構造監査](chemistry_4033_structure_audit.json)では、実KMBのCCX合計4033と、完全な16行ブロック76個における既知のReed–Muller条件を確認しました。同じrの内部に収まる16行ブロックは64個です。再現コードは [audit_chemistry_4033_structure.py](audit_chemistry_4033_structure.py)。公開資料から元の4033生成器は発見できておらず、生成器の同一コスト再現・行置換による改善実験はまだ行っていません。

Claude論文の反復ワードによるQROM削減を受け、[完全ワードの重複監査](anthropic_repeated_rows_audit.json)も実施しました。15表すべてで1,220個の40bit差分ワードがすべて異なり、完全ワードの重複は0でした。単なる行置換では新たな完全ワードの重複は作れません。部分ビットの共有や線形関係の利用は、この監査で否定していません。

状態から履歴を復元する発想についても、[rolling flagの限定反例探索](dqi_rolling_flag_screen_report.md)を実施しました。許容された既知の25入力・425ノード状態で、ゼロ判定やパリティによる4種類の安い復元式を反証しました。同じ公開ノード内の反例であり、ノードごとに異なる係数を許すアフィン式も含みます。より複雑な非線形復元式まで否定した結果ではありません。検証済み回路は変更していません。

追加の[共通制御・二次位相簡約スキャン](dqi_quadratic_phase_scan_report.md)では、原821回路のCCZ全7000個を、条件変更・測定等を跨がない区間に分けて調べました。9 CCZを持つ18区間の全9036部分集合には共通線形因子を持つものが216件ありましたが、元のCCZ数を減らせるものは0件でした。共通制御を持つ別の12 CCZ区間2個も、二次形式のpolar rankが24で、この簡約方式では各12 CCZが必要でした。

新規の全区間・部分集合スキャン2本と結果JSON2件は同レポートから参照できます。合成規則は160ケースの独立シミュレーション、線形因子判定は31,713通りの直接代入との一致を確認しました。測定を跨ぐ変換、非線形な変数変換、一般的な三次形式の再合成まで否定する結果ではありません。追加削減が0件のため、検証済みe986候補・worker・KMBは変更していません。

続く[CNOT基底変換を含むCCX共有スキャン](dqi_affine_ccx_report.md)では、e986の全363,694 CCXを53,495区間に分け、制御の入口線形形式と出口ファンアウトを共通基底で比較しました。同じ出口方向を持つ562グループの二次rank簡約と、隠れた同一二次積の共有による追加削減は0件でした。236.21秒・最大約462.2 MiB、独立真理値検査もPASS。任意のtensor再合成まで最適と判断する結果ではありません。

固定gauge128に入力mask由来の32候補を追加する[別のgauge実験](dqi_gauge_dynamic32_report.md)も完了しました。[同一1024入力での比較](dqi_gauge_dynamic32_paired_comparison.json)では、syndrome・ancilla・位相の全出力が一致し、平均 **5.0595703125 Toffoli** を追加削減しました。候補の失敗入力はe986でも同じ失敗となっています。一方、[既定条件の全102,400ショット結果](dqi_gauge_dynamic32_compact_full102400.json)はPASSながら値エラー1・位相エラー0、DQI費用 `361400858314.11945` で、e986の既定条件より0.4579%悪化しました。回路hashが変わると既定の検証入力も変わるため、この差から真の失敗確率の悪化は断定できません。開発時の比較基準にはe986を使いますが、最良の競技提出は元の27.30683です。

### 追加：GF(2^24)乗算の構造探索

[実ブロックの代数同定と再合成](dqi_algebra_report.md)では、99 CCXの積が真のGF(2^24)上の共役積であることを576基底対で確認しました。255・3825・65025個の積を許す3種類の辞書で、評価点を跨ぐ共有も探索しましたが、最良は99のままでした。元の11点内の対称積だけに限定した99の下限は確認しましたが、一般の回路や他の辞書に対する最適性の証明ではありません。候補回路は生成していません。

### 追加：スコア低下とゼロ例外の原因を追う

[既知失敗の分類](dqi_rare_failure_admission.json)では、保存されたweight31/33の2入力を独立な有限体実装で再構成し、active quadratic chartの分子／分母の剰余ゼロという除外条件に一致させました。低weight cutoff不足やhalf-EEAのdegree gapではありません。これは保存済み失敗の分類であり、今回の非公開採点で失敗した入力そのものを取得した結果ではありません。

一般のゼロ例外へ対応する[可逆な局所chart切替](dqi_rare_chart_v2_report.md)を実装し、14,335入力×4測定seedで値・scratch・位相を確認しました。ただし、単純追加は平均164T/node、35nodeなら5,740Tを増やし、chart履歴と後続演算も変更する必要があります。現在の費用を改善する全decoderとしては採用していません。

[資源見積もりの再監査](resource_claims_v2_report.md)では、ANGLE回路の128Q上限により作業領域は最大77本であることを確認しました。また過去のEEA窓で数えた78CCXは、完全な99CCXブロックから先頭21CCXを除いた数と正確に一致します。現在の完全GF12積は42CCX、GF24積は99CCXです。「303個まで補助量子ビットを追加」「78CCX GF12を54CCXへ」という見積もりを、そのまま改善量に使いません。

## v1（96 CCX + gauge128）の実測結果・履歴

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

## invsqrtの位相基底を変えた追加計算

[実回路を使った77件の探索](invsqrt_structural_report.md)では、既存q30の回転を削除して残りを調整した **32 generic rotations** の候補を生成しました。全3,133,452入力の整数位相チェックと、各12,288 native shotsの入力・scratch・位相チェックはPASSです。ただし最小誤差余裕が縮まり、合成費用を含む内部コストは予測79,323.82で、元e46の78,719.53より悪化しました。q42という新しい位相基底を追加した34回転候補も、誤差余裕は44%増えましたが費用は増加しました。

**回転削除が可能か、固定基底のminimaxが最適か、総費用が最小かは別の問題です。** 旧ログの「削除不可」「global optimal」を回路構造全体の定理として扱いません。今回の候補は不採用で、公式200,540,928-shot検証や新たなKaggle提出は行っていません。[全入力結果](invsqrt_structural_domain.json)、[native検算](invsqrt_structural_native.json)、[結果要約](invsqrt_structural_summary.json)を参照してください。

[独立した構造監査](invsqrt_structural_independent_audit.json)では、変更した回転までの条件付き量子命令がすべて対角であること、挿入点が無条件であること、追加したCX–回転–CX以外の非位相命令が元回路と完全一致することを確認しました。新しい位相のBoolean値が測定結果に依存しないことを、有限ショットの検算とは別に確認しています。

[算術精度と保持値の再生成を変える実験](invsqrt_rearchitecture_report.md)も追加しました。7種類の算術変更を全3,133,452入力上で位相refitしましたが、最良でも誤差/許容が1.11729で採用できませんでした。位相で読まれないq42/q45の二次Boolean式による再生成には、合法入力によるGF(2)反証を得ました。これらは特定の算術変更・切断点の結果であり、別の係数表や高次の再生成まで排除しません。現e46は変更していません。

## Chemistryの追加計算

### 整数角度の変更とローダーを一緒に扱う

[address-affineな角度変更の実装](chemistry_affine_loader_v3_report.md)を追加しました。既存ローダーの前後にX/CXを加え、角度語の低位ビットをaddressの関数でXOR変更します。610語を変更する具体例で、全36,600往復遷移と全HMR分岐の位相検証、保存後の再読込、nativeの2 seed検算を通しました。Toffoliは **4033/pass**、各回路の最大Qは **128** を維持しています。逆方向では同じ回路を再適用するため、一般的な任意bitの変更が安全とは仮定せず、意図的な不正tag変更を拒否することも確認しました。この例の化学精度やスコア改善を示す結果ではありません。

[整数角度の探索結果](chemistry_discrete_v3_report.md)では、勾配だけによる候補選択に二次の誤差見積もりを加え、実際に角度語を変更してW/H2_Iを再fitしました。1語変更の数値適合候補は得られましたが、利益は微小で、その1語をロードする追加費用も確定していません。Toffoliを増やさないaffine候補では今回の短時間refitで適合する改善を得られず、新規提出はしていません。

採択条件を「ローダー4033以下」に固定しません。[資源の損益計算](chemistry_angle_search_v3_budget.json)では、整数角度から再評価したlambdaが44.17なら **4489/pass**、45.3なら **4294/pass** でも、Q=427と他の費用が同じなら基準費用を下回ります。連続角度のlambdaをそのまま採点値に使うことはできません。[実ファイルの探索範囲と出発点](chemistry_angle_search_v3_context.md)にも、外部WSLの最新候補は未取得で、この独立実験は公開基準から始めたことを記録しています。

[固定角度の重み再最適化](chemistry_polish_v2_report.md)を独立にやり直し、ゼロ近傍の絶対値と固有値の非滑らかさを扱う近接法・Schur補行列制約を試しました。C44の最良は `lambda_eff=46.906578536058`、再現した基準比の費用改善は **0.000023392%** にとどまります。ユーザーの別基準 `46.905894137` を上回った結果ではありません。

さらに、角度表91,500要素とローダーを保ちながら因子をC44→45へ増やす[構造変更](chemistry_rank_extension_v2_audit.md)を実装しました。最良 `lambda_eff=46.897594667538` は両誤差・gap条件の公式数値評価を満たしますが、Toffoliが14728→14807へ増えるため、総費用は基準より **0.517114334%悪化**します。改善に必要なlambdaは **46.65632810718未満**です。どちらも今回の採用・提出対象にはしていません。[最終数値・ハッシュ](chemistry_polish_v2_summary.json)と、W/H2_Iだけの小型チェックポイントおよび[復元コード](chemistry_polish_v2_restore.py)を保存しています。全配列一致は確認済みですが、これらの候補について全ANGLE回路検証を実行したという意味ではありません。

外部WSLログの `lambda_eff=45.308766` の実配列は共有環境になく、独立確認できていません。報告された時点の `error_2=20.396 mHa` は許容20 mHaを超えています。最終ポリッシュ後のNPZを取得するまで、適合候補や大域最適解としては扱いません。

[実到達入力の積依存と16行ブロックの探索](chemistry_relation_report.md)では、既存2706積の商空間依存による追加削減は0でした。別の出力基底を使う方法も、14回路・計1,221,388候補を評価しましたが、補正前の積数指標だけで現回路を上回るため不採用です。完成回路のToffoli数や全回路の下界を示した結果ではありません。k=0、別の非線形積、出力間の新たな積共有など、今回の探索範囲外をレポートに明記しています。

さらに[複数の積をまとめる再合成](chemistry_joint_product_report.md)で、k=1〜14の2706個のCCX積・260,835ペアを調べました。共通因子の統合、同一出力方向の二次rank分解、1回のXOR変換後の3→2統合は追加削減0件でした。14回路を正規化した式から再構築し、全34,160遷移と測定位相の厳密検証にPASSしています。k=0は区間途中の非線形な制御更新により今回の抽出対象外です。[確定結果](chemistry_joint_product_verified.json)はこの限定クラスの結果で、より大きい再設計の最適性を示しません。

正確なFeMoCo参照データと実際の4033ローダーを照合し、7bit・6bit化、C44→43、列の直交回転を調べました。採用できる改善は得られませんでした。

4033ローダーについては、任意の初期wordに対する汎用XOR写像とは一致しない[独立native反例](chemistry_native_contract_k1.json)を確認しました。一方、実アルゴリズムの前後batch上では、[厳密な到達部分空間証明](chemistry_reachable_exact_proof.json)により全1220 address × 15回路 × 2方向、計36,600遷移が正しいことを確認しました。全40出力bitが一致し、selectionとscratchを復元、2230個のHMR変数の位相係数が恒等的に0、2230個のRの入力も0です。サンプリングではなく全測定分岐を扱うため、この部分空間での任意の重ね合わせと参照系への絡みを含む正しさを支持します。[独立監査](chemistry_reachable_exact_proof_audit.json)でも実KMBの配置・ゲート形式・hashと証明の前提を確認しました。

汎用XORへの拡張と、実際に到達する部分空間での正しさは別の命題です。[現公式pinと一致する契約資料](chemistry_current_contract_provenance.md)にはXORの式と、シミュレートされる語をロードする構成の自由の両方があるため、任意wordでの反例だけから実アルゴリズムの不正や提出不適合を断定していません。今回の証明は化学テンソル精度や競技採点結果を再検証するものではありません。

[前後batchの到達入力だけを使う線形span再合成](chemistry_context_span_resynthesis.json)でも、4033 CCXからの置換は0件でした。また、[5個の保存tagを使う構造の厳密解析](chemistry_loader_contract_and_resynthesis.md#exact-structure-of-the-target-dependence)では、batch 1〜14が各wordのbit 6 XOR bit 7を保持し、その5 tagの高々二次関数を出力に加えることを確認しました。[構造証明の全結果](chemistry_tag_dependency_analysis.json)を保存しています。これらは限定した手法の結果であり、別の非線形再合成を排除しません。

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
