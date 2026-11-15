#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Bind the score4 exact rewrite, official verification and packaged bytes."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parent
WORK=Path('/workspace/scratch/3815fb5fae06')
RUN=WORK/'score4_dqi_fanout16'
OUT=WORK/'score4_submission'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def main():
    old=json.loads((ROOT/'score3_dqi_full_verification.json').read_text())
    new=json.loads((RUN/'official_verification.json').read_text())
    package=json.loads((ROOT/'score4_package_build_receipt.json').read_text())
    binding=json.loads((ROOT/'score4_dqi_guard_binding.json').read_text())
    baseline=json.loads((ROOT/'score3_submission_manifest.json').read_text())
    assert new['status']=='PASS' and new['verified_shots']==102400
    assert new['value_errors']==new['phase_errors']==0
    assert new['seed'] is None and new['salt']=='' and new['log2_delta']==-128
    assert new['verifier_sha256']==old['verifier_sha256']
    assert new['circuit_sha256']==package['candidate_dqi_sha256']==binding['candidate_sha256']
    assert binding['exact_unconditional_toffoli_reduction']==16
    assert binding['all_replacement_blocks_match_independent_proof']
    assert binding['all_other_operation_columns_byte_identical']
    assert package['all_member_sha256_and_crc_pass'] and package['member_count']==18
    assert package['preserved_other_member_count']==17
    archive=OUT/'submission.zip'
    assert sha(archive)==package['zip_sha256']
    pins={r['name']:r['sha256'] for r in baseline['members']}
    for row in package['members']:
        assert row['sha256']==(new['circuit_sha256'] if row['name']=='dqi.kmb' else pins[row['name']])
    for source,name in [(RUN/'official_verification.json','score4_dqi_full_verification.json'),
                        (RUN/'rewrite_certificate.json','score4_dqi_rewrite_certificate.json'),
                        (RUN/'before_profile.json','score4_dqi_before_profile.json'),
                        (RUN/'after_profile.json','score4_dqi_after_profile.json')]:
        shutil.copyfile(source,ROOT/name)
    reduction=old['score']-new['score']
    percent=100*reduction/old['score']
    summary=dict(status='EXACT_REWRITE_AND_FULL_OFFICIAL_AND_PACKAGE_PASS',
                 baseline_dqi_sha256=old['circuit_sha256'],candidate_dqi_sha256=new['circuit_sha256'],
                 additional_unconditional_ccx_removed=16,added_cx=32,
                 quantum_width=889,classical_bits=208087,
                 static_toffoli_before=old['max_toffoli_count'],static_toffoli_after=new['max_toffoli_count'],
                 mean_toffoli_before=old['toffoli_count'],mean_toffoli_after=new['toffoli_count'],
                 official_cost_before=old['score'],official_cost_after=new['score'],
                 official_cost_reduction=reduction,official_cost_reduction_percent=percent,
                 verification=dict(status='PASS',shots=102400,value_errors=0,phase_errors=0,
                                   seed=None,salt='',log2_delta=-128,verifier_sha256=new['verifier_sha256'],
                                   receipt='score4_dqi_full_verification.json'),
                 archive=dict(path=str(archive),sha256=package['zip_sha256'],bytes=package['zip_bytes'],
                              members=18,other17_byte_identical=True,sha256_and_crc_pass=True),
                 unchanged_component_receipts={k:baseline['official_receipts'][k] for k in ('invsqrt','dfthcsos')},
                 all_component_official_verifications_pass=True,
                 new_kaggle_submission_performed=False,new_public_score=None,
                 latest_prior_public_scores=dict(score3_369722797=27.28236,
                                                 v27_exact4096_369723885=27.28543,
                                                 selected_baseline=27.30683),
                 prior_public_score_source='Observed signed-in Kaggle submission UI, 2026-11-15 UTC',
                 caution='Exactly16 unconditional CCX are removed on every execution. The two default official runs use different hash-derived inputs; their measured mean difference is not the exact structural16.',
                 no_new_qrom_or_invsqrt_gain_claimed=True)
    (ROOT/'score4_delivery_manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
    report=f'''# Score4: 追加16 Toffoli削減、公式検証PASS

提出済み score3 のDQIから、**無条件CCXを新たに16個削減**した。これは以前の480個削減およびinvsqrtの1個削減への上乗せである。量子ビット数889と古典ビット数208,087は同じ。追加した32個のCXはToffoli費用に含まれないため、総命令数は16増える一方、採点対象のToffoli数は16減る。

## 実測結果

| 指標 | score3 | score4 |
|---|---:|---:|
| 静的Toffoli系ゲート数 | 382,934 | 382,918 |
| 公式平均Toffoli | {old['toffoli_count']:.12f} | {new['toffoli_count']:.12f} |
| 量子ビット | 889 | 889 |
| 公式DQIコスト | {old['score']:.6f} | {new['score']:.6f} |
| 値エラー / 位相エラー | 0 / 0 | 0 / 0 |
| 公式検証ケース | 102,400 | 102,400 |

公式コストは{reduction:.6f}、{percent:.9f}%低下した。検証器は変更せず、既定のseed、salt、confidence（log2_delta=-128）で実行した。検証時間は{new['verify_seconds']:.3f}秒。両回路のハッシュに応じて検証入力が変わるので、平均Toffoliの実測差と、厳密な回路上の16個削減は分ける。

## 書き換え

無関係な測定や古典操作を跨いで可換なCCXを移し、次の恒等式を適用した。

```text
CCX(a,b,t); CCX(a,b,u)
  -> CX(t,u); CCX(a,b,t); CX(t,u)
```

任意の初期値を持つt,uでも両方へ同じ積abをXORする。8区間の16組に適用した。従来passは測定を一律の境界として扱ったため、今回の候補を除外していた。新passは各中間ゲートの可換性をチェックし、HMR/resetがCCXの3本のwireと独立な場合だけ跨ぐ。測定結果や位相補償を削っていない。

## 等価性と実ファイルへの結合

1. 4量子ビットの16基底列で、符号を含む恒等式を確認した。線形性から任意の重ね合わせと参照系とのエンタングルメントを含む。
2. 別実装で、先行置換を反映した局所回路上の16移動を再検査した。
3. 8区間×256入力のnative比較で量子値・古典値・位相が一致した。
4. 実候補の8変更区間が独立証明の置換後SHAと一致した。残る9区間は全10operand columns、register bytesが元とbyte一致した。
5. 最後に実KMBを公式102,400ケースへ渡し、値・位相エラー0でPASSした。

一次証拠: `score4_dqi_full_verification.json`, `score4_dqi_guard_review.json`, `score4_dqi_guard_binding.json`, `score4_dqi_rewrite_certificate.json`。

## 提出ファイル

`submission.zip` は18ファイル入りで、今回のDQI以外の17ファイルをscore3からbyte単位で保持した。invsqrtは既存200,540,928ケースPASS、chemistryは既存78,080ケースPASSのファイルとSHA一致する。全memberのSHA/CRCを再構成時に確認済み。

- ZIPサイズ: {package['zip_bytes']:,} bytes
- ZIP SHA256: `{package['zip_sha256']}`
- DQI SHA256: `{new['circuit_sha256']}`
- 自己完結再構成セル: `score4_package_cell.py`。元score3 ZIPを入力し、ネットワーク・追加依存・再最適化なしで同じ候補を再構成する。
- ソース・全証明・探索記録: `score4_source_and_evidence.zip`。

## Public Scoreの状態

今回のZIPはこの記録時点ではKaggleへ新規提出していないため、Public Scoreは未計測。過去のscore3は27.28236、v27 chemistry+exact4096は27.28543で、選択済みの27.30683を下回ったことを提出画面で確認した。今回の厳密な16個削減・ローカル公式費用低下を、Kaggle最高値更新とは表現しない。

## 他の探索

invsqrtのcache routing、affine差分、HMR延期、QROMのfunctional tensor合成、DQI13-AND共同写像の有限探索も実装・実行した。これらから今回の追加削減は得られていない。陽性対照の削減を実提出の削減へ加算していない。負の結果と有限探索の範囲は各 `score4_*_report.md` / JSONに保持した。
'''
    (ROOT/'score4_results.md').write_text(report)
    shutil.copyfile(ROOT/'score4_results.md',OUT/'score4_results.md')
    shutil.copyfile(ROOT/'score4_delivery_manifest.json',OUT/'score4_delivery_manifest.json')
    # Complete evidence, including large negative-search traces and small
    # positive-control fixtures, is kept in this archive. The submission ZIP
    # itself intentionally contains only the competition's eighteen files.
    files=sorted(p for p in ROOT.glob('score4_*') if p.is_file())
    files += [ROOT/n for n in ('kmb_profile.py','dqi_ccx_peephole.py','verify_dqi_candidate.py',
                               'score3_dqi_full_verification.json','score3_submission_manifest.json')]
    evidence=OUT/'score4_source_and_evidence.zip'
    with zipfile.ZipFile(evidence,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in files:z.write(path,path.name)
        z.write(RUN/'official_verification.log','official_verification.log')
    print(json.dumps(dict(status=summary['status'],archive=summary['archive'],
                          source_archive=str(evidence),source_archive_bytes=evidence.stat().st_size,
                          source_archive_sha256=sha(evidence),cost_reduction_percent=percent),indent=2))

if __name__=='__main__':main()
