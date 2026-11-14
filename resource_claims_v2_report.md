# 回路資源の主張監査（共有実ファイルから）

## 結論

1. **「ANGLEローダーは303clean ancillaまで無料」は実行可能域の説明として誤り。** グローバル採点のmax共有に加えて、各ANGLE_kの全量子ビット数128以下という独立した上限がある。現行selection11 + 5words×8bitではscratch最大77。直接ロードした15回路はangle_k_0が128Q/77scratch、残り14個は125Q/74scratch。従って追加できるのは0または3qubitsで、303までは増やせない。
2. **78CCXは完全なGF12乗算の数ではなく、99CCXのGF24ブロックを途中から数えた残数と正確に一致した。** 完全区間legacy[10528261,10534482)は6122CX+99CCX。ユーザー窓10529430から数えると先頭21CCXが欠け、残り78CCXとなる。10529400、10529439からでも同じ。これが外部スクリプトの誤り原因だと断定はしないが、数値一致は直接再現した。
3. 実e986の完全テンプレート照合はGF12 **3823箇所×42CCX**、GF24 **1376箇所×99CCX**。54CCX GF12への置換は同じGF12演算なら悪化する。GF24の2つの12bit出力は独立した2つのGF12積ではなく、結合した一つの24bit体積である。1477という回数の由来は今回確認できなかった。
4. 最新WSLのpolishコード・候補NPZ・precomputed NPZ・joint optimizerは共有ファイルには見つからない。ユーザーPC上での存在は判定していない。ログ上err2=20.396mHaの点は20mHa制約を満たさないため、その点のlambda低下を合格候補の改善として扱えない。

## Chemistry資源の正確な式

公式 `official_sources/Inzainos/verifiers/dfthcsos/verify.py` 134行でQUBIT_CAP=128、389–415行でANGLE資源、445–468行で状態準備の資源、492–516行で総量、539–553行で128上限違反の拒否を定義する。

```text
T = 2*4033 + 317 + 4095 + 2250 = 14728
Q = (40+44) + (5*8) + max(90,303,77) = 427
ANGLE totalQ <= 128
ANGLE scratch <= 128 - 11 - 40 = 77
```

従ってglobalQのmax plateauは存在するが、ANGLE circuitの合法性上限を回避できない。新規合成器はまず**77scratch以下**を守る必要がある。J/brot/R/B/Cを変える場合は全式を再計算する。

`scoreinfra/circuits.py` 10–28行はselection、wordレジスタとゼロ初期化・ゼロ復元workspaceの契約を定義する。出力wordは次のGivens演算中に生存するため自由なclean scratchではない。

共有済み基準の公式ローカル検証値（`chemistry_experiment_summary.json.baseline`）はlambda_eff=46.906589508623554、T=14728、Q=427、score=294988786.8708443。ユーザーが貼った46.905894137は別の正確な因子分解ファイルが未共有なので同一値とは扱わない。

## DQIの窓の切れ目を再計数

出典 `inverse_v2_actual_eea_product_certificate.json` 3–9行に完全区間と数、88–98行に体と演算の同一性証明を記録する。実KMXを1命令ずつ数え直した。

| 数え始め（legacy index） | 完全ブロック先頭から省略する命令数 | 省略CCX | 残りCCX |
|---|---:|---:|---:|
|10528261（完全ブロック）|0|0|99|
|10529400|1139|21|78|
|10529430|1169|21|78|
|10529439|1178|21|78|

完全演算はGF(2^12)を係数体とする`t^2+t+2048=0`の24bit拡大体における`output ^= conjugate(left)*right`。576基底対の双線形証明と任意target XOR検証があり、出力線形ランク24。12bit線形圧縮はできないが、非線形・in-place再合成の不可能性までは主張していない。

`theory_bilinear_patch.py` 62–78行は42/99テンプレートとe986 SHAを固定、90–104行は全演算・単射ワイヤー対応を照合。`theory_bilinear_manifest.json.discovery`はGF12=3823、GF24=1376を記録する。元テンソルを生成する`field_tensor.py` 3/126行は42項、`extension24_tensor.py` 3/163行は99項を明示する。42と99が大域最小であるという証明ではない。

既存CPR候補はこの5199箇所から9,901,509CXを減らしたが、CCX削減0、Q889のまま。これはファイルサイズとCNOT列の改善で、T/Qに基づく採点の改善ではない（`theory_bilinear_report.md` 8–20行）。

## 再現範囲と不足ファイル

読み込み・小規模計数のみを実行。重い全体シミュレーション、提出、外部push、既存ファイル変更は行っていない。公式verifyの再importはローカルkickmix_venvにscipyがなく失敗したため、直接のKMBメタデータ読み込みと既存公式全検証JSONを使った。この依存不足をもって全検証済みとは扱っていない。

共有ファイル検索で見つからなかったもの:

- `polish_dfthcsos_brot8.py`
- `dfthcsos_brot8_polished.npz`
- `precomputed.npz`
- `opt_dfthcsos_joint.py`

実際の数値、source SHA-256、完全certificateは同名JSONを参照。候補を新たに生成したという報告ではない。
