# 実821回路の共通制御・二次位相簡約スキャン

## 結果

**今回の限定探索では、新しく削減できるCCZは0個だった。** 元821回路の全7000 CCZについて、条件や測定を跨がずにまとめられる区間を調べた。共通制御が見つかる区間は既に必要なrankに達しており、残る区間の部分集合まで調べても改善はなかった。検証済みe986候補、worker、KMBは変更していない。

対象SHA-256は既存profileに固定された以下の値。今回ハッシュの再計算は行っていない。

```text
821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3
```

関連する研究手法の説明は[research_anthropic_chemistry.md](research_anthropic_chemistry.md)。今回の処理は実回路への独立した代数スキャンであり、研究の再検索は行っていない。

## 探索範囲

同じ暗黙の古典条件の下で、`NEG/Z/X/CZ/CX/SWAP/CCZ`のみからなる区間を扱った。`PUSH/POP_CONDITION`、明示的な古典条件付き命令、古典bit更新、測定、reset、`CCX/CSWAP`、未知の命令を境界とした。したがって境界内の条件値は変わらない。

各区間は最初のCCZから最後のCCZまでを対象とし、最大4096命令・64量子ビットに制限した。実際に複数CCZを持つ区間は最大145命令・25量子ビットで、上限による除外は0だった。KMBのmmapとコンパクトなopcode indexを使い、巨大なKickmix Circuitへ展開していない。

| 区間内CCZ数 | 区間数 | 判定 |
|---:|---:|---|
| 1 | 6814 | 複数ゲート簡約の対象外 |
| 9 | 18 | 区間全体にも、費用を減らせる部分集合にも共通制御簡約なし |
| 12 | 2 | 共通制御あり、二次形式のrankから12 CCZ必要で現状と同数 |

合計は`6814 + 18×9 + 2×12 = 7000`。静的ゲート数の議論であり、条件付き実行の平均費用とは区別する。

## 計算と証明

区間入口の各bitを独立な変数とし、X/CNOT/SWAPを可逆なaffine写像として追跡した。すべてのZ/CZ/CCZによる符号を、Boolean環`GF(2)[x]/(x_i²−x_i)`のANFへ展開した。入力に関する仮定や、途中のbitが0という仮定は使っていない。

三次部分`F`が`g q(x)`と書ける場合、二次形式`q`のpolar行列をGF(2)で簡約する。rankが`2r`なら、CNOTの座標変換、`r`個のCCZ、低次数のZ/CZでその位相を実装できる。ここでの費用の最小性は、この共通制御・線形変換の枠組みに限る。

物理bitをそのまま共通制御にできない場合も、全ての線形な候補を線形方程式で調べた。最高次数の三次ANFはalternating 3-formとして変換するので、共通線形因子`L`の必要十分条件は`L ∧ F = 0`。そのkernelを求め、必要ならCNOTで`L`を1本のwireへ移した形へ変換した。affine制御の定数項は次数2以下へ吸収できるので、三次部分の因子条件は同じになる。

候補生成時の証明は、元区間と置換区間の**全affine出力写像と全位相ANFの係数一致**で行う。したがって計算基底入力の部分サンプルだけでなく、区間入口の任意の重ね合わせに対する局所等価性を扱う。条件がfalseの場合は区間全体が恒等操作である。

### 共通q886制御の2区間

| 開始op | 終端op（含まない） | 元CCZ | polar rank | 簡約後CCZ |
|---:|---:|---:|---:|---:|
| 23,712,726 | 23,712,738 | 12 | 24 | 12 |
| 34,836,164 | 34,836,176 | 12 | 24 | 12 |

どちらも25量子ビット、12命令の区間。共通制御はq886で、残り24変数の二次形式がfull rankである。

### 9 CCZを持つ18区間

各区間は145命令・22量子ビット。CNOTを入口変数へ展開すると三次項が81個あり、`L ∧ F = 0`のkernel次元は0だった。よって区間全体を単一の共通制御付き二次形式にすることはできない。

区間全体で因子を持たなくても部分集合が簡約できる可能性があるため、9個のCCZから2〜9個を選ぶ全502通りを各区間で調べた。選んだゲートだけの位相を入口へ移し、部分集合ごとの因子とrankを計算した。

| 部分集合探索 | 結果 |
|---|---:|
| 調べた部分集合 | 9036 = 18 × 502 |
| 共通線形因子なし | 8820 |
| 共通線形因子あり | 216 |
| 因子ありのうちCCZ数が減るもの | 0 |

比較相手は展開後の81個等の単項式数ではなく、**元回路で選んだCCZ数**。展開した式を小さくできても、元の回路に勝てないものは改善に数えていない。

## 実装自体の確認

合成規則について、`2→1`、`3→0`、Xによる符号補正を含む`2→0`、隠れた線形制御の`3→1`の4例を用いた。独立なbitシミュレーションで条件on/offを含む160ケースの状態と位相が一致した。

また5変数の全非ゼロ三次ANF1023個と全非ゼロ線形候補31個、計31,713通りについて、`L ∧ F`のkernel判定とCNOTに相当する直接代入の結果が一致した。

最終の全区間走査は約0.995秒・peak RSS121.60 MiB、部分集合探索は約4.943秒・120.36 MiB。5分・約1GBの計算上限内で完了した。候補が0件なので、新たな全回路シミュレーションやKaggle提出は行っていない。

## 再現

- [dqi_quadratic_phase_scan.py](dqi_quadratic_phase_scan.py): 区間分割、affine/位相追跡、共通線形因子、rank簡約、代数証明。
- [dqi_quadratic_phase_scan_original821.json](dqi_quadratic_phase_scan_original821.json): 全7000 CCZの区間結果と自己検証。
- [dqi_quadratic_phase_subset_scan.py](dqi_quadratic_phase_subset_scan.py): 18区間の全部分集合に対する限定探索。
- [dqi_quadratic_phase_subsets_original821.json](dqi_quadratic_phase_subsets_original821.json): 部分集合探索結果。

```bash
python gvqcc_repo/dqi_quadratic_phase_scan.py \
  dqi_inputs/821bf8d157c0.kmb \
  --profile dqi_inputs/audit_actual_821/profile.json \
  --report gvqcc_repo/dqi_quadratic_phase_scan_original821.json \
  --seconds 270

python gvqcc_repo/dqi_quadratic_phase_subset_scan.py \
  dqi_inputs/821bf8d157c0.kmb \
  --profile dqi_inputs/audit_actual_821/profile.json \
  --whole-report gvqcc_repo/dqi_quadratic_phase_scan_original821.json \
  --report gvqcc_repo/dqi_quadratic_phase_subsets_original821.json \
  --seconds 90
```

この結果は、測定を跨ぐ修正、非線形な変数変換、複数制御を共同で扱う一般的な三次tensorの再合成、異なる補助レジスタ設計まで不可能とする証明ではない。今回の安全な小区間・共通制御簡約には追加の削減余地を見つけられなかった、という限定した結論である。
