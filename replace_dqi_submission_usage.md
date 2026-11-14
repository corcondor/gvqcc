# 元の提出 ZIP の DQI だけを差し替える

`replace_dqi_submission.py` は、元の `submission.zip` にある **`dqi.kmb` だけ**を、検証が完了した新しい DQI に置き換える。元の `invsqrt`、chemistry の `submission.npz`、全 `angle_k_*.kmb` など、それ以外のファイル内容はバイト単位で保持する。手元で改善した chemistry の重みもそのまま残る。

## Windows PowerShell での実行例

リポジトリのフォルダーから、次の 1 行を実行する。新 DQI と検証 JSON のファイル名は、実際に取得した名前へ合わせる。

```powershell
py replace_dqi_submission.py --baseline-zip "C:\Users\81808\.openclaw\gvqcc\kernel_out\submission.zip" --dqi "C:\Users\81808\.openclaw\gvqcc\dqi_improved.kmb" --verification "C:\Users\81808\.openclaw\gvqcc\dqi_full_verify.json" --output "C:\Users\81808\.openclaw\gvqcc\submission_dqi_improved.zip"
```

Python の標準ライブラリだけで動く。`kmb_profile.py` を同じフォルダーに置く。Kickmix を読み込んだり、量子回路の検証を再実行したりはしない。

## 必要な検証 JSON

元の DQI は `821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3` に固定している。

新しい DQI については、**実際に完了した公式検証処理が保存した JSON** を使う。トップレベルに `status=PASS`、`verified_shots=102400`、`log2_delta=-128`、`circuit_sha256`、量子ビット・古典ビット・命令数、値と位相のエラー数、および `score` が必要。ファイルの SHA-256 と KMB ヘッダーが、その JSON の対象回路と一致することを確かめてから ZIP を作る。

256 ショット等のスモーク検証結果や、途中経過の JSON では作成しない。DQI ではエラー数が 0 でなくても公式の統計的判定に合格する場合があるため、パッケージ処理が独自に「エラー数 0」を要求することはない。

検証合格はスコア改善の保証ではない。DQI は検証時のサンプルやエラー率によってコストが変わるため、改善幅は同じ条件での比較および Kaggle の採点結果で判断する。

この処理が確認するのは、提供された検証記録とファイルの一致である。JSON の作成者や、記録された計算が本当に実行されたことを暗号学的に証明する仕組みではない。検証記録の `PASS` やショット数を手作業で書き換えないこと。

## 出力

成功すると、指定した新しい ZIP と、同じ場所の `submission_dqi_improved.receipt.json` ができる。

- 元 ZIP と新 ZIP の SHA-256。
- 全 ZIP メンバーの変更前・変更後の SHA-256 とサイズ。
- 元 DQI の固定ハッシュと、新 DQI のハッシュ。
- 使用した検証 JSON の SHA-256 と検証結果。
- DQI 以外の全ファイルがバイト単位で保持されたこと。

ZIP の圧縮データや ZIP 全体のバイト列は作り直すため変わるが、中に入っている DQI 以外のファイルのバイト列は変えない。元 ZIP、元 DQI、検証 JSON は書き換えず、既存の出力 ZIP や記録への上書きも拒否する。

同名ファイルが重複している ZIP、`../` などを含むパス、複数の `dqi.kmb` / `dqi.kmx`、暗号化ファイル、リンクや特殊ファイルを含む ZIP は、対象が曖昧なので受け付けない。

## パッケージ処理のテスト

```powershell
py -m unittest test_replace_dqi_submission -v
```

テストで作る小さな回路と検証 JSON は、ZIP の保存・拒否動作だけを確認する**合成テストデータ**である。実際の DQI 解、公式検証の PASS、スコア改善の証拠ではない。
