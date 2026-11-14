# ANGLE ローダー：テンソル縮約の実験と、固定構造に対する下界

日付: 2026-11-15（日本時間）.

## 結果

**今回、化学ローダーの追加 CCX 削減は得られていない.** 既存の片道4033 CCX、量子ビット数、角度表、提出物は変更していない. その一方、従来の「削減候補が見つからない」という観測を、次の2つの限定された数学的な不可能性証明へ進めた.

1. **現在と同じ特徴関数の集合を準備する段階は、74 CCX が下界であり、既存回路はちょうど74個を使っている.**
2. **現在の線形な入出力処理と特徴関数を維持し、現在使っている積を候補集合とする限り、全体で2706個の積のどれも、他の積の任意の XOR と特徴関数の無料の線形結合で消去できない.** これは2項だけの照合より広い範囲を排除する.

どちらもローダー全体の大域最適性を意味しない. 新しい積、異なる中間関数、出力データの借用、角度の符号化変更、段階をまたぐ同時合成は対象外である.

## 1. 読んだ一次資料と今回の実装

中心となったのは Khoruzhii, Gelß, Pokutta,
[*Tensor Decomposition for Non-Clifford Gate Minimization*, arXiv:2602.15285v2](https://arxiv.org/abs/2602.15285v2)
（2026-10-26改訂）と、その[公開実装 Polytof](https://github.com/ZIB-IOL/polytof)である.
使用した実装のコミットは `0dcac107d15adc34dc646242d222f21ae7d32699`.

論文の flip graph search は、一時的に積を増やす plus 変換を許し、単純な局所削減で動けない状態から別の分解へ移る. 例えば GF(2) 上で

\[
u_1v_1w_1+u_2v_2w_2
=(u_1+u_2)v_1w_1
+u_2(v_1+v_2)w_2
+u_2v_1(w_1+w_2)
\]

が成立する. 単に同じ因子を持つ2項を探す手法より探索範囲が広い.

今回の ANGLE は一般的な Hadamard を許さないので、任意の CCZ 位相回路への変換は採用していない. **作者実装の COMM モード**を使い、2つの制御側だけを交換・合成し、出力側を分離した二次形式

\[
z\longmapsto z\oplus\sum_i u_i(x)v_i(x)w_i
\]

として探索した. 各項は X/CX/CCX だけで再構成でき、出力を制御側に混ぜることも、量子ビットを追加することもない. Boolean 恒等式 \(x^2=x\) による一次の補正は、最適化前後の多項式差から明示的に回収する実装にした.

AND を非線形な資源として数える理論上の背景は、Boyar–Find,
[*Multiplicative Complexity of Vector Valued Boolean Functions*](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=919080)
（[NIST書誌](https://www.nist.gov/publications/multiplicative-complexity-vector-value-boolean-functions)）で確認した.
下に示す74個と固定積集合の下界は、この論文の数値を転用したものではなく、実回路の正確な真理値表から今回導いた証明である.

## 2. 作者の探索器で実際に調べた範囲

対象は batch 1〜14 の出力蓄積部分. batch 0 は途中に3つの非線形な制御更新があり、この分離した二次形式の条件を満たさないので除外した.

| 対象 | 数値 |
|---|---:|
| 変換したローダー | 14 |
| 各二次テンソルの形 | 90 × 90 × 35 |
| 元の積の総数 | 2706 |
| 各回路の積の数 | 187〜212 |
| 作者ログの walk attempts | 28028 |
| 作者ログの `total_flips` | 88,717,654 |
| 成功した plus 操作 | 15,243,888 |
| 作者ログの探索収集時間の合計 | 25.69秒 |
| CCX 削減 | **0** |

`total_flips` は作者実装が数える探索ループ回数であり、全てが成功した flip 変換という意味ではない. 指定は1回路あたり最大2000 walks、最大200000 steps、2 threads、pool size16、plus interval2000. 原実装の実行ログは `theory_qrom_polytof_search.json`、集計は `theory_qrom_polytof_summary.json`.

この結果は有限の確率的探索の不成功であり、探索空間を尽くした証明ではない. また作者実装では、消去済みノードを含む配列から plus 候補を64回抽出して失敗すると walk が終了する. 今回も指定した最大200000 stepsより早く終了する walk が多かった. したがって「各 walk を200000回必ず実行した」「全ての plus の経路を調べた」という報告はしない. 改良候補を得ていないため、最適化器の候補検証数は0である.

## 3. 再構成と量子位相を独立に検証

探索の入出力変換が正しいかは、作者のテンソル検証だけに依存せず、既存の独立した `chemistry_reachable_exact_proof.py` で検証した.

14回路をテンソル表現から再構成し、**1220アドレス × 14回路 × 正逆2方向 = 34160遷移**を全数確認した. 40出力ビット、selection の復元、scratch のゼロ、R のゼロ入力、**2072個の独立な HMR 測定結果に対応する位相係数の恒等的な消去**が通った. 再構成後も各回路125量子ビットで、CCX数は変わらない. 実行11.49秒.

これは実際に到達する正逆の batch 入力部分空間上の証明であり、任意の40ビット target に対する汎用 XOR オラクルへの拡張を主張するものではない. 元回路と同じ到達部分空間を扱う. 全ての測定枝が同じ写像と相対位相0を与えるので、その部分空間内の重ね合わせと参照系とのもつれも線形性で含まれる.

検証記録: `theory_qrom_all_bridge_proof.json`.

## 4. 74 CCX の下界：同じ中間関数を作る限り、これ以上減らせない

batch 1〜14 は5つの保存タグ

\[
s=(a_0a_1,\ a_0a_2,\ a_1a_2,\ a_0a_3,\ a_1a_3)
\]

を、角度ワードの bit 6 XOR bit 7 として引き継ぐ. このタグを露出した直後から、現在の90本の制御用ワイヤーを準備する段階を考える. 残り35本の角度データは、この段階の新しい入力として借りない.

各ワイヤーに載るBoolean関数を、全1220アドレス上の1220ビット真理値表として扱い、定数1を加えた線形空間の次元を GF(2) 上の消去法で求めた.

\[
\dim V_{\mathrm{in}}=17,\qquad
\dim V_{\mathrm{required}}=91.
\]

X と CX は既知の関数の線形結合しか作らない. 1つの CCX は、制御2本の積という高々1つの新しい関数を追加する. 従って、この同じ必要関数空間を生成するためには

\[
T_{\mathrm{features}}\ge 91-17=74
\]

が必要である. 実回路は74 CCX を使い、**全74段で次元がちょうど1ずつ増える**ことまで確認した. 14回路すべて同じ結論となった.

この下界は入力・出力の途中の基底を変えても成り立つ. 一方、必要な中間関数の集合を変える、35本の角度データを借りる、後段と同時に合成する場合には、この固定インターフェースの下界を適用してはいけない.

コードと証明記録: `theory_qrom_prefix_bound.py`, `theory_qrom_prefix_bound.json`（全数計算1.39秒）.

## 5. 2706積の辞書：任意の多項 XOR でも既存積を間引けない

次は中間関数を形式的に独立とみなさず、**実際のアドレスから生じる非線形な関係も含めて**調べた.

準備済み関数と定数が張る空間を \(V\)、現在の各制御積を \(p_i(a)\) とする. 全1220アドレス上で

\[
\dim\bigl(V+\langle p_1,\ldots,p_r\rangle\bigr)-\dim V=r
\]

を14回路すべてで確認した. 具体的な次元差はそれぞれ187, 188, 189または212で、その回路の積の数に等しい.

よって \(p_i\) は商空間 \(\mathcal F/V\) で線形独立である. 元の出力データに対する線形処理を固定して取り除いた後の、積から出力への寄与が

\[
F(a)=\sum_i p_i(a)w_i+v(a),\qquad v\in V^{35}
\]

であり、全ての \(w_i\) が非零なので、同じ積の辞書における係数表示は一意である. どれかの積を消して、他の既存積の任意の XOR と無料の線形関数で置き換えることはできない.

これは既存のペア照合を何度も広げるより強い排除結果だが、**新しい積を導入する低ランク分解は排除しない**. また、到達可能な角度データの関数を新たに無料の資源として加えたり、データ側の線形処理を変えてその関数を使う場合も、この下界の範囲外である. plus 変換による探索はまさに新しい積を試すためのものであり、この下界と矛盾しない.

コードと証明記録: `theory_qrom_dictionary_rank.py`, `theory_qrom_dictionary_rank.json`（最終記録の全数計算2.00秒）.

## 6. 次の研究対象として残るもの

今回の固定構造内で繰り返す必要がなくなったのは、既存積を単に間引く探索と、同じ90ワイヤーの特徴集合を74未満のCCXで準備する探索である. 化学側で追加削減を狙うには、例えば出力に既に保持されている関数も中間資源として使う、特徴集合と後段の積を同時に作り直す、元の物理テンソルを保つ角度符号化の自由度を使う、という設計変更が必要になる.

これらの新しい設計を今回実現したとは報告しない. 現提出の4033ローダーは保持し、実際に回路が小さくなる別候補を得てから、同じ到達部分空間証明と公式の化学精度・資源評価へ進める.

## 再現

`kickmix` と NumPy を利用できる Python で実行する. 出力パスは未使用のものを指定する.

```bash
python theory_qrom_prefix_bound.py --loaders /path/to/chemistry_4033 --report new_prefix_bound.json
python theory_qrom_dictionary_rank.py --loaders /path/to/chemistry_4033 --report new_dictionary_rank.json

python theory_qrom_polytof_bridge.py prepare \
  --loaders /path/to/chemistry_4033 --workspace /path/to/new_polytof_work \
  --report new_tensor_preparation.json
```

Polytof を固定コミットから取得し、`VEC_WORDS=2, COMM` でビルドする.

```bash
g++ -D VEC_WORDS=2 -D COMM -O3 -std=c++20 -march=native -s -pthread \
  -I third_party -I src src/cpd.cpp -o /path/to/comm2
```

作業ディレクトリを `new_polytof_work` にし、tensor ID 9101〜9114を使う.

```bash
/path/to/comm2 9101 --continue --fgs --plus --save --verify --log \
  -f 200000 -m 2000 -s 16 -t 2 -p 2000
```

作者実装は乱数種を起動時に生成するので、探索経路は実行ごとに変わる. 使用した種は `theory_qrom_polytof_search.json` の各標準出力に記録されている. 元のテンソルと下界計算、回路の等価性検証は確定的に再現できる.

```bash
python theory_qrom_polytof_bridge.py verify \
  --loaders /path/to/chemistry_4033 --workspace /path/to/new_polytof_work \
  --table /path/to/chemistry_4033/submission.npz \
  --report new_bridge_proof.json --output-dir /path/to/new_candidates
```

改善が0の場合には候補KMBを書き出さない. 既存の回路ファイルは一切上書きしない.
