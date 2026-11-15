#!/usr/bin/env python3
"""Bind the final score5 delivery to completed verification and ZIP receipts."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--delivery',type=Path,required=True)
    a=p.parse_args();root=Path(__file__).resolve().parent
    score=json.loads((root/'score5_final_scorecard.json').read_text())
    package=json.loads((root/'score5_final_worker_check.json').read_text())
    full=json.loads((root/'score5_dqi_final_full_verification.json').read_text())
    old=json.loads((root/'score4_dqi_full_verification.json').read_text())
    assert full['status']=='PASS' and full['verified_shots']==102400
    assert full['circuit_sha256']=='e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355'
    assert package['candidate_dqi_sha256']==full['circuit_sha256']
    assert package['output_sha256']==score['candidate']['zip_sha256']
    source=Path(package['output']);assert sha(source)==package['output_sha256']
    a.delivery.mkdir(parents=True,exist_ok=True)
    target=a.delivery/'score5_submission.zip'
    if target.exists():assert sha(target)==package['output_sha256']
    else:shutil.copyfile(source,target)
    assert sha(target)==package['output_sha256']
    metrics=score['dqi_metrics']
    report=f'''# score5: 検証済みの追加10 CCX削減

## 完成した提出用ファイル

新しい二つの等価変換で **10 CCX** を追加削減し、分母ゼロ修正版と従来の16 CCX削減を統合した。全体の量子ビット数は889である。提出用ZIPの18メンバーすべてのSHA256とCRCを検査し、DQI以外の17メンバーは元の検証済みポートフォリオと一致した。

| 指標 | 前回のscore4 | 今回のscore5 |
|---|---:|---:|
| 静的Toffoli-like | {old['max_toffoli_count']:,} | {full['max_toffoli_count']:,} |
| 公式検証の平均Toffoli | {old['toffoli_count']:.9f} | {full['toffoli_count']:.9f} |
| 量子ビット数 | {old['num_qubits']} | {full['num_qubits']} |
| DQI費用（小さいほど良い） | {old['score']:.4f} | {full['score']:.4f} |
| ローカル総合スコア | {score['previous_score4_local_combined_score']:.10f} | **{score['local_combined_score']:.10f}** |

総合の実測増分は **{score['local_combined_increase']:.10f}**。大幅改善とは表現しない。これは公式コードをローカルで実行して得た各費用から計算した値であり、新しいKaggle Public Scoreではない。今回の競技提出は行っていない。

ZIP: `{target.name}`（{package['output_bytes']:,} bytes）

ZIP SHA256: `{package['output_sha256']}`

DQI SHA256: `{full['circuit_sha256']}`

## 実装した二つの縮約

1. 共通制御・同じtargetを持つ二つのCCXを因数分解し、8 CCXを削減した。`CCX(a,b,t); CCX(a,c,t)` を `CX(b,c); CCX(a,c,t); CX(b,c)` に置き換える。targetや制御がdirtyでも成り立つ。跨ぐゲートや測定は個別に可換性を確認した。
2. 最後の書込みの後に使われない量子ビットを早めにHMRし、書込みを測定結果に条件付けたCZへ変換して2 CCXを削減した。`M_m X_t^f = (-1)^(m f) M_m` を使用する。古典ビットの途中の読み書きを壊さないよう、測定結果は新しい2ビットに保持し、元のHMR位置で初めて元の宛先へコピーする。

従来の16 CCX削減を含めると、分母ゼロ修正版ebfbからは26 CCXの削減である。score4との差には別作業で完成した分母ゼロ修正も含まれるため、「今回の新規10」と「静的合計差{old['max_toffoli_count']-full['max_toffoli_count']}」を区別する。

理論と一次資料の対応は `score5_theory.md` に記載した。MBUndoのinterval MBUと、reversible pebbling/Reqompを実回路の契約に合わせて検討した。汎用ZXやCartan分解を通しただけで同じ削減が得られたとは主張しない。

## 検証

- 最終DQIは公式デフォルト **102,400ケース PASS**。値エラー **{full['value_errors']}**、位相エラー **{full['phase_errors']}**。
- seed未指定、salt空文字、信頼度パラメータ `log2_delta=-128` を維持した。
- 独立レビューが基底・測定結果ごとの等価性、途中の古典ビット使用、変更箇所と実KMBの一致、対象外の全10オペランド列とレジスター宣言の保存を検査した。
- 以前の16 CCX統合については、固定16,384入力と既知回帰512入力の計16,896ケースで、入出力・位相・古典値のハッシュが前版と一致し、各実行のToffoli差が16だった。
- 変更していないinverse-square-rootは既存の200,540,928ケースPASS、化学は78,080ケースPASSをメンバーのハッシュ一致で引き継ぐ。これらを今回再実行したとは主張しない。

新しいKMBでは公式デフォルトの入力サンプルが変わる。HMRの順序変更では乱数列の対応も変わる。したがって、二つのデフォルトrunの平均Toffoli差を、そのまま代数的に証明した削減数とは扱わない。

## 残る失敗例とスコアの感度

分母がゼロになる既知のクラスは統合した修正版で処理できる。一方、node13の分子ゼロの既知入力は残っている。有限ケースでのPASSは全入力に対する正解の証明ではない。今回の等価縮約はこの性質を引き継ぐ。

DQI費用は `R(error_upper) × Q² × mean_Toffoli`、総合は三つの参照費用比の幾何平均である。平均Toffoliと他の費用を今回の値に固定すると、102,400ケース中の失敗数に対する感度は次の通り。

| 仮定したDQI失敗数 | 計算上の総合スコア |
|---:|---:|
'''
    for row in score['error_count_sensitivity']:
        report+=f"| {row['total_dqi_errors']} | {row['combined_score']:.10f} |\n"
    report+='''
この表は感度計算であり、追加の実測やKaggleでの失敗数の予測ではない。既知の分子ゼロ修正は後続41インターフェースへ伝播し、少なくとも1968 Toffoliを追加する現構成になるため、今回のポートフォリオには採用していない。

## 実装・検証したが採用しなかった幅削減

子ノルムを一時消去して借り、後で再計算する逆元部品を実装した。局所的にはQ889→883・追加180 CCXを達成し、GF64²の全4096組とnativeの512入力×2seedを検査した。実KMBの正逆二つのブロックに組み込むところまで実施した。

しかし別のcarry24+flag1+product24区間等が残り、回路全体はQ889のままだった。この中間版はToffoliが180増えて費用が悪化するため、提出ZIPには含めない。`score5_dqi_width_report.md` に部品・実バイト照合・残ったピークを保存した。

化学側も最新4030-loaderの数値表からC44→C43と離散角度更新を探索したが、20 mHa制約を満たす改善にはならなかった。このZIPの化学は既に検証済みの4033-loader版である。存在しない4030-loaderの組合せの費用を、このZIPのスコアへ算入していない。

## 再生成

標準Pythonだけで、対応する既知SHAの元ポートフォリオZIPから再生成できる。

```bash
python score5_final_worker.py --source /absolute/path/input.zip --output /absolute/path/submission.zip --receipt /absolute/path/receipt.json
```

受理するDQIは9a82、ebfb、6a、e4のピン留めされた完全ハッシュのみ。未知の入力は拒否する。DQI以外の17メンバーを保持するので、新しい化学版を含む対応済み親ZIPにも同じ縮約を適用できるが、保持した部品の検証結果を自動で新規認定する処理ではない。既存ファイルを上書きせず、競技提出も行わない。

実測の再計算は `python score5_scorecard.py`。一次証拠は `score5_dqi_final_full_verification.json`、`score5_final_worker_check.json`、`score5_final_scorecard.json`。大きなKMB全体をソースZIPへ重複格納せず、ハッシュ固定の再生成ワーカーと完全なパッチ・証拠を収録した。
'''
    (root/'score5_results.md').write_text(report)
    record=dict(status='FINAL_EXACT_REWRITES_OFFICIAL_AND_PACKAGE_VERIFIED',
                archive=dict(path=str(target),sha256=sha(target),bytes=target.stat().st_size),
                candidate_dqi_sha256=full['circuit_sha256'],new_ccx_removed=10,
                total_ccx_removed_vs_projective_norm=26,num_qubits=full['num_qubits'],
                local_combined_score=score['local_combined_score'],
                previous_score4_local_combined_score=score['previous_score4_local_combined_score'],
                official_dqi_shots=full['verified_shots'],value_errors=full['value_errors'],phase_errors=full['phase_errors'],
                other17_members_preserved=True,width_experiment_adopted=False,
                known_numerator_zero_failure_remains=True,
                new_submission_performed=False,new_public_score=None,
                receipts={name:sha(root/name) for name in [
                    'score5_dqi_final_full_verification.json','score5_final_worker_check.json',
                    'score5_final_scorecard.json','score5_dqi_failure_fanin_review.json',
                    'score5_dqi_hmr_independent_review.json','score5_results.md']})
    (root/'score5_delivery_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
