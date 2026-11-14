# スコア改善の追加検証 — 採用可能な改善は未達

## 結果

今回の追加実験から、公式の数値条件を満たす低コスト提出物は得られなかった。化学の低い `lambda_eff`、DQI の局所的な補助ビット解放、逆平方根の合成探索を、確認済みのスコア改善として扱わない。失格した NPZ や未統合の回路を提出物へ混ぜていない。

並行作業で保存され、main のコミット `5b3f06b88b9d6c4a33e65ae93bd166caf6e18ff0` に記録された Public スコアは **27.27654**、従来の最高値は **27.30683**。この作業では画面を直接操作して確認しておらず、[共有の完了記録](https://github.com/corcondor/gvqcc/blob/5b3f06b88b9d6c4a33e65ae93bd166caf6e18ff0/results/2026-11-15/kaggle_v2_submission_complete.json)を参照した。追加の1失敗による DQI ペナルティという説明は数値と整合するが、サーバー側の課題別結果が開示されたという意味ではない。

ユーザーの最新ログによると、外部 task 1031 は `lambda_eff≈46.708, error_2≈20.029 mHa` で終了し、続く角度・重みの交互最適化 task 1046 は `changed_words=0, lambda_eff=44.16992, error_1=19.997 mHa, error_2=20.105 mHa` に到達した。いずれもその時点では精度条件を満たしていない。外部 task 1051 は、丸め後の `words0` に厳密固定した再ポリッシュとして報告されている。

これらの実配列は、この作業環境では見つからなかった。外部の task 1051 を完了済みとは扱わない。次の具体的な入力は、**task 1051 が実際に保存した最終 NPZ** である。`changed_words=0` だけでは、連続角度で計算した誤差や `lambda_eff` が、丸め後の角度から再構成する公式評価でも同じになるとは限らない。また固定角度の局所探索の失敗は、固定角度で改善が不可能であることを証明しない。

## 1. 化学：固定角度の連続最適化

使用した検証済み基準は `submission_asterios_full.npz`、SHA-256 `809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5`。基準の `lambda_eff` は `46.906589508623554`。ユーザーが別に報告した `46.905894137` の元配列は未入手なので、両者を同じ提出物とはみなさない。

角度表は `1220 × 75`、**91,500個の8bit word**。ビット数は732,000である。今回保存した13個の C44 endpoint では、全 word と Givens tree が元の表と一致した。したがって既存の15ローダーを再利用でき、資源数は `T_total=14728, Q_total=427` のままである。ただし数値誤差の失格を、この一致で回避することはできない。

| 項目 | 最終 C44 候補 | 条件 |
|---|---:|---|
| `lambda_eff` | 46.90582747479046 | 低下したが精度失格 |
| `error_1` | 19.999860527 mHa | 20 mHa 以下 |
| `error_2` | **20.003194680 mHa** | **上限を3.194680 µHa超過** |
| `Lambda` | 282.9512727865309 | 49より大きい |
| `E_gap` | 3.914955937947525 Ha | 3.914898より厳密に大きい |

精度を満たした修復点も得られたが、その `lambda_eff` は47.22以上となり、基準より高コストだった。未採用候補について新たな全回路検証や公開提出はしていない。

実装上の成果は、評価式の縮約と最適化の条件改善である。

- `d = H2_I − sum_b W` と `c_rb = sum_c W_rbc d_rc` を使い、352個の行列を毎回展開せずに一体ハミルトニアンを計算する。評価時間は同じ環境で約4.1〜4.5倍短縮した。量子回路スコアの改善ではない。
- `(W,d)` 座標と Cholesky whitening を導入し、勾配を独立に照合した。
- 固有値絶対値の非微分点に対し `sqrt(e²+δ²)` を使うと、76固有値の合計誤差は最大 `76δ`。その余裕をギャップ制約へ加え、最終判定は平滑化なしで行う。
- Hungarian 対応付けの切り替わりで約2.314 µHaの不連続を実測した。微分検査を通すだけでは、その境界をまたぐ探索の正当性は保証されない。

詳細と全記録は [score_chemistry_report.md](score_chemistry_report.md)、独立レビューは [score_independent_review.json](score_independent_review.json) に保存した。

## 2. C43：局所探索と理論上の下限を区別

`C=44 → 43` は他の資源条件を固定すると Toffoli を14728から14650へ減らす。しかし、whitening 後に収束した局所探索の二体誤差は **21.121775 mHa**、一体誤差も31.533886 mHaで不合格だった。

一方、二体テンソルを対称ペア空間へ等長に写すと、任意の実 SOS は半正定値かつ rank が `R*C` 以下になる。元の構造制約を緩めた最良 rank 制限 PSD 近似の誤差は

\[
\sqrt{\sum_{\mu_i<0}\mu_i^2+\sum_{\text{捨てる正固有値}}\mu_i^2}
\]

以上である。この必要条件による C43 の下限は **8.168351 mHa**。20 mHaを下回るので、**C43の不可能性は証明していない**。逆に、緩和問題で小さい値が出ても、量子化された共有ベクトルを使う元の構造で達成できることは証明されない。これは残差を検査したfloat64計算であり、区間演算による厳密数値証明でもない。

記録は [score_chemistry_c43_whiten_converged.json](score_chemistry_c43_whiten_converged.json) と [score_chemistry_rank_bound.json](score_chemistry_rank_bound.json)。C43探索後に `tree_edges` 一致のガードを追加したため、実行時の旧ソースハッシュと最終ソースハッシュを区別して保存している。既存の実験入力がこのガードを満たしていたことは独立に再確認した。

## 3. DQI：生存期間の短縮は局所で確認

HMR で Boolean 関数 `f` を消すと、測定結果 `m` に応じて位相 `(-1)^(mf)` が残る。この位相を既存の逆向きゼロ判定へ移すため、前向きフラグの差分と古典測定ビットの suffix XOR を使う方式を実装した。

限定した controller では、17段のうち16段で前向き演算中のフラグを保持せずに済み、静的 Toffoli は増えなかった。4181個の許可されたフラグ列を3種の測定乱数系列で照合し、入力復元・位相・作業ビットを確認した。ただし実際のGF演算全体を含むデコーダを新たに生成したわけではない。

フラグと重なるGF24 consuming演算の候補箇所は66から34へ減る。しかしノルム逆元計算等の別のピークが残り、**889量子ビットを888へ削減したとは言えない**。必要な23補助ビット版の演算器もまだ得ていない。34箇所へ各24 Toffoliを足す仮定なら816となり、1量子ビット削減の約861 Toffoliの予算内だが、これは設計予算であって達成値ではない。

約4948万命令の記号実行、既知の0/1を追跡する約5938万命令の別検査、CCX再相殺も実施し、採用できる追加Toffoli削減は0だった。個別探索が陰性という範囲の結果であり、大域最適性の主張ではない。詳細は [score_ancilla_report.md](score_ancilla_report.md)。

## 4. 逆平方根：有限到達領域での再合成

検査対象は46量子ビットの既存回路。全入力 `x=1..3133452` の到達関係を使い、補助ビットの早期解放、位相修復、2出力のAND共有を調べた。小さな入力サンプルだけでは成立して見えた45量子ビットへの affine 縮約は、小さい入力を追加すると破れたため採用していない。

局所の2出力を復元する既存回路は5 ANDを使う。現在の6入力で到達する47パターンについて、最初のANDの651商クラスと、最初の2 ANDの1,524,950クラスを全列挙した。未解決の低rankケースは0で、独立レビューで列挙と全3,133,452入力の表抽出を再実行した。**この6入力・47パターン・2出力のXOR/AND直線回路という範囲では、4 AND以下への削減は不可能で、既存の5 ANDが最小**という有限の結論が得られた。

隣の root bit `q17` を使う7入力への拡張では、固定first gateの族は陰性、一般の列挙は60秒で385/2667 first classまで進んで打ち切った。この7入力問題は未解決であり、6入力の下界を拡張しない。これは回路全体の最適性や、測定を使う全構成に対する最小性の証明でもない。

詳細は [score_invsqrt_report.md](score_invsqrt_report.md) と [score_invsqrt_joint_enum_review.json](score_invsqrt_joint_enum_review.json)。この一連の作業から新たな提出回路は生成していない。

## 5. 外部 task 1051 の候補を取り込む手順

[score_dfthcsos_fixed_words_verify.py](score_dfthcsos_fixed_words_verify.py) は、完全な基準 NPZ の `W` と `H2_I` だけを置き換える。候補が角度表や tree を含む場合は完全一致を必須とし、元の15ローダー、元の公式 verifier、標準の全検査を使う。任意の比較値と、ハッシュで結び付けられた検証済み基準を区別する。

```bash
python score_dfthcsos_fixed_words_verify.py \
  --candidate FINAL_TASK1051.npz \
  --baseline ../dqi_inputs/chemistry_4033/submission_asterios_full.npz \
  --loaders ../dqi_inputs/chemistry_4033 \
  --verifier ../official_sources/Inzainos/verifiers/dfthcsos/verify.py \
  --engine-dir ../kickmix_venv/lib/python3.12/site-packages \
  --baseline-portfolio-receipt results/2026-11-14/submission_v2_full_reconstruction.json \
  --out-dir /tmp/gvqcc_task1051_full_check
```

出力先は未作成のディレクトリを使う。公式 verifier が返る前に PASS としない。公開提出も自動では行わない。今回このラッパーはコードレビューまでで、未入手の候補に対する実行結果は存在しない。

## 文献との対応

- Meuli et al., [The Role of Multiplicative Complexity in Compiling Low T-count Oracle Circuits](https://arxiv.org/abs/1908.01609), 2019。XOR/AND回路のAND数と量子オラクル合成を対応付ける研究。今回の有限Boolean再合成の根拠となるが、論文の一般構成だけで対象のAND削減を保証するものではない。
- Khattar et al., [Leveraging verifiable structure in quantum circuits to find more efficient compilations with agentic AI](https://arxiv.org/html/2610.23832v1), 2026。対象ベンチマーク、HMRの位相、古典入力による検証の前提を確認した。
- 先行する [PR #5](https://github.com/corcondor/gvqcc/pull/5) のテンソル縮約・QROM研究を継続した。今回の変更は同PRのコミットを基礎に置く。先行の約990万CNOT削減も、今回の古典評価高速化も、それぞれ単独でToffoli・量子ビットを課金するスコアの改善を意味しない。

## 保存と再現の範囲

`score_continuation_manifest.json` は、この追加作業が所有するファイルだけを列挙する。並行作業のREADMEや `score_loss_*` は変更しない。大きいJSONは決定的gzipで保存し、解凍後の元バイト列とハッシュをmanifestへ記録する。実行パス、公式データ、Kickmixと科学計算の依存関係は各実験のmanifestに記載した。失格NPZや再生成可能な実行バイナリはこの成果物に含めない。
