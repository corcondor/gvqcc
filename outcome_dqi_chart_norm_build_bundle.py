#!/usr/bin/env python3
"""Bind the completed qualification into a self-contained offline worker."""
from pathlib import Path
import base64
import hashlib
import importlib.util
import json
import zipfile

ROOT=Path(__file__).resolve().parent


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    qpath=ROOT/'outcome_dqi_chart_norm_full_verification.json'
    qbytes=qpath.read_bytes();q=json.loads(qbytes)
    expected='ebfb770f6fc8abc7f48287a0fa4ee6404a2e32a9facdd38449b4f7b73be05d0e'
    assert q['status']=='PASS' and q['verified_shots']==102400 and q['circuit_sha256']==expected
    assert q['num_qubits']==889 and q['max_toffoli_count']==382920
    assert q['seed'] is None and q['salt']=='' and q['log2_delta']==-128
    patch=(ROOT/'outcome_dqi_chart_norm_patch.json.gz').read_bytes()
    public=(ROOT/'outcome_v27_public_pins.json').read_bytes()
    proof=(ROOT/'outcome_dqi_chart_norm_proof.md').read_bytes()
    scope={'candidate_sha256':expected,'official_receipt_sha256':sha(qbytes),
        'guaranteed_component_domain':'Thirdpublicpivot finiteoutput: queriedN!=0. ZeroqueriedD is included.',
        'fixed_known_valid_input':{'weight':33,'batch':349,'shot_in_batch':121,'absolute_shot':89465,
            'first_exception_node_zero_based':2,'N':[1103,3094],'D':[0,0],
            'case_sha256':'e92fab245e56346d002fdd3254466d3d98bc764a6db93596d46cb7b50da206ce'},
        'remaining_known_valid_input_failure':{'weight':31,'batch':104,'shot_in_batch':184,'absolute_shot':26808,
            'first_exception_node_zero_based':13,'N':[0,0],'D':[1013,2476],
            'case_sha256':'87c18965ac99615c6b1c20156350ac83acc398ead86fbe4a78bc2274c2c74433',
            'still_value_error':True},
        'third_pivot_N_zero_also_guaranteed':False,
        'independent_common_valid_inputs':16384,'new_failures_in_that_corpus':0,
        'global_correctness_or_public_score_claim':False,
        'note':'The remainingknownN=0 counterexample is node13, not the thirdpivot. A finite officialPASS does not eliminate it.'}
    scope_bytes=(json.dumps(scope,indent=2)+'\n').encode()
    (ROOT/'outcome_dqi_chart_norm_qualification_scope.json').write_bytes(scope_bytes)
    source=ROOT.parent/'official_sources/Syed_v12/source/dqi_source'
    license_bytes=(source/'LICENSE').read_bytes()
    original_notice=(source/'NOTICE').read_text()
    spec=importlib.util.spec_from_file_location('outcome_chart_upstream_portfolio_notice',ROOT/'outcome_v27_combine.py')
    predecessor=importlib.util.module_from_spec(spec);spec.loader.exec_module(predecessor)
    notice=(predecessor.NOTICE+'\n## Original DQI source NOTICE (preserved verbatim)\n\n'+original_notice+
        '\n## New modification, 2026-11-15\n\n'
        'The third public pivot now keeps an explicit projective-infinity flag. '
        'Its zero queries reuse the existing GF(4) norm through the upstream cubic inverse zero_flag API. '
        'This fixes the D=0, N!=0 chart case at that pivot and reduces static Toffoli count by14. '
        'Other N=0 failures remain outside the stated extension. The paired source and deferred-mask ownership '
        'proof, native component receipts, and full official102400-shot receipt are included. '
        'This is a derivative of Syed Asad Ali’s Apache-2.0 DQI source; its existing AI-agent credits above are retained. '
        'The unchanged other17 members are pinned to maoxin123 public-v27. '
        'No Public score for this new circuit is claimed before actual submission scoring.\n').encode()
    values={'PATCH_B64':base64.b64encode(patch).decode(),'PATCH_SHA256':sha(patch),
        'QUALIFICATION_B64':base64.b64encode(qbytes).decode(),'QUALIFICATION_SHA256':sha(qbytes),
        'SCOPE_B64':base64.b64encode(scope_bytes).decode(),'SCOPE_SHA256':sha(scope_bytes),
        'PUBLIC_B64':base64.b64encode(public).decode(),'PUBLIC_SHA256':sha(public),
        'PROOF_B64':base64.b64encode(proof).decode(),'PROOF_SHA256':sha(proof),
        'NOTICE_B64':base64.b64encode(notice).decode(),'LICENSE_B64':base64.b64encode(license_bytes).decode()}
    worker=(ROOT/'outcome_dqi_chart_norm_worker_template.py').read_text()
    for key,value in values.items():
        token='__'+key+'__';assert worker.count(token)==1
        worker=worker.replace(token,value)
    compile(worker,'outcome_dqi_chart_norm_worker.py','exec')
    (ROOT/'outcome_dqi_chart_norm_worker.py').write_text(worker)
    (ROOT/'outcome_dqi_chart_norm_NOTICE.md').write_bytes(notice)
    (ROOT/'outcome_dqi_chart_norm_LICENSE.txt').write_bytes(license_bytes)
    readme=f'''# Qualified projective-chart patch and offline Kaggle worker

Candidate DQI SHA-256: `{expected}`. Q889, static maximum382920.
Official default102400-shot result: {q['status']}; value errors{q['value_errors']}; phase errors{q['phase_errors']}; mean Toffoli{q['toffoli_count']:.8f}; cost{q['score']:.5f}.

The included worker is self-contained Python standard library only. It embeds the87KB exact byte patch, public-v27 member pins, proof hash, and the completed qualification. No full500MB KMB is needed in Git.

## Kaggle inputs

Attach outputs from:

- `maoxin123/qcc-v27-4030-toffoli-coded-word-chemistry`, public-v27 v3 / script369706978, or an exact copy. The17 non-DQI members must match all pinned sizes and hashes.
- `geocpuresearch/gvqcc-exact4096-gauge-score2` v1 / script369719696, or another output containing the exact9a82 DQI.

Run `outcome_dqi_chart_norm_worker.py` as a CPU Python notebook/script. It discovers those pinned files under `/kaggle/input` and writes `/kaggle/working/submission.zip`, a packaging receipt, qualification, proof, and source notices. It never submits to the competition and never accesses credentials or the network.

For explicit local paths:

```bash
python outcome_dqi_chart_norm_worker.py --public /path/to/public_v27.zip --dqi /path/to/donor_9a82.zip --output-root /path/to/new_output
```

To reconstruct just the KMB:

```bash
python outcome_dqi_chart_norm_worker.py --patch-only --dqi /path/to/donor_9a82.kmb --output-root /path/to/new_output
```

The output folder must not already contain the target artifact. The script requires the whole pinned input SHA, each old patch region, and the whole reconstructed output SHA. It preserves the other17 public-v27 members byte-for-byte and rejects older chemistry portfolios.

## Scope

This generally repairs zero denominator at the third public pivot when its numerator is nonzero. The knownweight33 counterexample is fixed. A knownweight31 numerator-zero failure remains. The original and new circuits were compared on the same16384 independent valid inputs, with no new failures. A finite verification PASS is not universal correctness or a new Public score.

The source builders in this bundle are optional research provenance and require the pinned upstream DQI source/KickMix environment. The portable worker itself has no such dependencies. See the proof, component receipt, splice ownership audit, paired receipt, and qualification for evidence.

The bundle retains the upstream Apache-2.0 license and source credits. The candidate is for review and the next submission quota slot.
'''
    (ROOT/'outcome_dqi_chart_norm_README.md').write_text(readme)
    names=['outcome_dqi_chart_norm_worker.py','outcome_dqi_chart_norm_patch.json.gz',
        'outcome_dqi_chart_norm_README.md','outcome_dqi_chart_norm_NOTICE.md','outcome_dqi_chart_norm_LICENSE.txt',
        'outcome_dqi_chart_norm_proof.md','outcome_dqi_chart_norm_full_verification.json',
        'outcome_dqi_chart_norm_qualification_scope.json',
        'outcome_dqi_chart_norm_component_report.json','outcome_dqi_chart_norm_splice_report.json',
        'outcome_dqi_chart_norm_paired_comparison.json','outcome_dqi_chart_norm_patch_export.json',
        'outcome_dqi_chart_norm_worker_check.json','outcome_dqi_chart_third_norm.py',
        'outcome_dqi_chart_inverse_norm.py','outcome_dqi_chart_check_norm.py',
        'outcome_dqi_chart_splice_norm.py','outcome_dqi_chart_norm_export_patch.py',
        'outcome_dqi_chart_norm_build_bundle.py']
    for optional in ['outcome_dqi_chart_norm_review.md','outcome_dqi_chart_norm_review.json',
                     'outcome_dqi_chart_norm_review.py']:
        if (ROOT/optional).exists():names.append(optional)
    files={name:{'sha256':sha((ROOT/name).read_bytes()),'bytes':(ROOT/name).stat().st_size} for name in names}
    binding={'status':'FULL_OFFICIAL_QUALIFIED_PORTABLE_BUNDLE','candidate_sha256':expected,
        'input_dqi_sha256':'9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1',
        'qualification_sha256':sha(qbytes),'proof_sha256':sha(proof),'patch_sha256':sha(patch),
        'qualification_scope':scope,'qualification_scope_sha256':sha(scope_bytes),
        'worker_sha256':sha(worker.encode()),'public17_pins_sha256':sha(public),
        'full_kmb_in_bundle':False,'submission_performed':False,'files':files,
        'scientific_result':{k:q[k] for k in ['status','verified_shots','value_errors','phase_errors','num_qubits','toffoli_count','max_toffoli_count','score']}}
    binding_path=ROOT/'outcome_dqi_chart_norm_qualification_binding.json'
    binding_path.write_text(json.dumps(binding,indent=2)+'\n');names.append(binding_path.name)
    bundle=ROOT/'outcome_dqi_chart_norm_bundle.zip'
    with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in sorted(names):
            info=zipfile.ZipInfo(name,(2026,11,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3;info.external_attr=0o100644<<16
            z.writestr(info,(ROOT/name).read_bytes())
    built={'status':binding['status'],'bundle_path':str(bundle),'bundle_bytes':bundle.stat().st_size,
        'bundle_sha256':sha(bundle.read_bytes()),'worker_path':str(ROOT/'outcome_dqi_chart_norm_worker.py'),
        'worker_bytes':len(worker.encode()),'worker_sha256':binding['worker_sha256'],
        'qualification_sha256':binding['qualification_sha256'],'candidate_sha256':expected,
        'files':len(names),'submission_performed':False}
    (ROOT/'outcome_dqi_chart_norm_bundle_build.json').write_text(json.dumps(built,indent=2)+'\n')
    print(json.dumps(built,indent=2))


if __name__=='__main__':main()
