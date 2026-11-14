# 整数角度更新へ進むためのデータ探索と資源条件

2026-11-15（日本時間）のユーザー更新に対応する記録。

## ユーザー側の新しい実験ログ

`test_alt_rounded.py` / task-1051の途中経過は、旧angle_words固定での
`(error_2 mHa, lambda_eff)` が `(20.548,45.270)`、`(20.236,45.833)`、
`(20.084,46.417)`。連続角度では44.17との報告がある。
これらはユーザーが共有したログであり、この環境で再現した実配列の結果ではない。
固定表での回復傾向は前回の独立再計算と整合するが、大域最適性の証明にはしない。

## 実ファイルの探索

対象は `dfthcsos_brot8_polished.npz`、`polish_dfthcsos_brot8.py`、
`opt_dfthcsos_joint.py`、`test_alt_rounded.py`、`alt_cont`、`precomputed.npz`。

- GitHub: corcondor/gvqccの7ブランチ、全履歴とPR refを含む18 commit trees、
  8 Actions artifactsを検査。artifact ZIPは実取得・SHA照合・内容確認済み。
  対象は見つからず、artifactsは旧算術ツールの3 JSONのみ。所有repo横断の名前検索も補完した。
- Google Drive: 名前・本文検索に加え、root、Downloads、ChatGPT、CodexUploads、
  Colab Notebooksなど8フォルダ447項目のメタデータを確認。対象は見つからなかった。
  この接続の検索が一部バイナリを返さないことを確認しているため、Drive全体での不存在とは言わない。
- 保存済みファイル: 最近200項目（11月10日以降を含む）と対象名を確認。
  ユーザーが以前アップロードした `gvqcc_dqi_opt.py` は存在し、内容はDQI worker v4だった。
  同ファイルの既存ローカルコピーは4147 bytes、SHA256
  `ce18eda70b1d84e03b4555e44b74973759bbb03f52c6c3a33e9a28aab77ac460`。
  生成済み `gvqcc_dqi_tools.zip` は51メンバーで、対象化学ファイルは含まない。
- Kaggle: Your Workのgvqcc検索は3ノートブック、dfthc検索は0件。
  元 `geocpuresearch/gvqcc-dqi-optimizer` の最終成功v12は出力0ファイル、
  最新v13 (`scriptVersionId=369597582`) は失敗runで、出力は `dqi.kmb.xz` 1個だけ。
  他2ノートブックは既知の96CCX/480CCX版で、今回の化学ポリッシュではない。
- 指定されたWindows作業フォルダは共有Linuxにマウントされていない。
  ブラウザからのfile://アクセスはURL security policyが明示拒否した。
  この拒否を迂回していない。Windows内にファイルが存在しないと判断したものではない。

最新の連続角度・重みは取得できていない。以降の独立実験は、既存の公開基準NPZ
SHA256 `809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5`
を出発点とし、外部WSL taskの継続や結果回収とは扱わない。

## 4033という固定上限を採択条件にしない

基準T=14728には2回のloader総数4033が含まれ、他の部分は6662。
形状、brot=8、Q=427、他の回路費用を維持する場合の改善条件は

\[
\lambda_{\rm new}(6662+2L_{\rm new})
<46.90658950862355\times14728.
\]

整数角度から公式再評価したlambdaが44.17ならL<=4489、45.3ならL<=4294、
46.4ならL<=4113でも基準費用を下回る。連続角度の44.17をそのまま使用して
改善済みとは判断しない。Qやnon-loader費用が変わる場合は式を更新する。

再現は `python chemistry_angle_search_v3_budget.py`。

## 独立実験の範囲

整数angle_wordsの変更を提案し、その後のW/H2_I再fitと公式数値評価で選ぶ。
低位bitへのaddress-affine XOR変更については、既存loaderの前後にX/CXを加える
構成を検討する。元loaderの到達状態依存と、公式が同じ回路を逆順に再適用する
仕様の両方を検証する必要がある。単純なpre/post変更が無条件に正しいとは仮定しない。

低位語の変更は量子化誤差を変えるため、Toffoliを増やさない構成が見つかっても
物理精度・lambda改善が得られたこととは別である。実行結果は各実験の報告に記録する。
