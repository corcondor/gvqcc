# 作業線の載せ替えを伴う厳密XORローダー

化学の新候補は最大128量子ビットで15本のANGLEを構成し、片道4,323 Toffoli、化学全体15,308 Toffoli、427量子ビット。全1,220アドレスで任意の初期40ビットに対するXOR、選択レジスタ保存、作業領域のゼロ復帰、各HMRの全測定分岐の位相相殺をシリアライズ後のKMBで証明した。公式デフォルト検証は78,080ショットPASS。DQIとinvsqrtは前のアーカイブとバイト一致。

比較は同じW/H2_Iと同じ物理演算の、任意入力で証明済みの4語版。ローカル総合点 **26.1996042395 → 26.9745891652**、化学費用 **334,648,493.7597401 → 306,625,698.92914605**（8.374%減）。変更前の27.327844992は到達列に対するローカル値で、下記の任意入力XORに不一致がある。Kaggleには提出していない。

| 化学ローダー | 片道Toffoli | 最大ローダーQ | 化学費用 |
|---|---:|---:|---:|
| 旧4語、任意入出力XOR | 5,182 | 125 | 334,648,493.7597 |
| 2タグの出力補正 | 4,936 | 128 | 331,182,996.2173 |
| 2タグの出力補正と積のペア化 | 4,689 | 128 | 別記の検証結果を参照 |
| 2作業線の載せ替え、ビーム幅6 | 4,338 | 128 | 307,226,611.5871 |
| 2作業線の載せ替え、幅6と24のバッチ別最良 | **4,323** | **128** | **306,625,698.9291** |

## 作業線をどの順で入れ替えるか

元の5語版には前バッチの語ビットから得られる5つの既知値をアドレス関数として使う箇所がある。一般の語入力に対してはその5値を退避し、本来のアドレス積を計算してから処理する。すべての作業線に追加すると130量子ビットになるので、各時点で2つの特徴量を外す。

1. ANGLE中央部のCCXを、アフィン制御形式のペアと出力のXOR方向に変換する。中央部の制御を入口の特徴量で表現し、出力に作用する線形写像と定数項を分離する。
2. 作業線の値を全アドレスのビット集合で表し、他の線の積で再生成できる特徴量を求める。実回路では50種類の特徴量が該当し、外す2種類の組は1,225通り。各組が実行できる積と線形補正をビットマスクで記録する。
3. 組を頂点にしたグラフを構成する。共通に保持している線から、再生成・測定補正に必要な全制御が取れる場合に限って遷移できる。遷移費用は新たに生成する特徴量のCCX数。ビームの状態は現在の組と未処理項の集合。状態の重複を統合し、残り項の数と実際の再生成費用で順序を決める。
4. 訪れた組ごとに適用可能な項をまとめ、全ての値がある状態の中で既存のパリティ合成を再実行する。不要な特徴量はHMRと条件付きCZで消す。相手の回路を再現するクリーンな作業線だけで特徴量を作り、最後に語入力の退避を戻す。

初期版から幅を変えた結果をバッチ単位で照合し、Toffoliの少ない方を選んだ。新しい配列に対し全回路を再証明して公式検証をやり直した。バッチ数ごとの選択とハッシュは [selected.json](selected.json)、値・位相の証明は [final_proof.json](final_proof.json)、公式結果は [final_verifier.json](final_verifier.json)。

機械学習はこの候補の生成・採否に使用していない。探索でログを集めるなら、状態の特徴量と一定予算で完走できた最小再生成CCX数が教師候補となる。等価性の証明、正確な費用、Q上限は従来通り検査する。旧方式のCX削減を教師にした結果とは別の学習問題になる。

## 比較と反例

- [旧J4の同係数比較](../gemini/chemistry/verified_compliant_j4_score12.json)
- [2タグの残差を出力側でまとめる合成](../gemini/chemistry/repair_tag_oracle_unpaired.py) と [積のペア化](../gemini/chemistry/repair_tag_oracle.py)
- [score11とscore12に共通する任意入力の反例](../gemini/chemistry/arbitrary_tag_witness.json)。アドレス0で初期語ビットを一つ反転した実KMBの結果。以前のローダーで知られた制約を、今回のZIPのバイナリでも独立検出した。
- [スコア計算および18ファイルのSHA-256](score13_scorecard.json)

## 再現

Python 3.12、KickMix、NumPy、SciPyと公式の化学検証データを用いる。SOURCEはscore12の化学サブフォルダ、WORDSは同版の回路から回収した角度表。WORDの1220×75をuint8で連結したSHA-256は証明コードの定数に固定した。REPOは元のGVQCC実装で、SCHEDULERはリポジトリの `algorithm_rework/chemistry` へのパス。

```sh
python leaf_census.py "$SOURCE" > leaves.json
python feature_cache.py --source "$SOURCE" --output beam6 --repo "$REPO" \
  --scheduler "$SCHEDULER" --leaf-census leaves.json --beam 6
python feature_cache.py --source "$SOURCE" --output beam24 --repo "$REPO" \
  --scheduler "$SCHEDULER" --leaf-census leaves.json --beam 24
python select_cache.py --variants beam6 beam24 --out exact-family
python prove_cache.py exact-family "$WORDS" --out proof.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$VERIFIERS/dfthcsos/verify.py" exact-family
```
