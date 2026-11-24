# GVQCC × DeepMind「独立チーム＋Lean」実験（2026-11-24）

## 研究資料と対象

- 対象: 公開 V8 7-bit C46 / 1,219 アドレス / 15 ANGLE KMB / 片道3,357 Toffoli、128 qubits。
- DeepMind一次論文: [Discovering formally verified quantum programs with AI (arXiv:2611.09822)](https://arxiv.org/abs/2611.09822) / [公式説明](https://deepmind.google/blog/finding-faster-quantum-algorithms-with-agents-and-formal-verification/) / [Leanライブラリ](https://github.com/google-deepmind/formal-quantum-computation)。「独立チームが探索→形式証明→共有」の制御方式を参考にした**小規模な独立実装**であり、Gemini 4やDeepMind社内エージェントを実際に動かしたものではない。
- **本コードは公式スコア更新を達成していない。** 公開されたバンク単体APIは維持できていない。元ZIPや提出KMBは変更していない。

## 実装した「学習方法」

8つの**異なる変換方針**（AIモデル8体ではなく探索ポリシー8種）を各64回、共有73次元のGF(2)可逆基底を候補として進化させる。前回の高評価解からの派生だけでなく、一時的な費用悪化や別の谷へ遷移する経路も残す。各案をSHAで重複排除し、真の80+2次元線形変換を保持しながら評価する。

- team0: 非隣接基底のswap
- team1: 1つの方向に他方向をXORするトランスベクション
- team2: 2連続XOR
- team3: swapとXORを同時適用
- team4: 3位置の循環置換
- team5: XOR→swap→XORの非局所的置換
- team6: 長さ3〜8の複合変換
- team7: 長さ8〜16の大きな非単調変換

本実装では、`frame_score`（前後の82×82可逆線形変換の実CNOT個数）で512候補を安く順位付け。16案を実バイナリKMB化して**値・位相・128Q**を検証した。最良は候補#368、研究用部分KMBの `CCX9 / CX1965`。元の同部分KMBは `CCX9 / CX2164` なので **CX−199**、実Toffoli変化0。

8種のポリシーはあくまで**共通基底の異なる移動作用素**であり、512個の独立アルゴリズムでも、512個のスコア改善でもない。

## 新しい二バンク結合KMB（前進のみ）

`compile_pair_forward.py` は公開k13のHMRを延期して中間Scratchを保持し、候補#368の9CCX基底アダプタを使う。公開k14のワード更新を再現しつつScratch新規生成82CCXを省く。生成された**本物のネイティブKMB**は次の通り。

| 指標 | 元k13+k14 | 連結KMB |
|---|---:|---:|
| Toffoli | 422 | **349** |
| Q | 128 | **128** |
| HMR数 | 164 | **91** |
| 対象 | 独立2バンク | 一体化した順方向のみ |

独立検証 `independent_forward_verifier.py` は **全1,219アドレス**の B12→B13→B14 を計算し、最後の選択・出力35ビット・Scratch82本・HMR91分岐の位相係数をすべて照合。`address_err=word_err=scratch_err=phase_err=0`。CCX2種類・条件付きCZ2種類を1ゲートずつ削除した**4つの負例**はすべて不合格。SHAおよび再現原票は `forward_pair_receipt.json` と `independent_forward_receipt.json`。

⚠︎ **この349Tは提出可能な `angle_k_13.kmb` と `angle_k_14.kmb` の代替ではない。** 個別バンクは scratch=0での呼出し規約があり、後段バンクが前段のdirty scratchを受け取る今回の連結KMBとは契約が違う。逆方向 k14→k13 と公式KickMix試験も未実施。73Tを公式スコア改善として加算しない。

## Lean 4

`lean/GVQCC.lean` は `leanprover/lean4:v4.35.0` 向けに**生成済み**。3つの一般Boolean恒等式、実計算で得られた73本の共通関数の有限真理値同一性、512案の各変更ベクトルの同一性（計588定理）を `by decide` で記述している。各Natは公開KMBから抽出した2,438合法入力状態を表す2,438ビットの真理値マスクである。

このLean定理は、**入力済み真理値マスクの有限同値を証明するだけ**であり、元KMBの抽出処理自体の信頼性や全波動関数上の正しさをLeanで形式化したものではない。Leanバイナリがこのコンテナにはないため、現在の`lean_proof_status.json`は `GENERATED_NOT_KERNEL_COMPILED`。コンパイル済みと誤記しない。

```bash
cd lean
lake build
```

DeepMind純正の `QuantumComputation` はより強いQuantum Hoare仕様の環境だが、本実験では依存の軽いBooleanトレースで一次検証する。量子状態／HMR全般のLean形式化と独立バンクの公式検証は追加の実装課題。

## 実行方法

Python 3.11+、NumPyが必要。入力 `public_3357.zip` を同ディレクトリに配置。

```bash
python -m pip install numpy
python patch_builder.py
GVQCC_DUMP_MATRICES=baseline_affine.json python build_73d_9t_adapter_evolved.py public_3357.zip
python multi_team_search.py --episodes 8 --emit 16 --seed 20261124
python generate_lean.py
python compile_pair_forward.py
python independent_forward_verifier.py
(cd lean && lake build)  # Lean 4.35.0が必要
```

`--episodes 8` は 8 episode×8変換ポリシー×8候補=512件。

## どこまで完成し、何が未完成か

| 項目 | 状態 |
|---|---|
| 512候補・重複排除 | Python実行済み |
| 16実KMBの局所検証 | PASS |
| 349T・128Qの順方向一体化KMB | 生成・独立トレース検証PASS |
| 4負例の検出 | PASS |
| Leanソース588定理 | 生成・Python真理値確認済み、Leanコンパイル未実行 |
| 両方向と独立15バンクAPI | **未達** |
| 角度表を変えたW/H2再学習 | この探索では **0ステップ**。角度表を変えないため無駄な学習を行わずに済んだ |
| 公式KickMix / Kaggle総合スコア | **未採点・更新なし** |

次の探索の評価値は、常に**公式呼出し契約に収まる実KMBの有料ゲート数**とし、同じ73D基底交換を増やすことは優先しない。物理学習はANGLE角度表そのものを変えた候補が生成された後に開始する。