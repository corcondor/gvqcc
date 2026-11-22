# OSS流用の実KMB費用検証（2026-11-23）

**目標はスコア増加。学術的な新規性は評価対象外。** 既存の失敗履歴を検索した上で、未検証の公開実装を流用した。既存33.17023の公開Kaggleバッジと、公開3費用式のローカル換算33.17027660010は区別する。**今回の新しい公式スコア・新しいTQ改善は0件**。

## 実KMB実験

| 手法 | 実回路で実行した範囲 | 減った実Toffoli相当 | 結論 |
|---|---|---:|---|
| [RMSynth](https://github.com/super-quantum/rmsynth) (Apache-2.0) | 37Q公開invqrt, SHA `bb676b95f94c...`, 60,766命令から5,343の線形位相区間を抽出。複数Tを含む3区間（操作範囲32659–32665, 34337–34344, 35285–35296）、各最大5量子ビットのReed–Muller coset全探索。 | **0T**（各3→3） | ≤5量子線局所のみ最小。より広い非線形・条件付き領域は未評価 |
| [Gidney 2018](https://arxiv.org/abs/1709.06648) / [MBUndo 2026](https://arxiv.org/abs/2611.02345) | 測定付きAND消去の状態ベクトル・位相証明20,016分岐、最大誤差1.24e-16。900Q公開DQI `4b5721411adc...` 69,782,188命令の保守的クリーンAND逆計算対を走査 | **0T**（有資格組0） | 局所ガジェットは正しいが大規模への適用箇所なし。一般のMBUndo全パス未移植 |
| [RwUn](https://github.com/cadake/RwUn-artifact) (MIT) | 16公開KMB（invqrt 1本・3,357T ANGLE 15本）の実命令 `CCX(a,b,q);CX(q,t)` を読み、1,389箇所の交換可な箇所を発見。4線全16基底で純粋な可逆写像の同値証明 | **0T**（可換交換だけなら+1T） | 後続のCCXとの厳密相殺可能箇所0。実37Q KMBを書き換えたが回路費用悪化につき採用しない |

### RwUnの実KMB変更と費用

元37Q invsqrt `bb676b95f94c923cc5482f6cd8d457ab5ff3e8180c8f7cfd2c9678335d0ba56b`、再生成37Q `47122f276c46bd27213ea957dce7937282d482ad8bcb75a879cff7f3f34997f5`。KMB全体を元の `60,766 instructions / 1,553 T-equivalent / 37Q` から `60,767 instructions / 1,554 T-equivalent / 37Q` とした。**費用式で -0.00671181点**、不採用。この実験にnative KickMixは未実行。編集したゲートは位相なしの厳密4線恒等式、他はバイト列上の同じ命令。

**検出した実装バグ:** 過去の研究用 `native_kmb.py` の `to_bytes` はヘッダ中のToffoli相当数をCCXだけで算出し、CCZ/CSWAPを数えず、元37Q KMBの全バイトラウンドトリップに失敗した。比較検証ZIP内の**コピーのみ** `header[5] = count(op & 127 in {48,49,50})` に修正し、元KMBのバイト完全一致を確認した。元の研究ファイルおよびmainブランチは未変更。

## 既知失敗との比較：再試行しない

- [andigu/uncompute](https://github.com/andigu/uncompute) のBM/Forney移植は、以前 `research/archive/workspace-evidence/alexchilton_history_audit_ja.md` に具体的履歴がある。新規実装として数えない。
- [Swapnil Jain GF12](https://github.com/Swapnil-jain/gf2m-circuits/blob/main/multipliers/circuits/final_f12.slp) の公開SLPは78 AND・132 XOR、しかも多項式 `0x1009`。当該DQIのGF12が既に42 AND・`0x1053` なので単純移植は36積/乗算悪化。実KMBの変更前に棄却。
- andiguの別仕様 BMは442,397T / 1,837Q。現在の公開900Q / 推計平均376,595Tに対し、同じRと仮定した `T*Q²` は約4.89倍。不採用（有限体基底・失敗率も異なる）。 
- 過去のGF12 42→41積の400M級探索、ANGLE単独XAG、単純Reqomp型ペブリングは成功扱いして再実行しない。

## 達成率（測定条件を定義）

REVS、Reqomp、RwUn、MBUndo/Gidney、RMSynth、BM/Forneyの **6系統** を母集団とすると、本ターンに実KMB命令で新しく実行した系統は **3/6=50%**。**採点済み18ファイルの公式スコア改善に到達した系統は0/6=0%。** これらの割合は「学術的新規性」でも「将来成功確率」でもない。

## 再現用出力

当該会話に生成した `GVQCC_OSS_Scoring_Reuse_REAL_20261123.zip` (SHA256 `dbbd4f8ba7ab82eeb10d17d17a183dc8db84eee9f81a052b3e24f5bcddba0ddb`) を参照。含む: `rm_phase_port.py`, `native_kmb.py`(ローカル修正版), `mbundo_dqi_screen.cpp`, `rwun_commute_port.py`, `rwun_real_kmb_patch.py`, `mbu_proof.py`, 6件unit tests, `score_screen.py`, 結果JSON、拒否した実37Q KMB、ハッシュ一覧、原著出典と権利表示。実テスト6件PASS、ZIP検証PASS。

**この結果はスコア更新ではない。** Native KickMix / Kaggle提出は実行していない。新しい方向は、これらを繰り返すのでなく、現在の本番900Q DQIの復号・Forney段を *アルゴリズム単位* で変える手法へ進むこと。
