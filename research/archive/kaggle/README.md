# Kaggleのノートブック・提出・出力の記録

対象は [Google Quantum AI Verifiable Quantum Circuit Compilation](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation) の `geocpuresearch` 関連履歴。版を固定できる場合は `scriptVersionId` を残す。これは当時の会話・レシートから回収できた一覧で、Kaggleのログイン後の「My Submissions」全件エクスポートではない。

- [提出履歴（本人ログイン）](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/submissions)
- [公開順位表（ユーザー名で絞り込み）](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/leaderboard?search=geocpuresearch)
- [機械可読の版・結果一覧](notebook-submission-index.tsv)

| 版・提出 | Kaggleで確認された状態／根拠 | ローカル・出力情報 |
|---|---|---|
| [検証済み480 CCX削減 / gauge128](https://www.kaggle.com/code/geocpuresearch/gvqcc-verified-480ccx-gauge128) | ノートブック所在を[会話](https://chatgpt.com/c/6af8bd53-d7b4-83ec-b179-5054e4d5ec58?messageId=76d6fe80-43cb-52a5-a5ce-629eac49e98c)で確認。版番号と提出行の対応は未照合 | [完全ZIP v2](https://chatgpt.com/library?file_id=libfile_fde3_f-a651683dae648191983621dbe676fdc1_e9171c3d17a08191be76d9438ecb9078&account_id=personal)（約50.3 MB） |
| [GVQCC 821 score2 verified — 369715705](https://www.kaggle.com/code/geocpuresearch/gvqcc-821-score2-verified?scriptVersionId=369715705) | 提出受付済みと[当時の会話](https://chatgpt.com/c/6af8884d-9310-83e8-9f6a-85f6ad859ec4?messageId=22456ff5-f812-55e3-adda-9de6fb57b3ae)に記録 | Public採点値の対応行は未照合 |
| [GVQCC exact4096 gauge score2 — 369719696](https://www.kaggle.com/code/geocpuresearch/gvqcc-exact4096-gauge-score2?scriptVersionId=369719696) | 同じ[当時の会話](https://chatgpt.com/c/6af8884d-9310-83e8-9f6a-85f6ad859ec4?messageId=22456ff5-f812-55e3-adda-9de6fb57b3ae)で受付済み | Public採点値の対応行は未照合 |
| [QCC v27 — 369721985](https://www.kaggle.com/code/geocpuresearch/qcc-v27-4030-toffoli-coded-word-chemistry?scriptVersionId=369721985) | **Public 27.31512**, 2026-11-15 02:27 UTC 採点完了、のち選択済みと[当時の会話](https://chatgpt.com/c/6af96b11-0a24-83ee-8430-03e88e466d9c?messageId=0941c138-67ab-571d-a670-2a00df5bc799)に記録 | 化学4,030 Toffoli/片道。同版のまま命令609,579→306,105でも大半はCXなので採点上のToffoliは不変。[原票とコード](https://github.com/corcondor/gvqcc/tree/535450e428b674c8e35ee7afc43f5a07347f1d2b/graph_research) |
| [GVQCC score3 exact4096 invsqrt cache v2 — 369722797](https://www.kaggle.com/code/geocpuresearch/gvqcc-score3-exact4096-invsqrt-cache?scriptVersionId=369722797) | 受付済み、[報告時はPending](https://chatgpt.com/c/6af8bd53-d7b4-83ec-b179-5054e4d5ec58?messageId=9a40e7e7-d790-57b8-91ea-f4d48ea29a6c)。最終Public採点は未照合 | Output → `submission.zip`, 63,552,631 bytes, SHA-256 `5a3011d3f208a0bae3b1e1bfb9b763ac8c7201f4de35a74d772699949b971882`。逆平方根−1 CCX／Q46、DQI full4096／Q889 |
| [GVQCC score4 extra16 CCX v3 — 369731618](https://www.kaggle.com/code/geocpuresearch/gvqcc-score4-exact4096-extra16-ccx?scriptVersionId=369731618) | [当時の会話](https://chatgpt.com/c/6af8bd53-d7b4-83ec-b179-5054e4d5ec58?messageId=f0f72f11-c54b-5ace-a1a8-42fd0864e428)では実行96.1秒で成功、日次上限で受付されず | OutputのZIPは18ファイルの整合性と事前検証版のSHA一致を確認したとの記録 |
| [Antigravityフォーク v1](https://www.kaggle.com/code/geocpuresearch/qai-fewer-toffolis-same-qubits-lb-28-05784) | Kaggle実行成功。[過去に同じ版のOutputから回収](https://chatgpt.com/c/6af9c383-510c-83ee-aee9-e61e8a9e21cd?messageId=1bd1b5ac-a345-5589-ba54-45348ad9275f) | **Output** に `submission_dqi_peephole.zip`, `submission.zip`, `receipt.json` とログ。DQI SHA-256 `7de70ead999d2636664edc617ce82d0a42c348cf2e1cb96feda78a1f134193a5`。復元版ローカル28.070288381345、invsqrt合流版28.070348619369 |
| graph562 | [当時のKaggle公開順位の照合](https://chatgpt.com/c/6af9c383-510c-83ee-aee9-e61e8a9e21cd?messageId=2aff0b43-0c70-5386-a40d-3fde2ae97f69)：**Public 28.03163** | [ローカル28.074486840280528](https://chatgpt.com/library?file_id=libfile_fde3_f-0272506123e081919f4db94746837089_e9171c3d17a08191be76d9438ecb9078&account_id=personal) と [提出時レシート](https://chatgpt.com/library?file_id=libfile_fde3_f-cb34143885408191bd510c817bfedc72_e9171c3d17a08191be76d9438ecb9078&account_id=personal)。スコア差はDQI 1失敗の試算と整合するが実際の採点ログから失敗数を確認したものではない |
| 28.319 | 2026-11-19 UTC、**Kaggle提出一覧に28.319があると[所有者が明示](https://chatgpt.com/c/6aff2289-8a48-83ec-8d6d-9143d94e0e4c?messageId=a6d54a88-4aa8-4cd7-99b2-b91e15a635ed)** | Round 43ローカルは別に **28.31933595161014**。[Round 43報告](https://chatgpt.com/c/6afe7e59-f028-83ec-97f9-f95a21380d8f?messageId=b7dcf5a3-2d6b-5cf7-b5c9-e8af72936186)。ページの表示値は本人確認済み、Kaggle行IDとローカルZIPハッシュのひも付けは未照合 |

## 上流ノート・データ（参照用）

- [areebbb: QAI Fewer Toffolis, Same Qubits](https://www.kaggle.com/code/areebbb/qai-fewer-toffolis-same-qubits-lb-28-05784) と [syed3000: QCC circuit portfolio](https://www.kaggle.com/datasets/syed3000/vqcc-own-circuit-portfolio)。
- [masumhuq: per-task max composite 28.09](https://www.kaggle.com/code/masumhuq/qai-per-task-max-composite-28-09)。
- [maoxin123: 44-qubit invsqrt](https://www.kaggle.com/code/maoxin123/qcc-v27-a-44-qubit-invsqrt-on-the-28-09-frontier)。
- [alexchilton: 28.09 private salt（固定版 370114729）](https://www.kaggle.com/code/alexchilton/28-09-lb-which-circuits-survive-private-salt?scriptVersionId=370114729)、[28.23 private salt](https://www.kaggle.com/code/alexchilton/28-23-lb-which-circuits-survive-private-salt)、[24.94 verified portfolio 固定版 369763055](https://www.kaggle.com/code/alexchilton/24-94-lb-verified-three-task-portfolio?scriptVersionId=369763055)。

## 今回コピーできなかった範囲

現環境の公開ウェブ経由では上記の本人ノートブック・提出ページを直接取得できず、認証済みKaggle CLIも確認できなかった。この記録は版へのリンクと既存レシートを保存したもので、Kaggleにある全履歴、ノートブックソース、各版Outputのバイナリを再取得したものではない。第三者のノート・データは参照リンクのみ。過去取得ファイルと話者が違う場合は、Kaggle原本の版・著者・ダウンロードしたSHAと検証レシートを照合してから差分に加える。
