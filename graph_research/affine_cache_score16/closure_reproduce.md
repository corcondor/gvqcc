# 準備・消去順序の合成

従来の準備命令列と消去命令列は、補助作業ビットを省略できる始点と終点を制限していた。候補の2本を除き、選択ビットから再生成式を適用して残りの全特徴量を準備できるか調べた。その順序を逆にたどれば、HMRと条件付きCZで同じ特徴量を消去できる。準備と消去に使える状態はCCX一回で生成する式の依存先の閉包で決まる。

各再生成式には、元の制御式に加えて「2本のXOR」と「1本の否定」を片側の制御に使う積も探索した。積の真理値を1,220アドレスで一致させ、既に存在する再生成式の依存先を含む候補を省いた。開始と終了に使える省略組は各876→1,717→2,837と増えた。

採用回路は第5・8・11・12バッチのCCXをそれぞれ1減らした。片道合計は4,241→4,237、化学全体では15,144→15,136 Toffoli相当。全15回路について全1,220アドレスと任意の初期40ビットでのXORと位相を検証した。

公式検証器で78,080ショットPASS。化学費用303,180,466.35690844。DQIとinvsqrtの従前の検証済みKMBを組み合わせた結果、ローカル総合点は27.07638103220335。Kaggleへの提出は行っていない。

## 再現

`SOURCE`、`REPO`、`SCHEDULER`、`EXACT`、`VERIFIERS`、`WORDS` の意味は README と同じ。README の手順により `family` と `search_routes` を先に生成する。

```sh
python closure_cache.py --source "$SOURCE" --output closure_first --repo "$REPO" \
  --scheduler "$SCHEDULER" --incumbent family/cache_receipt.json \
  --beam 160 --weight 35 --batches 1 3 6 12
python closure_cache.py --source "$SOURCE" --output closure180x60 --repo "$REPO" \
  --scheduler "$SCHEDULER" --incumbent family/cache_receipt.json \
  --beam 180 --weight 60
python factored_cache.py --source "$SOURCE" --output factored96x23 --repo "$REPO" \
  --scheduler "$SCHEDULER" --incumbent family/cache_receipt.json \
  --beam 96 --weight 23
python choose_family.py --incumbent family \
  --variants closure_first closure180x60 factored96x23 --out family_closure
python "$EXACT/prove_cache.py" family_closure "$WORDS" --out closure_proof.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$VERIFIERS/dfthcsos/verify.py" \
  family_closure > closure_official.json
```

`family_closure/cache_receipt.json` が採用したバッチとハッシュの内訳。
