# GVQCC × DeepMind 型の3タスク共通・形式検証付き探索（実装試作）

2026-11-24時点の構成。原著: Google DeepMind, *Discovering formally verified quantum programs with AI*, https://arxiv.org/abs/2611.09822 。原コード: https://github.com/google-deepmind/formal-quantum-computation 。**この試作はGoogleの複数エージェントシステムを再現したものではなく、探索→Lean証明→実KMB検証を構成する独立の第1段階**。Googleのコードやデータの無断転載は含まない。Leanは同一の4.35.0をpin。

## 対象の3回路、出発点

- `dqi.kmb`: 公開900Q・69,782,188命令、原KMB SHA-256=`4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52`。限定探索の失敗歴: GF12の42CCX核の固定入力/出力基底交換、同制御CCX統合。基底・復号方式も変更可能な次段階を視野に入れる。
- `invsqrt.kmb`: 公開37Q・60,766命令、原SHA-256=`bb676b95f94c923cc5482f6cd8d457ab5ff3e8180c8f7cfd2c9678335d0ba56b`。Z_POWなどの位相回転を通した変形は現試作ではバリア扱い。
- `dfthcsos/angle_k_{0..14}.kmb`: 公開3,357 CCX/片道、各回路128Q。位相・最終scratch・到達可能な前後語を確認する既存検証器が別にある。ANGLE以外の化学コスト（Givens、状態準備、λなど）も全体の採用条件に含める。

元の公表資料はユーザー側で供給された公開再現ZIPで、**いずれもこのブランチへアップロードしない**。元回路・既存の採点・READMEは変更しない。

## 実装

1. `scan.py`：KMB v2のoperand列をストリーム的に読む。`X/CX/CCX/Z/CZ/CCZ`の測定なし区間について、制御積の融合・可換な逆演算の相殺・位相エコー（`CCX; CZ; CCX → CZ; CCZ`等）を候補生成。任意入力・出力・入力位相符号も任意とした相対位相について最大6ビットの **全 2^n 入力** を照合し、候補ごとに`candidate_*.lean`を生成する。HMR/R、条件付き命令、Z_POW、未知命令を跨がない。いずれのレジスタも初期値が0であるという仮定を用いない。
2. `lean/GVQCCMicro.lean`：KickMix部分命令のbasis-state意味論とBoolean位相、ゲート費用を形式化。ファンアウト・共通因子・位相エコーの3定理とゲート費用定理を`cases ...; decide`で証明。生成した証明もLeanのカーネルで検査する予定。**HMRの全測定分岐と一般Z_POWの量子意味論をLeanで形式化したとは主張しない。**
3. `emit.py`：発見した局所同値区間を、元ファイルのregister・未変更ゲート・全角度・condition列をバイト単位で保持し、原ファイルと異なる`*.kmb`へ再シリアライズ。元SHAと窓operand列、幅、局所の基底・位相照合を再確認。これだけでは公式採点PASSにならない。
4. `test_scan.py`：位相とコストの正例・負例とバイナリ書換えを8件、独立KMB2 writerで検査。生成実KMBの全入力比較も確認済み。

## 再現コマンド

Python 3.11以上、標準ライブラリのみ：

```bash
python3 -m unittest discover -s research/deepmind_multi -p 'test_*.py' -v
python3 research/deepmind_multi/scan.py --task dqi \
  --kmb /path/to/dqi.kmb --start 19980000 --max-ops 3000000 \
  --window 96 --out-dir output/dqi
python3 research/deepmind_multi/scan.py --task invsqrt \
  --kmb /path/to/invsqrt.kmb --window 96 --out-dir output/invsqrt
python3 research/deepmind_multi/scan.py --task angle \
  --kmb /path/to/dfthcsos/angle_k_8.kmb --window 96 --out-dir output/angle8
```

Lean4.35.0＋Lakeを導入後：

```bash
cd research/deepmind_multi/lean
lake build
# Positive candidateが出た場合、生成されたファイルをこちらから確認
lake env lean /absolute/path/to/output/angle8/angle_candidate_000.lean
```

候補が見つかった場合のみ、LeanビルドPASS後に：

```bash
python3 research/deepmind_multi/emit.py \
  --source /path/to/original.kmb --receipt output/angle8/angle_scan.json \
  --index 0 --out output/angle8/candidate.kmb
```

その後 **公式KickMixの該当task検証器** により全入力/全shot/phase確認、実Toffoli/量子ビット/化学精度・総合スコアを計測する。正しさがあってもコストが不利なら採用しない。CIでは生成ミニ回路のLean・Pythonだけを必須とし、巨大ユーザーデータをリポジトリに公開しない。

## 今回の実行結果（限定探索）

公開ANGLE15本・合計3,357 CCXを全命令スキャン。37Q逆平方根を全60,766命令スキャン。DQIは開始位置をずらした5ブロック、合計11,000,000命令をスキャン。局所置換クラスの実Toffoli削減候補は **0**。各スキャン領域のJSONとSHAは独立成果物ZIPに保存。この陰性結果は**小窓・6ビット以下・指定変換**に限られる。多出力XAG/変数変換/one-hot・測定境界を跨ぐ再設計・逆平方根近似再学習・化学係数の再最適化には結論できない。

状態: **Pythonの正例・負例試験8/8 PASS、toy実KMBの生成と位相全入力比較PASS、Leanはローカル実行環境にないためCI実行待ち、公式スコア増分なし。**

### HMRのLean補助定理

公開k1の既知の関係 `q124=q54 XOR(q4 AND q5)` に対する「測定枝の符号を条件付きZ・CZで消す」Boolean位相恒等式を追加した。HMR全回路・resetのLean証明ではない。
