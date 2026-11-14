# 原821回路: 同じ2引数を共有するCCZの結合探索

実行日: 2026-11-14 UTC。結果: **今回の安全な移動条件を満たす新しい削減箇所は0件**。

## 規則と独立確認

4つの量子ビット `a,b,c,d` が異なり、classical conditionとcondition stackが同じで変化しないとき、

```text
CCZ a b c; CCZ a b d
    -> CX c d; CCZ a b d; CX c d
```

は正確に等価。位相多項式は `abc XOR abd = ab(c XOR d)` であり、前後のCXは全量子ビットの値を復元する。追加CXにも同じclassical conditionを付ける。

独立した確認では、16個の量子基底入力 × 明示条件on/off × condition stack全体のon/off = **64ケース**について、最終量子ビットと位相の完全一致を確認した。条件offでは双方とも恒等作用。基底上の位相付き置換が完全に一致するため、各固定classical branchの重ね合わせにも等価である。

これは既存CCX書き換えとは別に調べた位相因子化規則であり、特定の論文から発見した改善と主張するものではない。

## 探索条件

- `BinaryCircuit`のmmapと既存profileを利用し、大きな`kickmix.Circuit`は作っていない。
- CCZの3引数の対称性を使い、共有する2引数の3通りを全て調べた。
- 明示classical conditionが等しい候補のみ扱った。
- `HMR`、`R`、classical write、`PUSH_CONDITION`、`POP_CONDITION`、その他未証明の操作はbarrierにした。
- 片方のCCZを間の全ゲートと1ゲートずつ可換であると証明できる場合だけ、隣接させることを許可した。
- 位相ゲートとは可換。`X/CX/CCX`はCCZの3引数を書き換えない場合のみ許可。`SWAP/CSWAP`は交換する2bitが両方CCZ引数内、または両方外の場合のみ許可した。

原回路のcached SHA-256は `821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3`。このread-only実行では既存profileのSHAを利用し、巨大ファイル全体を再hashしていない。

## 結果

| 探索 | CCZ確認数 | 異なる4量子ビットの候補 | barrierで棄却 | 非可換で棄却 | 合法な削減 |
|---|---:|---:|---:|---:|---:|
| 最大距離4096命令 | 7000 | 164 | 128 | 36 | **0** |
| 同じbarrier-free区間内を距離制限なしで調査 | 7000 | 36 | 区間分割で除外 | 36 | **0** |

第2探索では安全な区間内の全候補を調べたので、4096という窓幅による見落としはこの探索条件内ではない。残った36候補の最大距離は48命令だった。複数ゲート全体の合成だけで可換になる場合、classical controlの再構成、測定をまたぐ等価変形などは調べていない。従って全CCZ最適化の不可能性を示すものではない。

### 条件付きゲートについての補足

実binaryのCCZは全7000個とも**明示`if`なしのopcode**だった。しかし全てcondition stack内で、depth 1が2956個、depth 2が4044個。したがって「明示条件なし」を「無条件実行」と取り違えない。最終stack depthは0、空stackへのPOPは0。条件の真偽や平均実行回数は、この静的走査では求めていない。

第1探索は合計1.47秒、peak RSS約122.6 MiB。第2探索はstack監査を含め合計2.05秒、peak RSS約122.0 MiB。基準KMB、提出候補、生成パイプラインは変更していない。公式フルシミュレーションも実行していない。

## 再現

コード: [dqi_ccz_pair_scan.py](dqi_ccz_pair_scan.py)

結果: [4096命令窓のJSON](dqi_ccz_pair_scan_original821.json)、[barrier-free全区間のJSON](dqi_ccz_pair_scan_segments_original821.json)

リポジトリの親ディレクトリから実行する。

```bash
python gvqcc_repo/dqi_ccz_pair_scan.py dqi_inputs/821bf8d157c0.kmb \
  --profile dqi_inputs/audit_actual_821/profile.json \
  --report gvqcc_repo/dqi_ccz_pair_scan_segments_original821.json \
  --window 0 --seconds 70
```

`--window 0`は、測定・classical write・condition stack変更等を含まない区間ごとに、距離制限なしで候補を調べる意味。出力はJSON報告だけで、KMBを書き換える機能はない。
