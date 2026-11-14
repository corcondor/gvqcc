# ANGLE の疎差分を、タグ・正逆動作・位相を保存して実装

## 最終統合結果：公式 78,080 ショット PASS

paired-tail の20 word変更を、Clifford再合成済みの最終 familyへ統合した。変更しない13本は元のSWAP符号化のまま保持し、loader3と4だけ差し替えた。**公式 verifier が全78,080ショットで受理し、SHAで結び付けた比較対象よりコストが低下した。**

| 指標 | 同じ入力NPZに結び付いた比較対象 | 最終候補 |
|---|---:|---:|
| 公式コスト | 294,988,786.87084424 | **294,988,052.12610483** |
| lambda_eff | 46.90658950862355 | **46.906472675810164** |
| 総Toffoli | 14,728 | 14,728 |
| 総量子ビット | 427 | 427 |
| ANGLE CCX / pass | 4,033 | 4,033 |
| ANGLE最大Q | 128 | 128 |
| 操作数 | 410,454 | **408,788** |
| 検証ショット | 78,080 | 78,080 |

コスト差は734.7447394132614、約**0.00024907548%**。最終誤差は error_1=0.01999998000005401、error_2=0.0199999936269957。元の未縮約611,422 opsとの比較では202,634 ops減ったが、スコアの比較対象は表に示した公式receiptのfamilyである。

最終回路は `/workspace/scratch/3815fb5fae06/score2_best_family/`、公式receiptは `/workspace/scratch/3815fb5fae06/score2_best_family_verified/verification.json`。小さい証明・receiptはrepo内の `score2_angle_best_family_exact.json` と `score2_angle_best_family_official.json` に同一内容を保存した。

これは検証済みのmatched local improvementである。ユーザーの別記録 lambda=46.905894137 よりは低くなく、Kaggle送信・公開スコア測定は行っていない。

## 今回できたこと

元の 15 本、片道 4033 CCX、最大 128 量子ビットの ANGLE family に対して、角度整数表の変更を反映するパッチャーを作った。元ファイルは変更していない。

通常の疎 XOR は 11 ビットのアドレス一致を 10 CCX で計算し、同じアドレスの全出力変更へ共有する。既存の feature を利用する方法では、有効アドレス 0..1219 上で同じ差分を 1〜2 CCX/loader に下げられた。さらに、既存 feature の線形空間に入る差分なら **追加 CCX は 0** である。単なるコスト見積りではなく、新しい KMB family と全アドレス・正逆・全測定枝の証明を保存した。

具体例として、アドレス 48..63、角度列 45 の LSB XOR を loader 9 と 10 に無料の線形処理だけで入れた。15 本の合計は 4033 CCX/pass、往復 8066、最大 Q128 のまま。実体は `/workspace/scratch/3815fb5fae06/score2_angle_zero_gain_family/`。その `package.json` が公式評価用 NPZ `candidate_numeric.npz` を指定する。

**この角度変更が数値改善の原因だとは結論していない。** 数値担当の対照実験では、同じ H2_I 再調整を使い角度を元に戻しても同じ lambda と精度条件を満たした。従ってその小さな数値改善は H2_I 再調整に帰属させる。ここで実証した成果は、整数角度の追加探索を 0 CCX でも実回路化できる一般機構である。公開スコア改善やユーザーの別の低い lambda 記録を超えたとは主張しない。

### 続いて得られた paired-tail 候補

その後、アドレス 0..15 と 1216..1219、角度列19 の LSB XOR、計20 wordを変更する候補も作成した。この関数は不足 high0 と high76 の二点指示の XOR なので、high の唯一の parity 制約を満たして無料で作れる。loader 3 と4への追加は **0 CCX**。

元4033 familyと、root が完成させた ZX round2 family の両方へ組み込んだ。後者の納品用 directory は `/workspace/scratch/3815fb5fae06/score2_angle_paired_tail_zx_family/`、評価用 NPZ は同 directory の `candidate_numeric.npz`。NPZ SHA256 は `5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357`。

ZX 元回路の 408,394 ops を、SWAP を3 CXに等価展開して409,228 opsにし、238 個の X/CXを追加した。候補は409,466 ops、4033 CCX/pass、最大Q128。全15本の正逆・位相と公式recover2seed、保存roundtripが通った。`package.json` と `proof.json` に元ZX・展開・パッチの hash を記録した。

数値担当による matched control では、この20 wordを同じW/H2_Iのまま元へ戻すと lambda は46.906571024915195、変更後は46.906472675810164だった。両者とも精度条件を満たすが、今回は角度変更による追加低下が観測された。これは、最初の one-body のみの16-word例とは異なる。二体側の角度から得るUが補正後一体行列にも影響するので、lambdaを一般にW/H2_Iだけの関数と扱ってはいけない。

対照記録は `/workspace/scratch/3815fb5fae06/score2_chemistry_paired_tail_revert/restore_check.json`。数値候補との統合公式 full-shot 評価も、冒頭のとおりPASSした。ここでの個別 loader 証明や公式ローカルコストを、未実行の公開スコアやユーザーの別記録への優越と読み替えない。

## ABI と、単純な終端 XOR が危険な理由

対象は R8、B143、C44、N76、brot8、J5。selection は q0..q10、5 個の 8 ビット word は q11..q50。残りは各ローダーの前後でゼロに戻る workspace である。loader 0 は Q128、loader 1..14 は元々 Q125。

公式 `recover_words_from_circuits` は、全 1220 アドレスについて同じ回路を順方向と逆方向で使う。loader k は前 batch と現 batch の間を行き来する。元の loader 1..14 は、各 word の bit6 XOR bit7 に

\[
(a_0a_1,\;a_0a_2,\;a_1a_2,\;a_0a_3,\;a_1a_3)
\]

を保存して計算に利用する。従って元回路を任意の 40 ビット target に対する汎用 XOR oracle とみなしてはならない。元の証明範囲は到達する前・現 batch の部分空間である。

タグを保存する差分は、batch 差分を差分化して loader k と k+1 に配る。最終 batch の変更は loader 14 のみ。最適化した差分回路を受理する前に、新表の前・現 batch を入力した両方向を必ず厳密に検査する。

## 任意の単一 word 変更：二点を対応させる可逆変換

タグを変える変更では、単純な pre/post XOR の正逆対称性を仮定しない。あるアドレスにおける元の前・現 batch を x,y、新しいものを x',y' とする。d=x XOR y、d'=x' XOR y'、w=d XOR d'、t=x' XOR x と置く。

d,d' が非ゼロなら、l(d)=l(d')=1 となる線形汎関数 l を選べる。共通の 1 ビットがあればその 1 ビット、なければ両側から 1 ビットずつを XOR して選ぶ。すると l(w)=0 であり、

\[
D(v)=v\oplus w\,[l(v)\oplus l(x')]\oplus t
\]

は可逆で、D(x')=x、D(y')=y。元の F を

\[
F'=D^{-1}FD
\]

に置き換えると、**同じ F' が新しい前・現 batch の両方向に正しい**。各 D はアドレスに条件付けた shear と translation で、通常 11 CCX。D^-1 は二つの順序を逆にする。境界で使用する scratch は q51..q62 の 12 本以内で、Q128 を増やさない。

元表の全 15×1220 遷移で、前・現 batch が異なる word 数の最小値は 2 以上だった。従って任意の一つの word を 0..255 の別の値に変えても、二点の衝突は起きない。`--force-conjugation` はこの一般構成を使う。複数変更で衝突が起きる場合は明示的に拒否し、誤った回路を保存しない。

単発タグ変更の実例 63→64 では、通常の 2 loader 合計が片道 +44 CCX、公式往復 +88 Toffoli。最終 batch だけなら半分になる。これはこの構成のコストであり、大域下界ではない。

## 測定 uncompute と共有アドレス述語

11 ビット一致の各中間 AND を CCX で作る。出力へ CX で fanout した後、中間値を逆順に HMR し、測定結果に条件付けた CZ で位相を打ち消す。AND の二つの入力を補正時に維持するので、uncompute に追加 CCX は不要である。

複数アドレスは prefix trie で共有する。深さ 1 の literal は無料、それ以降の各 prefix が 1 CCX。prefix の集合は選択したビット集合だけで決まるため、2^11 個の部分集合に対する動的計画で、11! 通りの**一つの共通変数順序を使う trie** の最小コストを求める。任意の Boolean 回路全体に対する最小性は主張しない。検証例では 8 アドレスを独立に実装する 80 CCX に対し、共有 trie は 37 CCX だった。

独立実装 `score2_angle_sparse_check.py` は、量子値を「全 2048 アドレスの真理値表 × 任意の 40 入力 target ビットに対する affine 係数 41 個」で追跡する。両因子が未知 target に依存する積は拒否する。HMR 結果を形式変数として追跡し、上書き前と終了時に全位相係数がゼロであることを確認した。

この独立検査は単一述語、多アドレス共有、一般の二点 adapter、逆 adapter、および両者の合成について PASS。**単独パッチでは全 2048 アドレス × 全 2^40 target × 全測定枝**が対象である。元 ANGLE family に対する証明範囲は別途、1220 の有効アドレスと指定された前・現 batch に限る。

## 既存 feature を使った 1〜2 CCX と 0 CCX の差分

loader 1..14 の出力積蓄積直前には 90 本の制御線がある。定数 1 を加えた関数空間の次元は 91。35 本の DATA 入力への依存が制御側から消えることも記号的に確認した。

h=a>>4、l=a&15 とすると、有効アドレス上でこの空間は

\[
V=\{A(h)\oplus B(l)\}
\]

と表せる。high-only の次元は **76/77**、low-only は **16/16**。共通の定数を引けば 76+16−1=91 と一致する。A には次の 44 個の high 値上で XOR 和がゼロという一つの制約がある。

`0,5,6,7,13,14,15,16,17,19,21,22,23,24,28,30,32,33,34,35,36,39,41,43,44,45,46,48,49,51,52,55,57,58,66,67,68,70,71,72,73,74,75,76`

この集合に入らない high の一点指示関数は、既存線の affine 結合だけで作れる。low の一点指示は全 16 点で無料なので、両者の積を出力に加える 1 CCX でアドレス差分になる。

不足集合に入る high h には、同集合の異なる j,k を使い、

\[
\delta_h=(\delta_h\oplus\delta_j)(\delta_h\oplus\delta_k)
\]

を使う。右辺の二因子は高側の制約を満たすので無料の affine 結合。high 指示を 1 CCX で q125 に準備し、無料の low 指示と掛けて出力へ 1 CCX、high helper は HMR/CZ で消去する。従ってこの構成では 2 CCX、該当 loader は Q126、family の最大 Q128 は変わらない。

複数出力は既存 DATA target を基準とする CX fanout の共役で共有し、最終積専用の helper は不要である。二つの制御 affine form は可逆な座標変換で準備し、先に準備した制御を二番目の target に選ばない。出力の方向は、挿入位置から終端までの線形処理を逆に伝播して求める。非線形制御、reset、位相制御へ差分が入る場合は拒否する。

さらに、出力関数を独立な方向へ分解し、V に入る成分は直接 X/CX だけで挿入する。これにより次を実回路化した。

| 変更 | 追加往復 Toffoli | 検証 |
|---|---:|---|
| high1 の単一 word、通常の 2 loader | 4 | 全 family PASS |
| high0 の単一 word、通常の 2 loader | 8 | 全 family PASS |
| high1 の単一 word、最終 batch | 2 | 全 family PASS |
| 同じアドレス・batch の 2 word | 4 | 出力共有、全 family PASS |
| 無料 high1 の 16 アドレスへ同一 LSB XOR | **0** | 全 family PASS |
| 不足 high0 の 16 アドレスと high76 の末尾4アドレスへ同一 LSB XOR | **0** | 全 family PASS |
| high76 の4アドレスのみ、通常の 2 loader | 4 | high AND 共有、全 family PASS |

この 1〜2 CCX は実装済みの上界である。有効アドレスの端部をさらに利用する特殊化、既存の積の係数変更、より一般的な積共有を排除する下界ではない。

## 検証と保存

各 family は `chemistry_reachable_exact_proof.prove_one` で 15×2×1220 = **36,600 遷移**を全数確認する。40 出力ビット、selection 復元、全 workspace のゼロ、R の入力ゼロ、全 HMR 形式変数の位相係数消去を確認する。さらに変更後の整数表を、変更前と同じ公式 `recover_words_from_circuits` で全 1220 アドレス・正逆・2 seed に対して回収する。

KMB を保存した後に再読込し、証明した gate 列と register 情報が完全一致することを確認する。NPZ の全配列も再読込して dtype と値を確認する。**追加 CCX がゼロでも変更された回路は必ず保存する。** 初期の診断出力ではこの保存条件を修正したため、納品に使うのは `score2_angle_verified/` と `score2_angle_zero_gain_family/` のみ。`score2_angle_trials/` は納品用ではない。

元表 SHA256 は `809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5`。各元・候補 KMB と実行時スクリプトの SHA は個別 `proof.json` に記録する。過去の証明記録は、その実行時版の SHA のまま保存する。

数値担当の単発候補 a322/col73 と a38/col21 については、元 feature に既存出力積を全て加えた空間で無料に表せるかも厳密に判定した。k14 は次元279、k4/k5 は各280で、該当の一点指示はいずれも非所属だった。これは指定した辞書内の判定であり、別の 0 CCX 構成全体を排除する主張ではない。

## 再現

`kickmix` を含む native Python を使う。`changes.json` は `[{"address":48,"column":45,"value":253,"old":252}, ...]` の形式。`value` の代わりに整数 `delta` も指定できる。

```bash
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score2_angle_sparse_patch.py \
  --changes changes.json --feature-patches --out /path/to/new_family
```

pure NumPy だけでコストを確認する場合は `--estimate-only --feature-patches` を使う。未知の元回路への一般的なコスト保証ではなく、ビルダーが再検査する元 4033 family の feature profile に対する見積りである。

```bash
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score2_angle_sparse_check.py \
  --report /path/to/new_standalone_proof.json
```

主な成果物は `score2_angle_sparse_patch.py`、`score2_angle_feature_patch.py`、`score2_angle_sparse_check.py`。証明記録と依存ファイルの SHA は `score2_angle_manifest.json` にまとめた。
