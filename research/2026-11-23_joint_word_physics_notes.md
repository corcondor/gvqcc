# GVQCC 結合探索の実装記録（2026-11-23）

**状態: 実装済み・実データ数値評価済み。新KMBなし、KickMix検証なし、新スコアなし。**

これは研究途中の証拠を保管するためのノート。以前の「同時最適化」と称した、固定ANGLE費用での条件付き計算を成功扱いしない。

関連ファイル:

- [実行コード](joint_word_feedback.py)
- [数理契約テスト](test_joint_word_feedback.py)
- [測定・ハッシュ原票](2026-11-23_joint_word_feedback_receipt.json)

## 1. 数学的に何を結合したか

パラメータはFeMoCoの (R,B,C,U,W,H2_I)、Givens木、量子化角度表、ANGLEローダー。今回は **R/B/Cが異なる2つの既存物理解**から出発し、量子化角度表・W/H2_I・15本の段間ローダーの低ビットBoolean構造を同じ候補で評価した。ただし J=5、7bit、固定Givens木、bit0の編集に制限している。

角度表をバッチ5語に区切り、段間のXOR更新量を

\[
D_0=A_0,\qquad D_k=A_k\oplus A_{k-1}\quad(k>0)
\]

とする。したがって Aの1ワードを変更すると **2個の隣接バンクの入出力関数が同時に変化**する。合成テストでこの差分が厳密に一致することを確認した。

Boolean構造の代理指標は、11bitアドレスの低4bitをANFに変換し、5出力語のbit0について、非定数低位モノミアル15個と高位アドレスから作るGF(2)行列 (75×H) の階数。Hは**完全な16行ブロックだけ**を数える。端数のアドレスをこの代理指標から除外するが、物理評価では全アドレスを使用する。

**GF(2)ランクはToffoli数ではない。** 高位キャッシュ、ANDの共有・実現可能性、線形出力、作業線、HMR位相の費用を含まない。比較のための構造スクリーニングに限る。

## 2. 角度表変更に伴うW/H2_Iの調整

実装には、変更した角度表からGivensを再構築してFeMoCo物理誤差を評価する処理と、任意指定のridge応答を入れた。影響を受けたrankについて

\[
\min_{W'}\|P_{\rm new}^{\mathsf T}W' - P_{\rm old}^{\mathsf T}W\|_F^2
+\alpha\|W'-W\|_F^2
\]

を解き、H2_Iを補正して D=H2_I-Σ_b W_b を保持する。これは **局所的な二電子チャネル保存の近似**であり、active-set/Newton制約付き最適化でも全パラメータ再学習でもない。変更後にe1/e2/Lambda/E_gapを再評価し、不合格候補を除外する。

離れた2つのバンクについて、2手目のランクを再計算して探索する（単独改善の足し算を仮定しない）。今回の2手目は追加のridgeを行っていない。

## 3. 実データ結果

### 公開V8・C46/R9/B127

- 3,375通りの低ビットをスクリーニングし、rank改善16通り、同点334、悪化3,025。
- 物理に進めた3通りに固定W/ridge応答の2種類を試し **6件中PASS 0件**。
- bit0の15バンク混合ランク合計 **382**。符号化された10バンクはランク1。
- 有限候補の陰性結果であり、このクラスの不可能性証明ではない。

### 既存物理PASSのC45/R9/B130

- 3,375通りの構造スクリーニング: rank改善566、同点2,137、悪化672。
- 30件の1ワード変更と24件の非隣接2ワード変更を評価し、**54件すべて独立物理PASS**。
- 最良の変更: 角度表の0始まりインデックス (row=700,col=41) と (row=700,col=54) のbit0を反転。段間の影響: slot 8,9と10,11。
- bit0混合ランク合計 **1,121 → 1,117**。これはコスト改善とは断定できない。

以前保存された公式のFeMoCo数値評価ソースで、物理メトリクスを独立に確認した:

| 数値 | 元のC45/B130 | 変更後 |
|---|---:|---:|
| e1 [mHa] | 19.274424 | 19.287094 |
| e2 [mHa] | 19.990366 | 19.990501 |
| Lambda | 304.413513 | 304.413461 |
| E_gap | 4.118917 | 4.118865 |
| lambda_eff | 49.90733793 | 49.90701906 |
| 物理制約 | PASS | PASS |
| 新しいKMB | なし | なし |
| KickMix位相・作業線 | 未検証 | 未検証 |

ベースC45/B130 NPZ SHA256:
1c1f067ce2d2ed1d469ae3d245befecc99de83bae821eda5b6eb3fda4125f9e7

変更後数値研究NPZ SHA256:
d4ce27280884d36a7bebc0e28a8e17026009a9adecfb6e5618eac23e01b14a87

参照 packed FeMoCo NPZ SHA256:
735282d9aa49bb3529e33e761ea501d1f796431221f684512de74d269b17562f

**解釈:** B130は物理条件を満たしていても、V8の符号化ビット構造を壊している可能性が高い。ランク1のバンクを多数持つV8(合計382)に比べ、B130は1,121。高位ブロック数も違うためToffoli数へ換算できないが、「C45は物理PASSだから3,357T級ローダーも安く作れる」という仮定を支持する証拠はない。

## 4. 再現の入口

使用した独立FeMoCo評価器とFeMoCo packedデータは、過去のユーザー提供研究ZIPにあり、ここでは再配布しない。Python3.11以降、NumPyとSciPyが必要。

    python -m unittest -v research/test_joint_word_feedback.py

    OPENBLAS_NUM_THREADS=1 python research/joint_word_feedback.py \
      --seeds /PATH/c46_public_v8.npz \
      --physical-module /PATH/physical_verify.py \
      --reference /PATH/chem_gpu_inputs.npz \
      --out runs/joint_c46 --top-rows 5 --per-slot 3 --ridge

    OPENBLAS_NUM_THREADS=1 python research/joint_word_feedback.py \
      --seeds /PATH/c45_B130_postangle_PSD_physical_pass.npz \
      --physical-module /PATH/physical_verify.py \
      --reference /PATH/chem_gpu_inputs.npz \
      --out runs/joint_c45 --top-rows 5 --per-slot 2 --beam-width 1

出力には全評価のJSONと研究NPZを保存する。ANGLE用の提出KMBは出力しない。別途、保存済み純Pythonの公式 scoreinfra に固定Hsym_lower/H1_Iを適用し、同じ数値物理制約がPASSであることを確認した。CPython3.12専用ネイティブKickMixの公式ショットテストはこの環境では実施していない。

## 5. 既存研究との相違と未完成部分

- [maoxin123原著](https://www.kaggle.com/code/maoxin123/qcc-33-17-3-357-toffoli-chemistry-loaders) は3,357Tの実KMBと説明文を提供するが、任意の新角度表を処理する合成器全ソースは非掲載。
- [manwithacat/vqcc-tools](https://github.com/manwithacat/vqcc-tools/tree/main/tools/dfthc-refit) の price_words.py、replan、chain.py は既に角度変更の物理価格付けと固定角度ローダー再計画を実装している。既存技法を独創と主張しない。
- 本実験の特徴は、前後の状態遷移2バンクに及ぶ1ワード変更を結合し、物理数値まで閉じた候補生成器を動かした点。**スコア上の差別化は未証明。**
- 未実装: **真のmulti-output XAG/KMB合成・HMR位相・128Q制約の検証**、任意のJ/brot/tree、R/B/C自動生成、制約付き大域重み再学習、公式Kaggle scoring。
- 次段で必要なのは、代理ランクではなく実KMBのゲート列・位相と物理精度を同じ評価器で計算すること。これがない限り期待スコアを断定しない。

**採用判定: 物理的に有効な新角度表を得たが、回路コストは未計測のため提出候補に昇格しない。**


## 6. 構成的な汎用KMX合成（追加実装・陰性結果）

[generic_angle_loader.py](generic_angle_loader.py) を新規実装した。こちらは代理ランクではなく、**具体的な可逆ゲート列 X/CX/CCX をKMXテキストへ出力**する（KMB化にはネイティブKickMixが必要）。

汎用J5/7bitローダーの構成: 11アドレス、5×8=40ターゲット（各語のタグを保持）、低4bitの16個の一致フラグ、高7bitの逐次一致フラグ、積の一時フラグ。合計 **82Q**、31本のscratch。各アドレスで前段との差分ワードのビットを dirty target にXORし、全CCXを可逆に戻す。使用ゲートがX/CX/CCXだけなので追加相対位相は恒等的に0。128Q制約内に入る。

計数の導出（1246有効アドレス、78高位ブロック、全行の差分ワードが非零）:

- 低位キャッシュの生成・逆算 = 48 CCX
- 高位一致判定の生成・逆算 = 12×78 = 936 CCX
- 各アドレスでのAND・逆算 = 2×1246 = 2,492 CCX
- **1バンク3,476 CCX。15本合計片道52,140 CCX。**

C45/B130の変更前・2ワード変更後をそれぞれ**全15本**コンパイルし、1246アドレスのビット並列実行、dirty targetの独立乱数初期値、タグ保存、scratchクリーンを検査した。すべてPASS。両方とも **52,140 CCX/片道で同数**。新しい表現で減った混合ANFランクは、この一般的なローダーではゲート数に反映しない。

**結論:** 新角度表から正しい可逆KMXを生成できることは実証したが、公開3357T/片道と比べて桁違いに高コスト。これはスコア改善ではない。なぜ高位キャッシュ・multi-output積共有・HMR消去・段間borrowが重要かを、具体的な費用差として可視化できた。次の課題は、この一般的な合成器の「アドレスごとに独立したAND」を、出力横断の共有積へ置き換えて実際に総CCXを下げること。

- 生成器の純Pythonテスト: [test_generic_angle_loader.py](test_generic_angle_loader.py)
- 計測原票: [2026-11-23_generic_loader_receipt.json](2026-11-23_generic_loader_receipt.json)
- 新KMBネイティブ検証・公式物理統合・Kaggleスコア: **未実施**
