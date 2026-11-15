# ANGLEのアフィン制御付き再生成
最新版では準備・消去順序も合成し、片道4,237 CCX、ローカル27.07638103に改善した。公式78,080ショットPASS。詳細は [最新版と再現手順](closure_reproduce.md)。

各バッチの特徴量生成部を解析し、作業ビットに一時的なXORが入った状態で生成された積を、元の作業ビットのアフィン形式で記録した。再生成時は選んだ2本をCXとXで制御形式に変換し、CCXを1回実行してから戻す。消去では同じ制御形式でHMRの位相を条件付きCZで打ち消してから戻す。すべての再生成式を1,220アドレス上で照合した。

論理タグを初期省略する場合、元の任意出力ビットをその物理線に残し、作業用のタグ値だけを必要に応じて計算する。この初期化方式とアフィン制御により、候補の省略組を1,485→3,081、終了と両立する組を415→876に広げた。グラフのビーム探索はC++で実行し、全出口への最短費用を使って枝刈りした。今回のバイナリはビーム探索で得た結果であり、最適性の証明は含まない。

| 指標 | 従来 | 今回 |
|---|---:|---:|
| 片道のANGLE CCX | 4,268 | **4,241** |
| 化学全体のToffoli相当 | 15,198 | **15,144** |
| 化学全体の量子ビット | 427 | 427 |
| 化学費用 | 304,422,352.5166685 | **303,340,709.7323613** |
| ローカル総合点 | 27.03951162825614 | **27.071612384511887** |

第1〜14バッチがすべて改善した。15回路すべてについて、全1,220アドレスと任意の初期40ビットに対するXOR、選択ビットの保存、補助作業ビットの復帰、全HMR分岐での位相相殺を証明した。公式の化学検証器は78,080ショットPASS。DQIとinvsqrtは検証済みの旧ファイルとバイト一致。ZIPを再読出しして全18ファイルのハッシュを検査し、総合点を再計算した。Kaggleには未提出。公式化学検証器が記録した入力ダイジェストは `993ea4c499b01a57f27bf604ef2274eca30cfe8ff034d151b86f2de04c11d0c5`。

## 再現

`SOURCE` はタグ拡張の入力に使った4,030 CCXの15本、`INCUMBENT` はそのタグ拡張で合成した4,268 CCXの採用回路。 `REPO`、`SCHEDULER`、`EXACT`、`VERIFIERS` は既存の厳密XOR合成と同じ。 `WORDS` は `outcome_v27_actual_words_uint8.npy`。

```sh
g++ -O3 -std=c++20 search_routes.cpp -o search_routes
python affine_cache.py --source "$SOURCE" --output first --repo "$REPO" \
  --scheduler "$SCHEDULER" --incumbent "$INCUMBENT/cache_receipt.json" \
  --beam 80 --weight 24 --batches 1 2 3 4
for config in 96:23 160:35 180:60; do
  beam=${config%:*}
  weight=${config#*:}
  python affine_cache.py --source "$SOURCE" --output "beam${beam}x${weight}" \
    --repo "$REPO" --scheduler "$SCHEDULER" \
    --incumbent "$INCUMBENT/cache_receipt.json" --beam "$beam" --weight "$weight"
done
python choose_family.py --incumbent "$INCUMBENT" \
  --variants first beam96x23 beam160x35 beam180x60 --out family
python "$EXACT/prove_cache.py" family "$WORDS" --out full_proof.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$VERIFIERS/dfthcsos/verify.py" \
  family > official_verify.json
```

成果物は `family/cache_receipt.json`、`full_proof.json`、`official_verify.json`。選択はバッチ単位の最少CCXで、同点なら指定された順を使う。

## その他の検査

- [タグを保存するアドレス置換](address_scan/README.md)。混合ランク指標は改善しなかった。
- [invsqrtの新しい再合成検査](invsqrt/README.md)。採点回路の置換は0件。
- [DQIの疎ANFによる検査](dqi/sparse_anf.json)。現在の制限付きモデルで採点対象ゲートの置換は0件。
