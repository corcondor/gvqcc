# score11 化学係数の再最適化

ローカル総合点は **27.32784439595798 → 27.327844644007193**（+2.4804921e-7）。化学費用は 294887890.976471 → **294887882.9465613**。score10に使った角度回路を固定し、WとH2_Iを近接SQPで再最適化した。化学は変更していない検証器で78,080ショットPASS、Q427、総Toffoli14722、ANGLE 4030/pass。化学の数値誤差とギャップは公式閾値に近く、検証結果の実数値を添付した。DQIとinvsqrtの費用はバイト同一のscore10の記録を使用。総合点はその3費用から再計算し、Kaggleには未提出。

- [全18メンバーと費用](score11_scorecard.json)
- [公式化学検証結果](chemistry_full_verifier.json)
- [化学メンバーと差分](chemistry_receipt.json)
- [最適化の診断](optimizer_receipt.json)

ZIPは18ファイル。score10に対して変更は dfthcsos/submission.npz のみ。NPZの変更はWとH2_Iのみ。他17ファイルのSHA-256と、化学の公式submission digestを組立時に再検算した。ZIP SHA-256は `99f1abbececfd07a453767b8e03e8bae0df54c1bec318c1af9d8f9f66101ffb1`。候補NPZはZIPから取得できる。

最適化器は、実回路復元角度語を持つ開始NPZを引数 `--start` に取り、公式参照データを `GVQCC_VERIFIERS_ROOT` から読み込む。開始SHA-256、角度語のSHA-256は chemistry_receipt.json に記載。stage_candidate.py は最適化結果の2配列だけで基準NPZを更新する。package_candidate.py は元のscore6とjoint-weightsのZIP、[score10照合記録](../score10_followup/score10_independent_receipt.json)、検証済み化学ディレクトリと検証結果から完全ZIPを組む。
