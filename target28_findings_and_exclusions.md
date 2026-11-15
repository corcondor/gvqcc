# 28点目標：既存知見との照合（2026-11-15）

## 状態
新しい28点超え候補は未完成。今回の2探索から新しい採用回路、公式PASS、Public Scoreは得ていない。
比較基準はscore8のローカル27.32784222155277。Public Scoreと混同しない。
他条件一定で28へ届くには3課題費用の積を0.92969807295417倍以下（約7.03019%削減）にする必要がある。

## 照合した系統
- research/score-continuation-2026-11-14 @084c7accbc70b10c91508f68f8b4c9ab17017916：score8、score9 rebatch、既存算術・位相・資源監査。
- main @6a2d7a731df76af1271612cf0efbf65fd99405a2：treeを比較。対応する手元報告も読んだが、全ファイルがこのcommitとbyte同一とは確認していない。
- improve/joint-weights-20261115-4020ae2c @282ddf583359290ed61dfca37651c7ae0c061295：FINDINGS_REPORT.md、chem_next_public4030_report_ja.md、chem_next_public4030_loader_analysis_ja.md、dqi_next_arithmetic_report.md、dqi_next_conditional_phase_fixture_review.md、invsqrt_next_phase_report.mdを取得・確認。
全リポジトリの全ファイルを精読したという主張ではない。

## 同じ条件では再探索しない項目
| 項目 | 既存結果・注意 | 再検討する場合に必要な変更 |
|---|---|---|
| 化学303 temporary Q | 公式内部見積もり。提出ANGLEで内側QROMを任意交換するAPIはない | 実際に提出できるパラメータ・構造を変更 |
| J=4 rebatch | 旧5434、score9で5197 CCX/pass。Q419でも4030版より悪い | 既存532分割・care域rank探索とは異なる共有構成。改善境界4170、28単独目標3643以下 |
| 化学角度表 | NPZメタデータと実回路復元値に473語差 | 実回路復元1220×75表を固定しSHA照合 |
| W/H2_I再フィット | 別枝でlambda_eff46.90965630568201、cost294887890.9764710、78080 shots PASSの記録あり | この既存改善を新規成果に数えない。採用時は実物と検証receiptを照合 |
| 公開4030積併合 | 第1〜14ローダー2703積、第0の3区間212積に共通制御・出力方向なし | 別の共有非線形積を導入する再合成等 |
| DQI GF12積 | 既に42 CCX。54/63からの改善と誤認しない。rank39の出典は次数11 | 正しい次数12と実operand契約で合成・検証 |
| DQI逆元 | 65T既導入。二重計上しない | 現行実体より改善 |
| DQI局所幅削減 | GF64固定scalar Q12→10、特定逆元pair Q889→877は部品結果。全体889ピーク残存 | consuming product、nested norm、phase helpersを含む全体lifetime改善 |
| DQI失敗 | N=0/D=0 chart例外が旧回路にもある。有限default PASSで解決としない | 既知反例・独立固定stream・位相・scratchを検証 |
| invsqrt位相LP | 順方向5239候補、選抜LP、1-AND基底探索は既実施で改善なし | 基底・算術・係数表・切断点等を明示して変更 |
| invsqrt退役 | q42/q45の特定切断点で二次復元は反証あり | 高次再生成または別切断点、全ピークと追加T予算の確認 |
| CCZ→7T | invsqrtでは7T/4=1.75 Toffoli換算、native CCZ=1。DQI/化学ではZ_POW禁止 | 接続先込みの全費用改善を示す |
| 条件付き位相scanner | BIT_STORE0/1/INVERT opcode誤りが修正され22fixtures PASS | 修正前production negativeを証拠に使わない。hitは独立exact replay |

局所探索の負の結果を一般量子回路の下限へ拡張しない。HMR位相、到達可能領域、任意target契約を混同しない。

## 今回の実験と既存研究との重複
1. target28_resource_screen.py / JSON：
   公式費用式で22,565 shapeを比較。paddingと直接和regroup、同じloader費用・lambdaという条件で改善0。
   **後から別枝のchem_next_regroup_resources.py（594設定）を確認した。方向は重複している。**
   今回は範囲拡張であり、新原理・候補回路ではない。今後同種screenを繰り返す優先度は低い。
2. target28_affine_ccz_search.py / JSON：
   既存score8の最初の2因子が単一wireである探索を拡張し、2〜4 wire parityと1〜4 wire parity、第三因子任意live parityを許容。
   10区間、4221合法sample入力、207016 queryでhit0。乱択・時間制限探索であり全候補網羅ではない。
   別枝の一般角Z回転LP／1-AND基底とは対象が異なるが、これも改善回路を生成していない。
   6bit全64入力の人工三次位相でpositive controlを手動実行しtruth vector一致を確認した。これはproduction改善ではない。

## 文献調査の到達点
ユーザー指定CCZ図とClassical Simulability of Quantum Circuits with Shallow Magic Depthは同じ論文。
arXiv2409.13809v2の参考文献は61件。主論文と多数の参照本文を取得したが、**全参照文献の精読は未完了**。
とくにSelingerのT-depth one（1210.0974）とGidney/JonesのCCCZ six T（2106.11513）は本文確認。
T-depth削減、古典シミュレーション高速化、固定状態準備の圧縮を、そのまま大会の任意入力回路費用削減とは扱わない。
別の表リンクはThe resource cost of magic in a code block、grapheneリンクは物性実験であり、同じ回路合成論文ではない。
後二者の参考文献も含め「全部読んだ」とは報告できない。

## 次の判断
28点目標に対して微小lambda polishだけでは足りない。
最優先はDQIの既知chart例外を含む正しさと、全幅ピークを同時に変える構成、
または化学の角度表と専用ローダーを共同設計する構造変更。
実装前に対象SHA、既存失敗との差分、公式費用での損益境界を記録する。
今回のファイルは研究記録であり、提出ZIPの更新ではない。
