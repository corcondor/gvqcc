# GVQCC：多方式7-bit ANGLE合成・比較実験（2026-11-23）

**判定:** 4種類の可逆X/CX/CCXローダー生成器を実装し、4つの実NPZの全15バンクで計240本の実ゲート列を生成・論理検証した。**新スコアなし、公式KickMix検証なし、公開3,357Tに届かない。**

## 何が違う4方式なのか

- `flat-minterm`：低4bitの16個のone-hotフラグを前計算し、高7bit一致フラグをブロックごとに逐次計算。個々のアドレスと5語35出力の関係を同じCCX積で制御する。**82Q**。
- `split-minterm`：高7bitを3+4bitに分け、それぞれ8個＋16個のフラグを前計算。高位の7bit比較を高位フラグ2本の積に置き換え、低位16フラグも共有する。**113Q**。
- `split-anf`：高位3+4bitフラグは維持。低4bitのBoolean ANFをMöbius変換で求め、単項式11個を可逆に一度だけ計算して5語35出力で共有。**100Q**。
- `split-basis`：各高位16行ブロックの(低位単項式×35出力)GF(2)係数行列を線形独立な出力マスクの基底に分解。低位Boolean形式を計算して各基底マスクを同時に更新し、各ブロックの非線形積を共有。**101Q**。

どの方式も選択アドレス11本、ターゲット40本（5語×8bit、うちタグ5本は不変）を使用し、遷移関数 `D_0=A_0`、`D_k=A_k XOR A_(k-1)` を正確に実装する。**前段を0に初期化すると仮定していない**。X/CX/CCXのみで構成し、全scratchをuncomputeするので相対位相を発生させない。真理値表は全有効アドレスで検証し、40ターゲットの任意初期値に対してXOR契約を満たす（ターゲットが制御として使われないことも検査）。

## 実測の総和（15バンク・片道）

| 構造 | 方法 | Q | CCX | CX |
|---|---|---:|---:|---:|
| C46 R9 B127 | flat-minterm | 82 | 51,150 | 320,340 |
| C46 R9 B127 | split-minterm | 113 | 40,680 | 320,340 |
| C46 R9 B127 | split-anf | 100 | 38,370 | 303,851 |
| C46 R9 B127 | split-basis | 101 | **38,010** | 301,176 |
| C45 R9 B130（元） | flat-minterm | 82 | 52,140 | 327,245 |
| C45 R9 B130（元） | split-minterm | 113 | 41,520 | 327,245 |
| C45 R9 B130（元） | split-anf | 100 | 38,850 | 324,288 |
| C45 R9 B130（元） | split-basis | 101 | **38,820** | 324,578 |
| C45 R9 B130（2ワード変更） | flat-minterm | 82 | 52,140 | 327,245 |
| C45 R9 B130（2ワード変更） | split-minterm | 113 | 41,520 | 327,245 |
| C45 R9 B130（2ワード変更） | split-anf | 100 | 38,850 | 324,292 |
| C45 R9 B130（2ワード変更） | split-basis | 101 | **38,820** | 324,582 |
| C45 R9 B129（Jacobi） | flat-minterm | 82 | 51,870 | 324,965 |
| C45 R9 B129（Jacobi） | split-minterm | 113 | 41,250 | 324,965 |
| C45 R9 B129（Jacobi） | split-anf | 100 | 38,850 | 324,452 |
| C45 R9 B129（Jacobi） | split-basis | 101 | **38,550** | 322,359 |

### 重要な陰性結果

以前の研究でC45/B130の2ワード変更により低位bit0の混合ANFランク合計が **1,121→1,117** に減った。しかし上の4種類の**実ゲート列ではCCX削減0**。基底分解を変えても物理回路で利益が出るとは限らないことを確認できた。

### Q・Tのトレードオフも見る

C46で**片道CCXだけ**を見るとsplit-basisが38,010で最良。ただし`Q_local × CCX`ならsplit-anfが3,837,000、split-basisが3,839,010で僅かに逆転する。split-mintermはQ=113のため、flatよりCCXが約2割減っても`Q_local × CCX`はむしろ増える。ただし**この積は公式化学コストではない**。化学全体のQピーク、Givens、状態準備、λ_eff、HMRは別途計測が必要。

## 実験データの蓄積方法

- `results/experiments.jsonl`：**append-only**、1行＝1構造×1方式×1バンク。実験IDは`SHA256(元NPZ SHA、方式名、バンク番号、生成器版)`、同じ入力を再実行しても重複挿入しない。各行にはCCX/CX/X、Q、対象アドレス数、検証結果、KMXサンプルのSHA（k0/k1）を記録。
- `results/comparisons.csv`：各種の15バンク費用、QとQ×CCXを横比較する表。
- `results/summary.json`：全比較の機械可読サマリー。
- `results/*k0.kmx`、`*k1.kmx`：実際に構成したKMXのサンプル。GitHubへ巨大な全回路のバイナリをコミットせず、**コードとSHAで再現可能**にする。

実験NPZのSHA：

- C46: `2ab7f2d01a02450eb2c47577097ef4bb27a1411b40ead88b6237f100bc9f4d61`
- C45 B130: `1c1f067ce2d2ed1d469ae3d245befecc99de83bae821eda5b6eb3fda4125f9e7`
- C45 B130 angle edit: `d4ce27280884d36a7bebc0e28a8e17026009a9adecfb6e5618eac23e01b14a87`
- C45 B129 Jacobi: `4e67df12c9a115121c42dabfe04becaa50217938e3f466777dc715efc9921307`

### 再実行

Python 3.11+、NumPy。元NPZはユーザー研究資料に保存（大きい外部データを再配布しない）。

```bash
python -m unittest -v research/test_multi_angle_synthesis.py
OPENBLAS_NUM_THREADS=1 python research/multi_angle_synthesis.py \
  --seeds /path/c46_public_v8.npz \
          /path/c45_B130_postangle_PSD_physical_pass.npz \
          /path/c45_B130_postangle_PSD_physical_pass_coupled_numeric_only.npz \
          /path/C45_B129_JACOBI_OPTIMIZED.npz \
  --out research/data/multiangle/2026-11-23
```

既存PR #18の[角度ワード＋FeMoCo研究](2026-11-23_joint_word_physics_notes.md)と連携するが、**新ANGLE合成器と物理重みの真の内側最適化は未完成**。今回の4種類は比較研究用の高コスト正解ベースラインである。

## 未検証・やらなかったこと

1. ネイティブKickMixの.kmbへの変換、競技の全状態・HMR位相および公式スコアテスト。純Pythonのビット並列XOR検証はそれを代替しない。
2. 128Q制約以外の全化学資源関数への統合。全体Q=405をそのまま仮定して費用を出していない。
3. R18 B127 C23は**2362選択アドレス**で11bit最大2048を超えるため本方式の対象外。12bitアドレスに変える場合、公式の選択・線数制約を確認する必要がある。
4. HMR測定消去、マトロイドパリティ、共通高位キャッシュと積の多出力時間再利用。公開3,357Tの要点をこの4方式だけで実装したとは言えない。