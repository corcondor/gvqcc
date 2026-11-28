# invsqrt：中間値を保持しない36Qプログラム区間（2026-11-24）

**状況：原公開37Q回路の命令4390..7351だけを36Qの実KMBとして再合成。全回路はまだ36Q化していない。競技スコア改善・公式検証PASSを主張しない。**

原37Q KMB SHA-256: `bb676b95f94c923cc5482f6cd8d457ab5ff3e8180c8f7cfd2c9678335d0ba56b`。

## アルゴリズムの変更

元回路では命令7266で `CCX q20 q33 q34` を計算して保持するが、`q34` は命令4390から7265まで未使用で、7267から7351までの間も一度も参照されない。さらに命令4389は `HMR q34` で、入口の `q34=0` が保証される。

そこで入口の仮想37線の `q34=0` を保持せず、物理36線の `q34` に仮想`q36`の値を割り当てる。命令7266のCCXを発行しない。`q36`の126件の測定を含む中間プログラムで、仮想`q34`を全く参照する必要はない。命令7339の直前には仮想`q36`がHMRでゼロになっており、物理`q34`が空く。そこへ元の積を**別の入力表現から**再構築する。

\[
 q_{34}=q_{33}\left(1\oplus q_5\oplus q_7\oplus q_{15}\oplus q_{21}\right).
\]

同式は最初に16,384入力で発見し、**全`2^22`入力で不一致0**を確認。さらにこの関係の原因は実KMB命令7266..7273のSWAP/CX/X群にあり、初期の20,33,5,7,15の**任意のBoolean値**についてLeanの等式で証明できる。制御線は遅延再生成まで不変であることを元のゲート列から確認する。

| 指標 | 元37Qサブルーチン | 新36Qサブルーチン |
|---|---:|---:|
| 対象元命令 | 4390..7351（2962命令） | 同等な2970命令 |
| Q | 37 | 36 |
| CCX | 146 | 146 |
| HMR | 126 | 126 |
| 新KMB SHA-256 | — | `6b743f7ea7fde6a8291b6c2ef24533bb7dc0073040e00b7c8951b5f05f560bce` |

**境界条件**：入力は任意の元37線状態で`q34=0`とし、物理36線は`q36`を物理`q34`に格納する。出口では元の`q34`を復元し、仮想`q36=0`。`q34`の生成を遅延する以外の命令、測定出力番号、条件付き古典処理、他のゲートは不変。

## 独立検証

- 元KMBの全22bit入力（4,194,304通り）×測定結果レシピ4系統＝**16,777,216状態・分岐ケース**。各レシピは領域内126回のHMRに対して0、1、入力依存2種類の結果を供給。状態/古典bit/相対位相不一致0。
- これは全`2^126`測定履歴の総当たりではない。ただしKMBゲート順序・no-read区間の静的証拠とLeanの普遍Bool等式は任意の測定結果に依存しない可逆化根拠になる。HMR Instrument全体のLean形式化とは区別する。
- Python unit testsは任意Booleanの7変数の原命令列・変更命令列を全128通り比較。Lean 4.35.0 `GlobalRemat.lean` は普遍恒等式と任意2測定結果の相対位相合致を検証する。GitHub CI結果は実行後に判定する。
- 完全36Q版、全60,766命令、位相近似の公式200M-shot検証は**未実施**。原回路と投稿済みZIPは変更しない。明示的に部分KMBとラベル付けしており競技提出には使えない。

## 再現

Python 3.11+。PR24の元`research/invsqrt36_nonlinear_lending/`構成を利用する。**公開37Qの元KMB**を `inputs/invsqrt.kmb` に置く。`GVQCC_INVSQRT_KMB=/path/to/invsqrt.kmb`で代替可能。

```bash
python3 research/invsqrt36_nonlinear_lending/global_remat/remat36.py
python3 research/invsqrt36_nonlinear_lending/global_remat/verify_full_q34.py
python3 research/invsqrt36_nonlinear_lending/global_remat/verify_remat36.py
python3 -m unittest discover -s research/invsqrt36_nonlinear_lending/global_remat -p 'test_*.py' -v
cd research/invsqrt36_nonlinear_lending/lean
lake env lean GlobalRemat.lean
```

**本質的な残課題**：前段926..4389など、状態を保持せず表現する必要がある別のピーク区間と、7352以降を合成し、36Qの*全回路*を一つのKMBにして公式検証を通すこと。単純な入力変数の入れ替えや2CCX局所置換はこの実験に含まれない。
