# DQI の測定消去と共通制御の再点検

対象は採用ZIPのDQIメンバー SHA-256
`e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`。
58,868,734静的命令、Q889、HMR 71,502、個別の古典条件付きCZ 537,071、
CCX 363,654、CCZ 7,000、CSWAP 12,240である。オペコードの件数には、
古典条件のブロック内で一部のショットだけ実行される命令も含まれる。

score5で独立確認した二つの短縮は、最終のCCXをHMRと条件付きCZを用いる
同値な測定操作に書き換えた。元からあったHMRの回数とQ889はそのまま。
測定結果の宛先を新しい古典ビットに取り、元の測定時点で古い宛先に転送する。
測定結果ごとのKraus演算子の一致、および実際のKMBへの適用が
`score5_dqi_hmr_independent_review.json` に記録されている。
DQIの採点費用はR(eps_plus) × Q² × 実行Toffoli-likeのショット平均。
このメンバーの公式検証記録は102,400ケース、値と位相のエラー0、
平均382066.529365234、費用359707293756.04297。

## 再点検

- `e4_strict.json` と `e4_fixed_branch.json` は既存の
  `score5_dqi_hmr_tail.cpp` を採用版に再実行した記録。HMR前に、
  対象をX、CX、CCXの書込先としてだけ扱う末尾を探す。
  最上位HMR 28,812件、固定条件内の全HMR 71,502件のいずれでも
  追加でCCXを減らせる区間は0件。
- `descendant_hmr.cpp` はHMRの属する条件スコープで完結する子ブロックを
  またぐ場合まで含めて探索した。候補は0件。この範囲の緩和は探索のみ。
  対象を位相に読んだり、制御として使うものは境界とした。
- `pair_screen.cpp` は、同じ条件スコープにあり共通する二つの制御を
  持つCCXとCCZの組を探索した。CCXは制御の変更か先の標的への
  参照まで、CCZは先の3入力のどれかが書き換えられるまでを対象とした。
  CCXとCCZとも単独条件なしのものを対象としたが、実回路ではすべて
  この形式だった。隣接と拡張のどちらでも0組。4つの小さい実KMB
  で、隣接、可換な間隔、不可換な間隔、一つ前より古い候補の動作を
  検査した。

CCX(a,b,t)とCCX(a,b,u)を可換に集められるとき、
CX(t,u), CCX(a,b,t), CX(t,u)に改めると1 CCXになる。
CCZ(a,b,t)とCCZ(a,b,u)には
CX(t,u), CCZ(a,b,u), CX(t,u)を用いれば1 CCZになる。
これらの変換はt,uの値を限定しない。回路全体の結果は、
共有制御が線形結合としてだけ現れる場合や測定で生じる位相を
再表現する場合の探索には及ばない。

```bash
g++ -O3 -std=c++17 descendant_hmr.cpp -o /tmp/dqi-descendant-hmr
/tmp/dqi-descendant-hmr "$DQI_E4_KMB" /tmp/dqi-descendant-hmr.json
g++ -O3 -std=c++17 pair_screen.cpp -o /tmp/dqi-pair-screen
/tmp/dqi-pair-screen "$DQI_E4_KMB" /tmp/dqi-pair-screen.json
```
