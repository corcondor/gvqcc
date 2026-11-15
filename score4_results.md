# Score4: 追加16 Toffoli削減、公式検証PASS

提出済み score3 のDQIから、**無条件CCXを新たに16個削減**した。これは以前の480個削減およびinvsqrtの1個削減への上乗せである。量子ビット数889と古典ビット数208,087は同じ。追加した32個のCXはToffoli費用に含まれないため、総命令数は16増える一方、採点対象のToffoli数は16減る。

## 実測結果

| 指標 | score3 | score4 |
|---|---:|---:|
| 静的Toffoli系ゲート数 | 382,934 | 382,918 |
| 公式平均Toffoli | 382095.687792968762 | 382079.294374999998 |
| 量子ビット | 889 | 889 |
| 公式DQIコスト | 359734745778.987610 | 359719311733.972595 |
| 値エラー / 位相エラー | 0 / 0 | 0 / 0 |
| 公式検証ケース | 102,400 | 102,400 |

公式コストは15434045.015015、0.004290396%低下した。検証器は変更せず、既定のseed、salt、confidence（log2_delta=-128）で実行した。検証時間は345.930秒。両回路のハッシュに応じて検証入力が変わるので、平均Toffoliの実測差と、厳密な回路上の16個削減は分ける。

## 書き換え

無関係な測定や古典操作を跨いで可換なCCXを移し、次の恒等式を適用した。

```text
CCX(a,b,t); CCX(a,b,u)
  -> CX(t,u); CCX(a,b,t); CX(t,u)
```

任意の初期値を持つt,uでも両方へ同じ積abをXORする。8区間の16組に適用した。従来passは測定を一律の境界として扱ったため、今回の候補を除外していた。新passは各中間ゲートの可換性をチェックし、HMR/resetがCCXの3本のwireと独立な場合だけ跨ぐ。測定結果や位相補償を削っていない。

## 等価性と実ファイルへの結合

1. 4量子ビットの16基底列で、符号を含む恒等式を確認した。線形性から任意の重ね合わせと参照系とのエンタングルメントを含む。
2. 別実装で、先行置換を反映した局所回路上の16移動を再検査した。
3. 8区間×256入力のnative比較で量子値・古典値・位相が一致した。
4. 実候補の8変更区間が独立証明の置換後SHAと一致した。残る9区間は全10operand columns、register bytesが元とbyte一致した。
5. 最後に実KMBを公式102,400ケースへ渡し、値・位相エラー0でPASSした。

一次証拠: `score4_dqi_full_verification.json`, `score4_dqi_guard_review.json`, `score4_dqi_guard_binding.json`, `score4_dqi_rewrite_certificate.json`。

## 提出ファイル

`submission.zip` は18ファイル入りで、今回のDQI以外の17ファイルをscore3からbyte単位で保持した。invsqrtは既存200,540,928ケースPASS、chemistryは既存78,080ケースPASSのファイルとSHA一致する。全memberのSHA/CRCを再構成時に確認済み。

- ZIPサイズ: 63,552,791 bytes
- ZIP SHA256: `72bac12e45e4d8f70af949f408a72a79c30e7422f9b3bb578e06ef8228cfb1e2`
- DQI SHA256: `5a60d66233198be8ce05d9710bd35a7d2d6700bbced87560d405651070ae8194`
- 自己完結再構成セル: `score4_package_cell.py`。元score3 ZIPを入力し、ネットワーク・追加依存・再最適化なしで同じ候補を再構成する。
- ソース・全証明・探索記録: `score4_source_and_evidence.zip`。

## Public Scoreの状態

今回のZIPはこの記録時点ではKaggleへ新規提出していないため、Public Scoreは未計測。過去のscore3は27.28236、v27 chemistry+exact4096は27.28543で、選択済みの27.30683を下回ったことを提出画面で確認した。今回の厳密な16個削減・ローカル公式費用低下を、Kaggle最高値更新とは表現しない。

## 他の探索

invsqrtのcache routing、affine差分、HMR延期、QROMのfunctional tensor合成、DQI13-AND共同写像の有限探索も実装・実行した。これらから今回の追加削減は得られていない。陽性対照の削減を実提出の削減へ加算していない。負の結果と有限探索の範囲は各 `score4_*_report.md` / JSONに保持した。
