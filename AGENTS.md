# DQI研究の必須方針 — 316k系統のみ

2026-11-28 JST、リポジトリ所有者の明示指示に基づく。以後のDQI関連の全セッション・AIエージェント・PRに適用する。所有者が明示的に変更するまで有効。

## 非交渉条件

- **316k系統の完全DQI回路のみを開発対象とする。** 410k、414k、419k、百万ゲート級等の別系統への切り替えは禁止。正当性優先、幅削減、比較実験という理由でも、別系統を新規開発対象にしない。
- 最新の316k系の成果をGitHubで確認して引き継ぐ。旧ドナーに戻って実装をやり直さない。元ドナー（SHA-256 `4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52`）は系譜・検証の参照点であって、常に採用する作業ベースではない。
- 現時点の参照点は [#247](https://github.com/corcondor/gvqcc/pull/247) の900Q全回路（SHA-256 `8b9d09f87692f59baaeb399d96650db9389835f23be5c2ab93be4d86259bc6ab`、平均316130.0954、静的318333）。強制反例499/1024、通常102400ショット1件失敗が残る。今後の検証済み316k系後継版があればそちらを優先する。
- 最新の数学・実装（例：#245の射影復号、#246の半次数Bézout・加法FFT、既存のHMR・有限体乗算・可逆履歴管理）は316k系本体へ統合する。高費用系統の既存資料は数学や部品の参照に限り利用可。本体の置き換え、特殊オラクルの高費用な単純追加、外部の入力依存チャート選択を行わない。
- **完成条件は同一の全回路で同時達成すること：900Q以下、採点分布における平均有料ゲート316000未満、値・位相・補助ビット・公開マスクのエラー0。** 全合法入力に対する数学的正当性を追求し、有限サンプルのPASSだけで全域保証とは呼ばない。
- Vercel/KickMixで実際に生成した全KMBを検証する。元の70シンドローム語から位相処理、逆計算まで一体化する。保存済み反例、重み0〜35、特殊極・低重み、零・one-hot・密なマスク、独立の強制反例と採点分布を含める。公式検証器102400ショットと既定・独立saltの検証、同一条件の比較、費用・幅・命令数・実スコアまたは明示した推定値を記録する。Leanの証明と厳密CIを省略しない。
- 部分回路、数学参照実装、別系統の全回路、未検証の予測値を、316k系全回路の修復完了・スコア改善として報告しない。条件未達なら明記し、同じ316k系の修正を続ける。ユーザーの明示許可なく提出や競技回路の置換はしない。
- 実験前に作業ベースのSHA-256と適用する既存修正を記録し、実験後に新しい全回路のSHA-256、ソース、実測JSON、反例、Leanの結果、再現手順を保存する。最新成果の再実装や無関係な探索で時間を浪費しない。

## English summary for automated coding agents

**Only develop the 316k DQI lineage.** Use its newest compatible verified checkpoint, currently PR #247, not the historical donor as a default and never a 410k/414k/419k or million-gate replacement. Reuse existing mathematical and native-circuit advances by integrating them into the 316k decoder itself. The same full syndrome-to-phase-to-syndrome native KMB must satisfy Q <= 900, mean paid gates < 316000, and zero observed restoration/phase/ancilla/public-mask errors on mandatory native regression and official verification, with strict Lean evidence for the underlying mathematics. Do not claim a component, a costly substitute, or an external chart-selected replay is the requested result. Preserve the pinned comparison and artifacts. This directive supersedes conflicting historical research goals for DQI; only the repository owner may relax it.
