# invsqrt の測定補正を同時に合成する検査

対象は最高ローカル版 score12 と同じ KMB。
SHA-256 は `684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a`。
既存の公式費用は 78,673.55534364567（46Q、200,540,928 shots PASS）。

二つの測定で生じた符号位相を、GF(2) 上で扱う。測定結果を a, b、
測定前のデータ値を f(x), g(x) とすると、補正対象は a f(x) + b g(x)。
これを (a+b) g(x) + a (f(x)+g(x)) と書ける。したがって f+g が
残るワイヤの定数・一次・二次項で表せれば、高価な補正を一つ減らし、
その代わりに既存のもう一方の補正を古典 XOR で制御し、Z/CZ を適用できる。
測定結果は固定せず、各結果に対応する位相を代数的に保存する。

- 50 件の対象補正から、補正対と挿入の組を 3,675 通り検査した。
  4,095 合法入力で得た 8 件を全 3,133,452 入力で再検査し、すべて棄却。
- 近接した 34 対について、計 96 の切断点から一対につき最大 5 点を
  併用した。39 件の対象補正について元の補正位相と内部測定係数を
  全域で確認した。得られた式を全域と比較し、相違する合法入力を
  最大 256 件ずつ追加して再合成した。等価な式は 0 件だった。
- 最大 9 件の補正を同時に扱い、残りの補正の XOR と複数時点での
  Clifford 項から最初の補正を再現する 38 グループも調べた。
  全域で元の補正が確認できたものは 47 件。計 131 切断点、初期
  12,270 合法入力と反例の追加で、縮約候補は 0 件だった。

この結果は指定された条件スコープと切断点の範囲に限る。採点対象回路の
新しい KMB や公式検証結果は得られなかった。

## 再現

```sh
python highest_inv/measurement_basis.py --source "$KMB" --code "$REPO" --out highest_inv/measurement_basis.json
python highest_inv/measurement_two_cut.py --source "$KMB" --code "$REPO" --priors highest_inv/measurement_basis.json --out highest_inv/measurement_two_cut.json
python highest_inv/measurement_group.py --source "$KMB" --code "$REPO" --out highest_inv/measurement_group.json
```

`REPO` には既存の `score4_invsqrt_block_cleanup.py` が必要。
`graph_inv/temporal_phase_graph.py` を読み取り専用で利用した。
