# GVQCC 会話・Kaggle・成果物アーカイブ

対象は Google Quantum AI の Verifiable Quantum Circuit Compilation（GVQCC）のみです。別のセッションから成果や失敗を引き継ぐときは、まず既存の[横断研究ノート](../2026-11-20_cross_session_synthesis.md)と[実験・スコア台帳](../2026-11-20_evidence_ledger.json)を参照してください。このディレクトリはその裏取りに使う資料の入口です。

| 探す内容 | 入口 |
|---|---|
| Round 48 DQI：45組の共同合成と18組の多段候補の実測 | [再現コード・結果JSON](experiments/round48-dqi-windows/README_experiment.md) |
| 多段 XOR–AND の論文・過去の成功例・再合成計画 | [多段XAG研究ノート](multistage-xag.md) |
| 会話本文、日付、元メッセージ、取得できなかった箇所 | [チャット索引](conversations/README.md) / [取得範囲 JSON](conversations/coverage.json) |
| Kaggleのノートブック・版番号・提出・出力の履歴 | [Kaggle索引](kaggle/README.md) / [版・結果 TSV](kaggle/notebook-submission-index.tsv) |
| 評価ZIP、再現コード、反例、検証票、スコアカード | [成果物索引](artifacts/README.md) / [Library一覧 TSV](artifacts/library_inventory.tsv) / [検証票の抜粋](artifacts/receipt_extracts.jsonl) |
| 手元で照合した旧ZIPの全メンバーのSHA-256とスコアカード | [旧版の検証資料](workspace-evidence/) |

- 会話本文は取得可能な表示済みのユーザー・アシスタントメッセージ。内部ログ、認証情報、取得できない本文、添付バイナリは含みません。本文の欠落・切り詰めは索引を参照してください。
- Kaggleにある **28.319** は本人確認の表示値。Round 43 の **28.31933595161014**、Round 48 の **28.32145634974874** は別に記録したローカル評価です。候補・ハッシュ・検証範囲・実提出の有無を取り違えないこと。
- Kaggleのノートブックや出力の全版をエクスポートしたわけではありません。参照可能な版を索引に残しています。大容量ZIP本体は既存のLibrary等へのリンクを使用し、このGitツリーにはコピーしていません。リンク先は別途元アカウントの権限が必要な場合があります。
- 回路ファイルの内容を変更したり、コンペに新たに提出したりする作業ではありません。
