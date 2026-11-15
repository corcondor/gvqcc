# score10の照合、文献の適用判断、追加実験

score10の再現ZIPを読み、score6およびjoint-weightsの元ZIPから選んだ18ファイルすべてのSHA-256をスコア表と照合した。記録された課題費用から再計算した総合値は **27.32784439595798**。28を超えるために必要な費用積の削減は現状から **7.0301705%超**。課題の検証は元コンポーネントの記録に由来し、今回の再計算は新規の採点結果を含まない。[照合結果](score10_independent_receipt.json)

## Kaggleの採点条件

Kaggleの公式概要・採点節と主催者論文v2のKickMix、各課題と測定の節を確認した。総合値は基準費用に対する三課題の改善倍率の幾何平均。invsqrtは `Q × (Toffoli + T/4)`、DQIは `R(ε₊) × Q² × T`、化学は `λ_eff × T × Q`。invsqrtの一般角回転の価格には最悪入力の精度余裕も効く。化学の128量子ビット上限は各ANGLE回路に適用され、全体の費用は内部状態準備を含む。[Kaggle公式](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation)・[主催者論文v2](https://arxiv.org/html/2610.23832v2)

手元の検証器でDQI・化学のZ_POW拒否、化学の実回路からの角度復元を確認した。保存角度メタデータとの差だけを失格理由にはしない。HMRと古典条件付き補正を含む位相の等価性を検査する。KaggleのData・Rulesは直接取得で本文が表示されず、2026-10-28の転記まで照合した。[転記](https://github.com/M4-on-Github/Quantum_Circuits/blob/main/competition.md#rules)

## 指定4リンクと引用文献

| 一次資料 | 確認した範囲 | 今回の回路への含意 |
|---|---|---|
| [Zhang & Zhang、Shallow Magic Depth](https://arxiv.org/html/2409.13809v2) | 指定のCCZ図と論文本体は同一論文。v2の61件を文献ごとに照合。通読・主本文・選択節・プレビューを台帳に記載 | Fig.3は7T/T†で、(b)は4補助量子ビットでT-depth 1。native CCZと同じ位相を生成するがinvsqrtの価格は1→1.75。DQIと化学はZ_POW不可。加法誤差での古典推定はコヒーレントな回路の実装費用を与えない |
| [Shen & Zhong、The resource cost of magic in a code block](https://arxiv.org/html/2608.29438v2) | 指定の表1と本文。v2の53件のうち累積45件の抽出全文、残る8件は関連箇所 | 論文の定理は符号化論理測定、受理確率、回復構造を仮定する。HMRの分岐ごとの位相補正の検算には使える。引用[15]の4T状態CCZは単純換算で既存CCZと同じ1相当 |
| [Jiang et al.、Atomic-Scale Imaging](https://arxiv.org/abs/2609.39986) | 主本文と全56文献。1–28は主本文23件と抽出全文5件、29–56は抄録と主結果・議論・結論を照合 | ヘリカル三層グラフェンの格子緩和、約1.9度の平坦バンド、境界状態の実験。回路のゲート数を減らす手法は確認できなかった |

一次資料の版で数えると計170件（論文間の重複を含む）。本文の取得と精読は分けて記録した。参考文献の全件・全段落を通読したとはしていない。

- Shallow Magic Depth [1–31](literature/shallow_magic_refs_01_31.md)・[32–61](literature/shallow_magic_depth_refs_32_61_ja.md)
- Resource cost of magic [1–53](literature/resource_magic_53_ja.md)
- グラフェン [1–28](literature/graphene_refs_01_28.md)・[29–56](literature/graphene_29_56.md)

## 現行回路に対する追加実験

- **CCZのパリティ位相化**。score10と同じinvsqrtバイナリへ再コンパイルできるソースの条件付き53区間を対象にした。独立入口値で三次となる42分岐はClifford+Tのパリティ位相に最低7 Tを要し、元のCCZは1 Toffoli相当。別の12分岐は四次以上、1分岐は位相が消える。対象はこのゲートクラスと区間に限る。[コード](invsqrt/cubic_phase_t_bound.py)・[記録](invsqrt/cubic_phase_t_bound.json)
- **位相の次数**。閉じた10区間についてはさらに、全3,133,452合法入力から求めた入口値のアフィン包の上で、既存のToffoli系ゲート数を k とすると位相次数はすべて k+2。区間を保ち、アフィン包上で厳密な整数半回転位相を求める範囲では既存の k が下限になる。[詳細](invsqrt/phase_degree_report_ja.md)
- **保持ビットq45**。以前の二次式に加え、1～2本のパリティと任意二次式の積に任意二次式を足す形を、既存候補の5切断点で検査した。合法入力4,096件で4,313のパリティ候補を調べ、合致0件。2測定seedで全46線の保存値をネイティブ再生し、食い違い0。より一般の三次式・切断点に関する結果ではない。[探索](invsqrt/q45_factored_cubic_width2.json)・[再生](invsqrt/q45_native_receipt.json)
- **化学の多段積置換**。実4030ローダーの17区間・2,915 CCXで、混合行列の階数2以下のペア和を繰り返す置換を検査。閉包で553,128組を調べ、出力方向を消せるものは0件。人工例では3積から2積への置換を検出した。[詳細](chemistry/score11_j5_report.md)

- **DQIの逆元位相部品**。GF(4096)で2個の末端積をパリティ制御CCZとして実装し、内部作業量子ビットを12→11へ削減。27 Toffoli系ゲートを維持し、旧回路・新回路と固定・可変マスクの4構成、計65,536ショットで比較した。実score10 DQIにも固定マスク版の厳密な命令型一致が100箇所あり、54箇所で元回路がq888を使う。別の計算区間もq888を使うため、この部品だけで全体Q889を下げられない。[部品結果](dqi/phase11/result.json)・[実回路照合](dqi/phase11/production_binding.json)

q45検査の再現には、score10の `invsqrt.kmb` をKickMixで `accepted.kmx` へ書き出す。上の2つのJSONは既存保存値の再生と幅2の探索の結果。保存値はシードを固定して以下で再生成できる。

```sh
python invsqrt/replay_q45_snapshots.py --inputs invsqrt/q45_inputs.json --kmx accepted.kmx --write-snapshot snapshots.json --out replay.json
python invsqrt/q45_factored_cubic.py --snapshot snapshots.json --kmx accepted.kmx --factor-width 2 --out cubic.json
```

現在の候補の費用を下げた新規回路はない。今回確かめた置換範囲を打ち切り、基準値はscore10のローカル再計算値とする。
