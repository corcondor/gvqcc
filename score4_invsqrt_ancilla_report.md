# invsqrt 第4段階：保持値と測定 cleanup の寿命変更

## 採否

**提出済み `684106f1…` を超える invsqrt の追加削減候補は、この担当範囲では得られなかった。** 採用回路は `score3_invsqrt_cache.kmb`、Q46・static Toffoli-like 1550 のまま。既存回路、Z_POW の精度、入力や許容誤差は変更していない。新しい invsqrt 提出候補や公式全件検証は作成していない。

今回は既知の 1 件の cache や h0 packing を繰り返さず、次の実行可能な rewrite を実装して適用条件を調べた。

1. 保存先を途中で別の constant-0/1 wire へ移動する cache routing。
2. 後の積が保存値と affine 関数だけ異なる場合の再利用。
3. HMR とその位相補正をまとめて延期し、既に計算された値を次の CCX へ引き渡す再利用。
4. 内部測定を含む条件付き cleanup ブロック全体を、古典 bit の寿命と位相多項式を確認して延期する方法。

最後の方法は合成した陽性対照で **5 → 3 static Toffoli** の実 KMB を生成し、全有効 x の等式証明と native 検査を通した。この対照の位相は単純な三重積であり、**invsqrt の改善回路・提出用ファイルではない**。

## 実回路で完了した範囲

| ベースと変換 | 検査した範囲 | 結果 | 秒 |
|---|---|---|---:|
| 提出済み回路・等しい積の routing | 無条件 CCX 1279 個、連続する等積 558 pair | 可能な追加計画 0 | 3.33 |
| 同・affine 差分も許す cache | 開始可能 gate 774、18,040 pair | 512 合法入力の時点で式なし | 3.87 |
| 同・inline 位相補正の延期 | HMR cleanup 390 群、11,755 pair | affine 関係の時点で該当なし | 4.19 |
| 同・条件付き cleanup も延期 | HMR cleanup 978 群、19,969 pair | affine 関係の時点で該当なし | 3.91 |
| root の 415 件の Clifford-only HMR hoist 後・等積 routing | 558 pair | 可能な追加計画 0 | 3.81 |
| 同・affine 差分 cache | 開始可能 gate 792、18,538 pair | 512 合法入力の時点で式なし | 4.09 |

各実行は数秒で終了した。後半の HMR hoist ベースも Q46/T1550 のままなので、それ単独を score gain として数えていない。

元の source KMX SHA256 は `d431f212c7da02418429c2883dcdf4e3a90c9124ab2409c999efe0a5c7c037a8`。hoist 後は `e46fa7c2277065a42551ab3c6ed1d853fb516b0d74d010c4a275bab305c32af8`。後者は root 所有の `score4_hmr_hoist.py` が生成した同値な中間回路であり、この担当はそのバイトを変更していない。

### 陰性結果の意味

Affine 関係は、定数と現時点の wire 値の任意の XOR を対象とした。512 点はランダムな失敗率の推定ではなく、全合法入力集合の部分集合である。その部分集合ですでに線形方程式が解を持たない場合、調べた因子・切断点・保存計画について全入力上の解も存在しない。

保存先は、全 3,133,452 入力で既知の 0 または 1 である physical wire に限定した。元回路がその wire に触れる前に別の slot へ移り、条件付きブロック内では移動しない。dirty target 自身を affine 加算項に含める置換、任意の非線形な live 値の符号化、計算順序全体の変更は探索外である。したがって、一般的な回路最適性や「あと 1 Toffoli を減らせない」という下界は主張しない。

## 実装した位相を保つ変換

### Routing と affine 差分

保存する積を f、後の積を p、保持される他の wire の affine 関数を L とし、`p = f XOR L` を要求する。後の CCX の target には、cache からの CX と L の CX/X だけを適用できる。

最後に cache を HMR した場合、測定結果 m の位相は `(-1)^(m f)`。`f = p XOR L` なので、p に対応する条件付き CZ と L に対応する条件付き Z で返せる。L の定数項も条件付き global sign として正確に扱う。dirty target と cache を L の説明変数から除外し、補正中に式の値が変わることを防いだ。

holder hopping 自体は公開祖先の `src/tools/hold_pass.py` に既に存在する。新規手法として扱っていない。今回の適用は提出済み 684106 に対するもので、constant-1 slot と使用時点だけの operand 除外まで許可した。公開 `audit_pairs.py` にも affine 差分の検出は存在するが、公開 hold builder は差分が非零の pair を除外しているため、その出力・位相補正まで新しく実装した。

### HMR と cleanup の延期

HMR で捨てる値 f をその wire 上に残し、古い測定結果 m の全利用を確認する。古い m が再代入まで使われるのは、取り除く位相補正か取り除く条件付き cleanup ブロックだけでなければならない。

条件付きブロック内の HMR には独立な記号を与え、各位相項を「測定結果の monomial × 入力の Boolean 関数」として合算する。内部測定に依存する係数がすべて 0、残る補正述語が元の f と等しければ、元 HMR の符号と補正は各分岐で相殺する。内部 HMR が代入した古典 bit も、取り除く領域外で再代入前に読まれてはならない。

その cleanup を延期し、後の CCX target が保持していた wire なら、値を直接引き渡せる。別 target なら cache からの CX で使い、最後に上記の正確な HMR 補正を行う。測定結果を探索用の値に固定する変更ではなく、不要となった測定と、その結果だけに依存する全補正を一緒に取り除く変換である。

## 陽性対照

`score4_invsqrt_positive_control.kmx` は入力の下位 3 bit を a,b,c として位相 `(-1)^(abc)` を与え、入力を復元して scratch をすべて clean にする小回路である。abc を測定・cleanup した後に再計算する構成を用意した。cleanup 内にも測定が 1 個あり、その符号の相殺まで検査する。

変換器は abc の HMR と条件付き cleanup ブロックを延期し、同じ値を後の CCX target に渡した。**static Toffoli 5 → 3、期待 Toffoli 4.5 → 3、Q46 維持**。これは変換実装が正のケースを扱えることの確認であり、ベンチマークの gain には含めない。

- 全 x = 1..3,133,452 で、保持値・消費先・cleanup の位相係数を検査して一致。
- 内部測定の非定数 monomial 係数が正確に 0。
- native は 256 入力 × 2 seeds × 変換前後。関係する全 8 入力パターンを含み、入力復元・scratch・厳密な `(-1)^(abc)` との差分位相は全て 0。
- 対照の変換後 KMB SHA256: `2488cd304cf47d61b4c6aa2731fd9543bbe61da3f2fbedc63760edc3bd3febff`。

## 保存と再現

新規コードは `score4_invsqrt_cache_route.py`、`score4_invsqrt_affine_cache.py`、`score4_invsqrt_delay_reuse.py`、`score4_invsqrt_block_cleanup.py`。各 CLI は `--out` に新規ディレクトリを取り、必要なら `--source` と `--expected-sha256` で入力を明示する。既存の回路・既存の score1〜3 ファイルを変更していない。

```bash
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score4_invsqrt_delay_reuse.py --allow-blocks --out /tmp/score4_delay_reproduction
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score4_invsqrt_delay_reuse.py --allow-blocks --source score4_invsqrt_positive_control.kmx --expected-sha256 89b029be9d4922e8a3c1534c14fc7918b0989e8ead71612062bd66e936a89f43 --out /tmp/score4_control_reproduction
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score4_invsqrt_positive_control_check.py --candidate /tmp/score4_control_reproduction/candidate.kmb --out /tmp/score4_control_reproduction/native.json
```

実行時の JSON に記録された script SHA は当時の版として保持した。current manifest は、古典 bit が離れた cleanup ブロック間で再代入された場合の version 分離を加え、scope 文言を明確にした最終ソースを別に記録する。実回路の最後の陰性結果は位相証明より前の affine 関係の時点で出ているため、この補強で探索結果は変わらない。最終版の内部測定位相処理は上記陽性対照で確認した。稼働中の探索や検証プロセスはない。
