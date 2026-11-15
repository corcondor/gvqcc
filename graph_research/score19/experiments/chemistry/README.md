# score18 ANGLE の成分間の積を探す

実際の score18 ZIP の化学ローダーを、入力ファイルの SHA-256 と照合した。各 CCX の4下位ビットと7上位ビットの混合部分を、1,216有効アドレスから再抽出した。以前の4030版の抽出物を使い回すと計算順とファイルハッシュが一致しなかったため、score18 から作り直した。同じ数の積は残っている。

従来のグラフは混合行列のペア和を繰り返し、階数2以下に残る辞書要素の支持を結合する。今回は、その閉包からペア和で到達しなくても、より多くの項を一度に XOR すれば階数2以下の新しい行列になる可能性を調べた。成分をまたぐ新しい辞書要素があれば、独立だった出力方向同士を別の組にできる可能性がある。

| バッチ | 4出力方向が依存する成分のサイズ | 追加の成分 | 検査した成分間支持 | 階数2以下 |
|---|---|---:|---:|---:|
| 8 | 1, 1, 1, 3 | 143 | 19,268 | 0 |
| 9 | 1, 1, 1, 2 | 155 | 8,240 | 0 |
| 14 | 1, 1, 1, 2 | 144 | 8,705 | 0 |

最初の列に示した4出力方向の依存は、全15本について重複しない2ペアの出力 XOR が一致する条件から列挙した。該当は表の3件。各件について、元の成分のみ、または元の成分と任意の追加1成分を合わせ、2成分以上にまたがる支持集合をすべて検査した。3件すべてで、候補の混合行列は階数が3以上だった。

別の Z3 実装では、任意の支持と任意の低側平面を許し、二つ以上の成分にまたがる階数2以下の行列が存在するかを直接問うた。対象は同じ3バッチで、各12秒のソルバー制限で `unknown (timeout)` だった。これは存在を否定する証拠にはならない。

この探索では新しい CCX 削減も、再検証に回せる候補KMBも得られなかった。元の辞書の線形包の外に置く積、成分を二つ以上追加した厳密探索、特徴量と出力積の同時再合成はこの有限検査の外にある。

## 再現

KickMix、NumPy、Z3を用意し、score18 の化学ファイルを `source/` に展開する。`WORDS` は既存の `score9_rebatch_synth_source_words_1232.npy`。

```sh
python ../j5_triples/export.py --repo "$REPO" --loaders source --words "$WORDS" --out .
python check_small_bridges.py --segments segments.bin --metadata segments.json --loaders source --out small_bridges.json
for batch in 8 9 14; do
  python minrank_bridge.py --segments segments.bin --metadata segments.json --loaders source --batch "$batch" --seconds 12 --output "minrank_$batch.json"
done
```
