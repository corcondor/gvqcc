# public4030 の W / H2_I 同時再フィット

## 今回の新規結果

public4030 の**実回路から復元した整数角度表**を固定し、W と H2_I を同時に最適化した。角度・Givens 木・配列の形状を変えていないので、既存4030ローダーをそのまま使う候補である。公式の変更していない `evaluate_dfthc_angle_words` で新しい係数配列を再評価し、全ての数値条件を満たした。

| 比較対象 | lambda_eff | 同じ T=14722, Q=427 での chemistry cost |
|---|---:|---:|
| 元の public4030 | 46.909726478631555 | 294888332.1042627 |
| 前回検証済み H2_I のみの候補 | 46.90967164973765 | 294887987.4337159 |
| **今回の W / H2_I 同時候補** | **46.90965630568201** | **294887890.9764710** |

元の public4030 に対して 0.0001495915%、前回の H2_I 候補に対して **0.0000327098%** の費用低下。前回候補からの絶対低下は約96.4572。小さな改善であり、大幅な順位上昇やKaggle最高値更新を達成したとは主張しない。

## 公式数値評価

- error_1 = 0.01999999900017499 Ha（上限0.020）
- error_2 = 0.01999999900000842 Ha（上限0.020）
- E_gap = 3.9148980009995284 Ha（厳密下限3.914898）
- Lambda = 283.0012787701885（下限49）
- lambda_eff = 46.90965630568201
- gap_in_domain = true

誤差の評価は最適化中の残差差分式だけでなく、最後に公式関数のテンソル評価で再確認した。さらに、最終NPZとbyte同一の15本のpublic4030ローダーに対し、変更していない公式verifierのデフォルト **78,080ショット検証を実行してPASS** した。結果は `chem_next_public4030_full_verifier.json`、実行条件と公式ソースのハッシュは `qcc_next_verification_provenance.json` に保存した。

## 実装

`chem_next_public4030_prox.py` は絶対値をsoft thresholdで扱う近接SQPを使用する。近零固有値を持つ3次元Schur補行列を保ち、符号反転による勾配の不連続を抑える。最初の180秒の探索に続き、固定したチェックポイントから90秒の探索を実行した。後半は誤差境界を0.019999999、gapを3.914898001とし、公式制約は変更していない。`chem_next_fixed_angles.py` は既存の高速数値モデルを数式変更なしで同梱した。

公式モジュールの所在が異なる環境では `GVQCC_VERIFIERS_ROOT` を設定する。FCIDUMPは公式関数がサイズ128128348 bytes、SHA256 `e5a48af746fd075026dec9e8f5df2d363802a121e8c53af9a0b984bde695e1bd` と照合する。

## 候補の適用

- `chem_next_public4030_weights.npz`: W / H2_I の2配列だけを含むパッチ。
- `chem_next_apply_public4030_patch.py`: 元のpublic4030 NPZをSHA256で固定し、2配列だけを差し替える。ソースZIPからの取り出しにも対応。回路・その他の配列を変えない。
- `chem_next_public4030_receipt.json`: 候補・2配列のハッシュ、数値結果、検証範囲。

```bash
python chem_next_apply_public4030_patch.py \
  --source /path/to/public4030/submission.zip \
  --weights chem_next_public4030_weights.npz \
  --out /path/to/new/submission.npz
```

原public NPZのSHA256は `4df35abdeec320a3f1c10f6f533e73550e50bb45d95e666deaa01062810a3559`。実回路角度表のuint8 SHA256は `8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea`。元NPZの保存角度メタデータは実回路と473語違うため、物理評価は実回路の表を使った。適用器は元NPZの他の配列を保持し、公式の回路復元に従う。

パッチSHA256: `ce9a087668d181478044fd800dc24588b21c9270d522d4fac4742f780075789d`。
最終提出NPZ SHA256: `df226db938dc440a37391091fba46c90ebcd14acfda88ec84939361ebcf9a955`。
最適化用の中間candidate NPZは `56214fd2151569758bf8fc3572c69d3258f030180a5f44b73217157b1d3e75f6` であるが、提出用には元NPZの他配列を厳密保持した前者を使う。

`qcc_next_build_submission.py` は元v27の18ファイル全てをハッシュ照合し、この2配列のパッチを適用して完全な提出ZIPを生成する。最終ZIPでは、DQI・invsqrt・15ローダーの17ファイルは元v27とbyte同一である。

## 同時に実計算した負の結果

`chem_next_regroup_resources.py` は、C列の分割とrho群のブロック対角合流、およびゼロpaddingによる、Hamiltonianを厳密に保てる594設定を公式コストモデルで調べた。固定ローダー数を仮定した比較では、元のR8/B143/C44が最小だった。C列を2分割してR16/C22にした場合でもTは同じでQは427→428となる。新しい任意ローダー合成の下限や、不可能性の証明ではない。

モデルは `Inzainos/quantum-circuit-compilation@4277c767440df9efb8a90860ae2ce47028e46ba9/verifiers/dfthcsos/scoreinfra/costs_prepare.py` を変更せずに使用。再グループ化からは候補回路を生成していない。

## 未実施

この実験からのKaggle提出は0回。新しいPublic Scoreは未計測。既存のH2_I候補の検証・提出状態は今回の新規成果に数えていない。
