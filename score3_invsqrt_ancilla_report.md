# invsqrt: CCX−1、Q46 維持、公式全域検証 PASS

## 採用結果

**公式 verifier の全 200,540,928 shots に合格した。** `score3_invsqrt_full_verification.json` が最終 receipt で、検証した circuit SHA は下記の凍結候補と一致する。

`score3_invsqrt_cache.kmb` は baseline `invsqrt_e46d90c36d1b.kmb` から、**無条件 CCX を 1 個削除した実回路**である。量子ビット数は 46 のまま、static Toffoli-like は **1551 → 1550**。元の全回転命令、元の全測定命令とその条件は保持した。新しい HMR とその条件付き CZ を各 1 個、CX を 3 個追加する。総命令数の増分は 4。

- baseline KMB SHA256: `e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6`
- candidate KMB SHA256: `684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a`
- candidate KMX SHA256: `d431f212c7da02418429c2883dcdf4e3a90c9124ab2409c999efe0a5c7c037a8`

| 項目 | original baseline | 公式合格した採用回路 |
|---|---:|---:|
| Q | 46 | 46 |
| Static Toffoli-like | 1551 | 1550 |
| measured mean Toffoli | 1479.7500405453395 | 1478.7506100300882 |
| effective T | 1711.2941118988529 | 1710.2946813836015 |
| 公式 verifier cost | 78719.52914734723 | 78673.55534364567 |

元の測定結果の分布を変えず、無条件ゲートを 1 個省くため、**期待 Toffoli 数は正確に 1 減る**。`Q × effective_T` に対する期待コスト差は 46。今回の有限ショットで観測した mean Toffoli の減少は **0.9994305152513**、cost の減少は **45.97380370156（0.05840203%）**。追加 HMR により乱数ストリームの対応が変わるため、有限標本の差と期待値の厳密な差は分けて扱う。

公式検証の範囲は x = 1..3,133,452、各 x につき default 64 shots。最大 error/tolerance は **0.9986660009092673、x = 159** で元回路と同じ。回転数は 33、rotation epsilon は 6.003064377662461e-13。検証時間は 321.751 秒。ここに示した cost は公式ローカル verifier の値であり、Public Score の結果はこの receipt の範囲に含まれない。

## 実際の変更と coherent な証明

元 KMX の line 3316 にある `HMR q21 b61` が q21 を clean にする。q21 はその後、今回の 2 回目の積の直後まで、位相命令を含むどの元命令にも参照されない。元 line 3322 と 3424 はともに `CCX q10 q11 q13` である。中間回路は q10 と q11 を X/CX で一時的に変更するが、2 回目の CCX の入口では両方を恒等に戻す。

初回を次に置換する。

```text
CX q13 q21
CCX q10 q11 q13
CX q13 q21
```

dirty な q13 の初期値を t、積を f = q10·q11 とすると、q13 は元どおり t XOR f、q21 は f になる。元の中間命令はすべてそのまま実行する。2 回目を次に置換する。

```text
CX q21 q13
HMR q21 b387
CZ q10 q11 if b387
```

2 回目の control の積は保存した f と等しいので、CX は元 CCX と同じ更新を行う。新しい測定結果を m とすると HMR の符号は `(-1)^(m f)`、条件付き CZ の符号も `(-1)^(m f)` であり、積は +1。q21 も clean に戻る。元の全測定には元と同じ値が入る。各元測定分岐と、新しい m の両方について coherent に同値である。

この局所証明は、到達可能入力の経験則に依存しない。独立チェッカー `score3_invsqrt_cache_proof.py` は、元 HMR による clean 条件、全元命令からの cache 未参照、q10/q11 の任意状態に対する恒等復帰を構文的に検査する。非線形 target を保守的に unknown とする affine 追跡でも両 control の恒等性が残る。追加の仮定はない。

## 検証と探索範囲

| 検査 | 結果と範囲 |
|---|---|
| 全有効入力の値 | x = 1..3,133,452。各元命令の後、使用中の cache 以外の全 wire が等しい。区間の外では cache も等しい。PASS。 |
| 独立した構文・位相証明 | 上記局所 coherent identity、全元分岐と新規 m=0/1、回転列の byte 同一性。PASS。 |
| native Kickmix 比較 | 2,081 種の有効入力 × 2 seeds。candidate の入力復元不良、dirty scratch、baseline との差分位相は全て 0。 |
| whole official verifier | **PASS、200,540,928 shots**。全 3,133,452 入力 × default 64 shots。`score3_invsqrt_full_verification.json` に候補・verifier・Kickmix binary の SHA と結果を保存。 |

今回の積 cache profile は、全無条件・条件スタック深さ 0 の CCX 1280 個を対象とした。全有効入力上で 721 種の積、497 個の重複した非零積グループがあり、**clean かつ全元命令から未参照の wire をそのまま使える計画は上の 1 件だけ**だった。同じ profile 内に直ちに合成できる追加の disjoint cache はない。これはその条件での探索結果であり、一般的な回路最適性の主張ではない。

値を全命令位置で比較する確認まで含む builder の所要時間は 141.57 秒だった。builder による hash grouping は候補抽出だけに使い、採用候補の積の一致は全真理値そのものを比較して検証した。

## 再現

repo を cwd とし、Kickmix を含む Python で実行する。出力先は未作成の新しいディレクトリを指定する。

```bash
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score3_invsqrt_product_cache.py --out /tmp/score3_cache_reproduction
python3 score3_invsqrt_cache_proof.py --candidate /tmp/score3_cache_reproduction/candidate.kmx --out /tmp/score3_cache_reproduction/formal.json
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score3_invsqrt_h0_native_check.py --candidate /tmp/score3_cache_reproduction/candidate.kmb --out /tmp/score3_cache_reproduction/native.json
```

先行する profile/formal/native receipt は当時の run 記録として改変せず保持しており、そこにある official 未実行や `score_improvement_claimed: false` は当時の検証範囲を示す。最終の公式合格と cost は `score3_invsqrt_full_verification.json` を参照する。採用 candidate の識別は SHA256 で行う。`score3_invsqrt_ancilla_manifest.json` に新成果と read-only 依存の hash を保存している。

## 付録：不採用の局所幅削減と 2 積の合成

先に構築した h0 packing は、original line 1636–3428 の q0 を空け、全有効入力と全新規測定分岐で復元を証明できた。しかし +2 CCX が必要で、残る 3120 個の full-live 位置を解消できず、whole Q46 は変わらない。**採用候補には h0 packing を一切含めていない。** この区間内で重複する積は 3 グループあり、どれも 2 回ずつしか現れず、packing 単独の費用を回収できない。局所幅の証拠は別ファイルとして保存した。

また、隣接する 2 個の CCX の間に無条件 X/CX/SWAP しかなく、同じ dirty target 方向に累積する 6 窓を profile した。2 窓は既存 phase 探索と重なるので除き、残る 4 窓を既存 one-AND solver で新たに検査した。各 512 個の実到達入力に対し、左因子を single/pair parity と既存 flag-parity 拡張、右因子と affine remainder を全 live wire の任意線形結合とした族は全件陰性（6.48 秒）。全入力で成立する式なら部分集合にも成立するため、この限定族の排除として有効だが、一般の AND 複雑性の下界とはしない。

