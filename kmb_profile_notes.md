# KMB v2 低メモリ集計と DQI 独立監査

## 今回確認した範囲

添付された gvqcc_dqi_opt.py は実際に読みました。元スクリプトは KMB 全体を kickmix の回路オブジェクトへ読み、KMX 全体へ変換していました。また、制御だけの参照も live と数え、条件付き R/HMR でも live を消し、INFO/DEBUG/PUSH/POP を除外した独自の命令番号を使っていました。

gvqcc_dqi_audit.py は、その出力を独立に確認するための別名の監査ツールです。ユーザーの別の v5 スクリプトを上書きしません。実際の dqi.kmb はこの環境にないため、ユーザーの 889 qubit 回路に対する結果はまだありません。

## 必要なファイルと実行

同じディレクトリに次の 3 ファイルを置きます。

- gvqcc_dqi_audit.py
- dqi_audit_scan.cpp
- kmb_profile.py

Python 標準ライブラリと C++17 対応の g++ が必要です。kickmix、NumPy、GPU は使いません。

旧 v4 と同じゲート番号で区間を確認する例:

    python gvqcc_dqi_audit.py --circuit /path/to/dqi.kmb.xz --index-mode legacy-v4 --scratch-start 840 --scratch-initial zero --snapshots 10500000,10530000,10539000,24000000 --window 10529400:10547601 --window-limit 20000 --out-dir dqi_audit_run1

scratch-initial zero は、課題が q840 以降をゼロ初期化する場合の明示的な仮定です。指定しない場合は unknown とし、ゼロとは仮定しません。任意の回路にゼロ初期化を推測して適用しないでください。

単独 .kmb、.kmb.xz、ZIP 内 .kmb に対応します。ZIP の場合:

    python gvqcc_dqi_audit.py --circuit submission.zip --member dqi.kmb --scratch-initial zero --index-mode legacy-v4 --out-dir dqi_audit_run2

入力を省略した場合、/kaggle/input 以下に dqi.kmb または dqi.kmb.xz が一つだけあれば選びます。複数候補がある場合は一覧を出して停止します。出力ディレクトリは新規作成し、既存の結果を上書きしません。

## 出力

| ファイル | 内容 |
|---|---|
| profile.json | KMB ヘッダー、最大 ID、レジスタ概要、命令ヒストグラム、入力 SHA-256、パケットサイズ |
| scan.json | 保守的な scratch 状態の集計、条件スコープ数、区間最大値、静的命令数 |
| events.jsonl | 指定区間の全命令、指定位置のスナップショット、INFO_TAG、最大値更新 |
| run_summary.json | 入力パス、SHA-256、初期状態の仮定、番号の定義、コードの SHA-256、制限事項 |
| compile.log / scan.log | コンパイルと C++ 実行の診断出力 |

イベントには、すべての opcode を数えた kmb_index と、旧 v4 の legacy_v4_gate_index の両方を出します。既定の index-mode は kmb です。旧 v4 の位置をそのまま指定するときは legacy-v4 を明示してください。

ウィンドウは START 以上 END 未満です。CX、古典ビット操作、PUSH/POP、INFO/DEBUG も除外しません。明示条件の bit ID、active な PUSH の元 bit ID と PUSH の kmb_index も記録します。PUSH はその時点の値を保持するため、後で同じ bit を上書きしても条件の意味は変わりません。

記録上限に達した場合は先頭から指定件数までを保存します。scan.json の window.eligible_operations と window.recorded の差で切り詰めを確認できます。INFO_TAG は先頭 256 バイトを hex で保存し、元の長さも記録します。Z_POW の角度は元の 16 バイトを hex で保存します。

## 状態の意味

possibly_nonzero は、各量子ビットがゼロでない可能性を過大評価する、保守的な近似です。量子ビットの物理的な生存期間や、レジスタを安全に削除できることの証明ではありません。

- X はターゲットを possibly_nonzero にします。X の二重適用による相殺までは追いません。
- CX/CCX は制御がゼロと分かるときだけ、ターゲットへの影響がないと判定します。制御側を参照しただけでは、制御を非ゼロ扱いに変えません。
- Z/CZ/CCZ/Z_POW などの位相操作は、ゼロの量子ビットを非ゼロ扱いに変えません。
- 無条件 SWAP は両側の状態を交換します。条件付き SWAP は両分岐の和を取ります。
- CSWAP は制御がゼロなら変化なし、それ以外は交換される両側を保守的に合併します。
- R/HMR は、明示条件がなく、PUSH のスコープ外にあるときだけゼロと確定します。条件付きでは実行されない分岐も残します。
- 古典条件の真偽は計算しません。PUSH の値も unknown として扱います。

touched_since_unconditional_reset は、最後の無条件 reset 以降に命令の量子ターゲットとして参照された履歴です。こちらも liveness ではありません。

レジスタ共有は、将来の読出し、古い値の保持、古典条件、HMR の結果と位相補正を確認したうえで別途検証してください。数値が小さくなったことだけでは公式回路の正しさを判断できません。

## メモリ

KMB の列形式を、固定サイズのバッファで読みます。命令ごとの Python オブジェクトや回路全体の KMX テキストは作りません。圧縮入力は一時 KMB ファイルへストリーム展開し、処理終了時に削除します。したがって圧縮入力では、非圧縮 KMB 一つ分の一時ディスク領域が必要です。

メモリは主にバッファ、量子ビットごとの状態、表示上限、条件スタックで決まり、全命令数に比例する回路配列はありません。対応上限は 100 万 qubit、scratch 1 万、条件スタック深さ 65,536 です。上限を超える場合は停止します。

## 単独の形式確認

C++ の状態解析が不要なら、Python の profiler だけを実行できます。

    python kmb_profile.py submission.zip --member dqi.kmb --output dqi_profile.json --progress

この場合は ZIP 内の KMB をディスクへ展開しません。分離したターゲット列の重複検査には ZIP を再読込するため、解凍処理を複数回行います。基本バッファは 1 MiB で、--chunk-kib 64 などで変更できます。

形式検査には、バージョン、パケット順序・長さ、命令件数、定義済み opcode、最大 ID、INFO_TAG オフセット、2/3 qubit ゲートの異なるターゲット、ZIP CRC を含みます。公式 verifier や回路の意味的正しさの検証は行いません。

## 検証

    python -m unittest -v test_kmb_profile.py

profiler の 23 テストが成功しました。公式仕様の 4 つの hex サンプル、ZIP、短い read、バッファ境界、切り詰め、件数・ID の矛盾、同一ターゲット、未知 opcode、入力非変更などを含みます。

独立した profiler CLI の実測:

| 合成入力 | 命令数 | 非圧縮バイト数 | 時間 | 最大 RSS |
|---|---:|---:|---:|---:|
| 単独 KMB | 200,000 | 2,600,288 | 0.075 秒 | 16.000 MiB |
| 単独 KMB | 2,000,000 | 26,000,288 | 0.741 秒 | 19.230 MiB |
| ZIP 内 KMB | 2,000,000 | 26,000,288 | 0.840 秒 | 20.398 MiB |

Python 3.12.14 / Linux、同じ CCX を繰り返す合成データでの測定です。実際の DQI の測定でも、別環境への性能保証でもありません。圧縮率も実際の DQI を代表しません。

詳細は kmb_profile_validation.json、形式例は kmb_profile_sample.json にあります。形式例は公式の “A Circuit with Every Operation” の結果で、ユーザーの DQI ではありません。

## 一次資料

- [Qualtran KMB binary format](https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_binary_format.md)
- [Qualtran Kickmix instructions](https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_instructions.md)

2026-11-14 に内容を確認しました。KMB version 2 以外を推測で読み取りません。
