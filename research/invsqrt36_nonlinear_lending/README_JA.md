# invsqrt 37Q → 36Q: 非線形レジスタ貸借・部分回路とLean証明

**競技提出用の完成36Q回路ではない。現時点の全体スコア増分は0。**

元回路: 公開37Q invsqrt, 60,766命令, 1,470 CCX, 1,278 HMR。固定 SHA-256:
`bb676b95f94c923cc5482f6cd8d457ab5ff3e8180c8f7cfd2c9678335d0ba56b`。
このソースをmain・旧候補へ上書きしないこと。

## 方法（ゲート2→1の局所置換ではない）

元命令341直前の**すべての2^22入力状態**で:

```
q22 = (!q19) & (!(q2 ^ q34))
q36 = 0
```

この関係を使って元のq22を1CCX＋Cliffordで**0に一時退避**し、元命令341〜400のq36をq22に再配置する。その区間はq22/q2/q19/q34を更新せず、最後のHMRによりguestを0へ戻すため、同じ1CCX＋Cliffordでq22を復元できる。出力レジスタ、計算状態、測定分岐の相対位相はこの区間の前後で保存される。

- 既存の36+1本すべてが線形独立になる場合でも、この関係は**二次**なので線形ランク検査からは見つからない。
- `outputs/invsqrt36_prefix_only_NOT_SUBMIT.kmb` は *命令0..414相当だけ* の36Q回路。後続60,351命令は含まない。
- `outputs/invsqrt37_first_lend.kmb` は全60,766命令を含むが、q36線を後続で使うので37Qのまま。+2CCXでコストは悪化。
- 将来の完成36Qはすべてのq36生存期間と残りの算術・精度・位相を再合成し、全入力・全測定分岐・誤差上限・価格を検証する必要がある。

## Leanで証明する命題

`lean/GVQCC36.lean` は公開KMBの実命令0..340から生成した可逆状態遷移と、実命令341..400に1 CCXずつ追加した変更後の測定命令を保持する。Lean 4.35.0 の `bv_decide` により:

1. `actual_reachable_invariant`: 入力22bitすべてで実KMBが二次の貸借前提を満たすこと。
2. `measured_lifetime_exact`: 任意の旧状態（前提が成立）・任意の入力位相・任意のHMR測定結果に対し、元・変更後の量子ビット値と相対位相が完全一致すること。
3. `measured_lifetime_cost`: 対象区間の追加CCXは正確に2個であること。

この形式化はKickMix全ゲートセット（特に任意角`Z_POW`）の一般的な量子意味論ではない。また、36Qへの全体縮約の証明ではない。

## 再現

元の37Q回路を `inputs/invsqrt.kmb` に置くか、環境変数 `GVQCC_INVSQRT_KMB` で指定する。

```bash
export GVQCC_INVSQRT_KMB=/absolute/path/to/invsqrt.kmb
python3 research/invsqrt36_nonlinear_lending/build_prefix36.py
python3 research/invsqrt36_nonlinear_lending/verify_prefix36.py
python3 research/invsqrt36_nonlinear_lending/generate_lean.py
cd research/invsqrt36_nonlinear_lending/lean
lake build
```

Python側は全2^22状態×4つの測定履歴で状態・位相を比較する（4通りで全測定トランスクリプトを列挙したという主張ではない）。Leanは対象測定の任意の1ビット結果を定理として量化する。

記録: `outputs/construction.json`, `outputs/prefix36_exact_verification.json`。SHA、分岐、入力範囲、全回路でない制限を出力する。

次の障害: 元KMB中にはq36が保持される長い区間（例926..7304、18557..26913、28912..43149）があり、同時に他の14作業線が変化する。単一の空き線借用をそのまま繰り返せないため、**中間値の維持・再計算と算術アルゴリズムの全体設計変更が必要**。2CCX局所削減への回帰は行わない。
