# 2026-11-22 反省・原因分析：Griffith型PyTorch探索がGVQCCスコアを更新できていない理由

> **判定**: 新しい実KMBの公式スコア更新 **0**。局所4bit XAG削減、PyTorch方策の合成コスト削減、物理誤差PASSを別々の成功として誇張してはいけない。
> 根拠: `QDLN_NativeWarmstart_PyTorch_Multilevel_20261122.zip`, `GVQCC_Griffith_QCC_Joint_XAG_PR17_Source_20261122.zip`, `GVQCC_20261122_7BIT_COHERENT_RANKDROP_EXECUTED_RESEARCH.zip`, `GVQCC_20261122_6BIT_C45_FULLPHYSICS_SEARCH_REPRO.zip`, `GVQCC_20261122_EXECUTED_MULTIAXIS_RESEARCH_EVIDENCE.zip`（2026-11-22 Library原票）。

## 本質的な原因

1. **探索する切断面がすでに下界を達成していた。** V8高費用5バンクの pre-HMR cached 82 + paid 27 部分では、独立formal入力に関する二次形式polar rankが54でAND下界27を達成している。16積の抽出部分でもrank32→少なくとも16積。ここを「同じ入力・同じ二次出力表現のまま16→15」に学習させたのは**不可能問題への計算投下**。ただしreachable inputや上流因子・ゲージを動かす場合には下界は適用できない。32積の全候補が排除されたわけでもない。
2. **損失関数が最終スコアを追っていなかった。** `torch_joint_native.py`と`torch_multilevel.py`は主にハード出力のMSEを最小化した。X/CX/CCXで実際に合成した前後の操作数、作業線の解放時刻、HMR相対位相、ピークQ、FeMoCo数値誤差、λeff、逆計算、15バンク共同費用、他2課題の固定ベースを返す目的関数がない。`griffith_qcc.joint`はfail-closedの**受け口**であり、実KMB生成+公式スコア報酬の閉ループではない。
3. **STE/Adamの大域マスク反転が離散回路を壊した。** 実V8の32→31二段XAGモデルでは一例でハード不一致がstep0の7560→step40の30218に増えた。32積の数百本の新hidden edgesは合法な厳密恒等変換ではなく、候補のほとんどが未検証。仮にsoft MSEが下がってもハード回路の機能一致は保証されない。最良teacherを保持しただけでは「学習によるゲート削減」にならない。
4. **局所ANF/XAG縮約を実ローダー削減と混同しかけた。** PR17の4bit 16-address witnessはbank4 bit8の5 ANF項→1 AND、bank13/14の4項→1 shared ANDを厳密検証したが、全1219アドレス、全15独立KMB、128Q、HMR/フィードフォワード、時間方向の関係を満たす再合成ではない。(15KMB)に適用できる持続キャッシュの配線・phase/scratch証明がない。`joint_grid_research_receipt.json`でも`hardware:null`、`score_comparable_cost:null`。
5. **バンクを独立に最適化した結果、隣接バンクで費用が増えた。** rankdrop実験ではbank7 bit0 rank16→15を達成し物理PASSでも、bank8がrank2→13に上昇。別のGF(2) shared-AND cost proxyは285→287Tと悪化し、新ANGLE KMB未生成。rankは局所proxyであってコンパイラの実Toffoliではない。
6. **物理制約のギリギリ解を壊した。** V8はe1≈e2≈19.99999995 mHaで上限20mHaにほぼ接している。7bit→6bit固定表現では最終e2=278.689mHa、固定6bit辞書への最良射影下界は202.0646mHa。C46→C45再学習でも最良e2=20.4633mHa>20でFAIL。これは探索範囲／固定辞書の結果であり、6bitやC45一般の不可能性証明ではない。
7. **ゲージ不変性とキャッシュ実装の不変性を混同した。** V8 5×LUT4の`bit5 XOR bit6`持続タグを無制約に変えると、物理的には等価でも42,743個の時系列整合違反/3,015個のlow-only違反が起きる。修復された32ワード7行の候補でも15-batch rank proxy 7373→7373、生成KMB費用ゼロ差。ゲージの選び直しだけでT改善と主張不可。
8. **比較親が最新フロンティアでなかった。** この実験群は公開V8（33.1352130647、3,375T/往路）起点。既知の公開V9は3,372T/往路、33.13877。仮にV8から−1Tを実現しても最新の既知基準を更新しない。公式入力データ・回路family SHA・スコア数式を**同じ親**でpinすべき。
9. **PyTorch方策の小型ベンチは実GVQCCとは別問題。** 4入力3出力toyではPyTorch REINFORCEが45→14 CCX、同予算random15、深さ3 classical beam14でありNN固有の優位は未確認。KaggleのDQI復号器・逆平方根・ANGLEでは別の多段制約がある。

## 設計を改める

- **不可能性ガード**: `GF(2) polar-rank/2`下界が飽和した形式サブ問題は、同じ入出力空間・同じゲート範囲での削減学習を停止。ガードに使った仮定（独立formal変数・完全二次・余計な状態なし）を保存する。全体到達可能空間への推論に使わない。
- **候補生成器**: NNの出力は生のゲート真理値や128bit自由マスクではなく、既存回路の厳密同値変換候補（可逆入出力基底、rank-two因子交換、3点以上のXAG rank交換、AND共通項共有、pebblingスケジュール、ゲージ符号、Givens木・角度表）に限定する。非法な提案には厳密GF(2)制約/SATで最も近い可行候補へ投影し、違反は採用しない。
- **本当の受理ゲート**: 変更前後の*同じ回路family*で `FeMoCo e1/e2/Egap/λeff→15本KMB生成→Q=128局所上限→全合法アドレスの順逆ワード/zero scratch→全HMR枝の位相→DQI/invsqrt固定ファイルと全18ファイル統合→公式KickMix salt panels→公式得点式` を通したときのみscoreable。常に元18-file ZIP SHAを保存。物理only、formal local、proxy、native KMB、official scoreを別ステータス。
- **探索対象の優先順位**: (A) 飽和した27積ではなくHMR前の126/131積に対する**物理到達空間と非線形因子辞書を含む多出力再合成**、(B) 7bit物理PASSを維持する3セル編集＋原KMBへの安価な差分修復、(C) DQIの4,053回出現する42CCX核のcaller-aware rank交換（特にCX-only 2,651組）、(D) invsqrt 37Q→36Qの幅-コスト交換。各候補で単発局所縮約ではなく親KMB+可逆スケジューリングと公式コストを計測。
- **score optimization**: 最終採用関数は `score` の真の改善と検証PASS。学習の近似目的は探索候補の優先順位付けのみに用い、raw rankやsoft MSEを成功指標にしない。改善なしも明記して次の枝へ切替。

## 即時中止する反復

1. formal polar rank が飽和している16積・27積の同表現・同出力1T削減学習を繰り返すこと。
2. bank7単独rank15達成や4bit witnessのAND減を総合T減と解釈すること。
3. `e2`が20mHaを大幅に超える固定6bit辞書を何度も同じ教師/同じ連続局所更新で冷却すること。
4. 最新既知V9より低いV8の微小H2-only数値改善を「更新」と呼ぶこと。
5. 公式KMB生成不能のまま `lambda_eff` だけ最適化し成功を報告すること。

**この記録自体は新しい回路・スコアを生成しない。** 適用前の最低条件として次の改造の根拠・棄却理由に利用する。
