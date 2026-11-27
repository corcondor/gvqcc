# V110の位相修復移植（研究用・提出不可）

既存 [#229](https://github.com/corcondor/gvqcc/pull/229) の位相参照と Lean 補題、[#227](https://github.com/corcondor/gvqcc/pull/227) の R→HMR 記録を、Kaggle提出済み実ファイル V110 に移植。既存の零判定を使い、復元された合法シンドロームがゼロの場合だけ参照位相を返済する。最大重み35で、先頭35モーメントがゼロなら Vandermonde により合法シンドローム全体がゼロ。復元値が既に壊れた場合にはこの保証を使えない。条件は量子回路で可逆計算し、入力の外部判定・測定・選別は追加しない。

* 親 SHA-256 `8010980d566e6b16d255bfa7f00b37fb0d00c62978cd8bd3932b1981adc05841`。
* 候補 SHA-256 `fd0d44937b72fff41b4e64c51c36d2875ff76e1420c44eb82ecfb56768973e9a`。900Q、318,584→319,366 静的有料、120,543,184命令、Rを41箇所でHMRに変更し実際の測定結果を位相参照で再利用。
* 比較した1,088ショットずつのうち、ゼロ・シンドロームは位相140/272→0/272。重み18〜35は両方0/544。重み1〜17は引き続き値272/272、位相136/272（値誤りと重複）、作業ビット・古典マスクの不一致は0。公式ベリファイアや全入力の証明ではない。
* 症状は `m·(x⊕x̂)`。逆分岐の推定値が実際の測定直前の値と一致しないと補正が残る。低重みの順・逆写像の最初の不一致は未確定。零点修復だけで316k版を完成扱いしない。

再現: KickMix 1.0.0、Python 3.12、NumPy、公式DQIベリファイアのある `DQI_VERIFIER_DIR` を設定する。

```sh
python prepare.py dqi.kmb
g++ -O3 -std=c++20 shadow_affine.cpp -o shadow_affine
./shadow_affine dqi.kmb qids.txt mask_ids.txt candidate.kmb
python replay.py candidate.kmb fresh.json
python replay_all.py candidate.kmb all.json --all-weights
```

既存局所Lean補題は回路全体の保証ではない。巨大KMBは公開コミットに入れず、親ハッシュを固定した生成コードと結果を掲載。main変更・Kaggle再提出なし。
