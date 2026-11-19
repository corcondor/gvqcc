# GVQCC 成果物索引（2026-11-19 UTC）

- [Library 成果物一覧](library_inventory.tsv): 565件、Library ID単位で重複排除。日付はUTC。ZIP・ソース・スコアカード・検証記録を元の保存場所へリンクする。候補名で見つけた索引で、ファイル内容は全件確認していない。一般名の提出ZIP 12件はQCC帰属未確認のため除外した。
- [スコアカード・マニフェスト・提出記録の抜粋](receipt_extracts.jsonl): 95件。元JSONの全ページを読み、数値・検証結果・ハッシュ等の関連フィールドを最大60個ずつ抽出。原本そのものではない。主に100 kB以下のJSONを対象にした。
- 大容量ZIPのバイナリ本体や、Libraryにない古いローカル成果物は、このディレクトリには複製していない。ZIPは同名別内容があるため、Libraryリンクと、元マニフェストにあるSHA-256で区別する。

## 比較用の主要版

| 系列 | 記録 | 検証と制約 |
|---|---:|---|
| Round 42 | 28.31653978572411 ローカル | [評価ZIP](https://chatgpt.com/library?file_id=libfile_fde3_f-beee21da4c6c819192c377bd1a67c0c9_e9171c3d17a08191be76d9438ecb9078&account_id=personal)。DQI標準2パネル各102,400、値・位相エラー0 |
| Round 43 | 28.31933595161014 ローカル。別途、Kaggle画面に28.319があると本人確認 | [評価ZIP](https://chatgpt.com/library?file_id=libfile_fde3_f-7b7a72e6e4f08191b73d1c1d935f6699_e9171c3d17a08191be76d9438ecb9078&account_id=personal)・[スコアカード](https://chatgpt.com/library?file_id=libfile_fde3_f-4b8b04dd7b788191a81591e759809ca5_e9171c3d17a08191be76d9438ecb9078&account_id=personal)。固定反例が残る |
| Round 44 | 28.321035838481225 ローカル | [評価ZIP](https://chatgpt.com/library?file_id=libfile_fde3_f-4465bcfca7548191bf179d3ae908582f_e9171c3d17a08191be76d9438ecb9078&account_id=personal)。標準2パネル0エラー、固定9件すべてで値エラー |
| Round 45 化学XOR修復 | 28.14354135943956 ローカル | [評価ZIP](https://chatgpt.com/library?file_id=libfile_fde3_f-045049f440a08191a54c0e07eebf372b_e9171c3d17a08191be76d9438ecb9078&account_id=personal)。14,986 Toffoliの化学は任意標的XORを修復。DQIはRound 44同一 |
| DQI 1,018Q + 化学14,858 | 25.0106543638087287 ローカル | [スコアカード](https://chatgpt.com/library?file_id=libfile_fde3_f-ec6b49d3df888191a96d9190f24a93ff_e9171c3d17a08191be76d9438ecb9078&account_id=personal)。最終ハッシュでdefault値エラー7、notebook値エラー5 |
| 修復v15（922Q） | 26.69266644620627 ローカル | [スコアカード](https://chatgpt.com/library?file_id=libfile_fde3_f-00bf42a609948191a4bffb59071e29d5_e9171c3d17a08191be76d9438ecb9078&account_id=personal)。固定・構造1,604ショットと標準2パネルでエラー0 |
| Round 47（1,000Q） | DQI診断、総合実測なし | [研究ZIP](https://chatgpt.com/library?file_id=libfile_fde3_f-9957169defb08191b45c4f9844fea463_e9171c3d17a08191be76d9438ecb9078&account_id=personal)。594ショットでエラー0。現構成の楽観上限は約26.8726 |
| Round 48 | 28.32145634974874 ローカル | [評価ZIP](https://chatgpt.com/library?file_id=libfile_fde3_f-24037822eb04819182c20b6c42644568_e9171c3d17a08191be76d9438ecb9078&account_id=personal)。16 Toffoli減、default 102,400エラー0だが既知の固定反例を継承 |
| 拡張修復v11（1,351Q） | 20.274036887539708 ローカル | [ZIP](https://chatgpt.com/library?file_id=libfile_fde3_f-2b0303d90a488191bb83298edde9806b_e9171c3d17a08191be76d9438ecb9078&account_id=personal)・[マニフェスト](https://chatgpt.com/library?file_id=libfile_fde3_f-9c89dec2b200819199fcb9597d993a13_e9171c3d17a08191be76d9438ecb9078&account_id=personal)。標準2パネル＋追加18,210試行（合計223,010）でエラー0。下位幅版の回帰検証に使える。未提出 |

Kaggleの実測値、公式方式によるローカル実測、固定反例の検証、費用式の試算は別のもの。いずれも、検証に使った回路ハッシュを別候補へ引き継がない。
