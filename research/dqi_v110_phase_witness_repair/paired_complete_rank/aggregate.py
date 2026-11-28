"""Combine hash-matched component costs. Score is local/conditional, not Kaggle."""
import csv, glob, hashlib, json, sys
from pathlib import Path
import verify_submission_dqi as verifier

def j(p):return json.loads(Path(p).read_text())
fixed=j('audit/integrated_manifest.json')['conditional_score']
chem294=247630624.56479988
ic294=60865.30803388468
ref_dqi=305039193398.27734
ref_chem=chem294; ref_inv=ic294; ref_score=33.3355088809884
s=ref_score
comparison={}
for arm in sys.argv[1:]:
    rows=sorted([r for p in glob.glob(f'r{arm}_?.csv') for r in csv.DictReader(open(p))],key=lambda r:int(r['batch']))
    assert [int(r['batch']) for r in rows]==list(range(200))
    sums={k:sum(int(x[k]) for x in rows) for k in rows[0] if k!='batch'}
    assert sums['n']==102400
    mean=sums['paid']/sums['n']
    k=sums['official_value']+sums['official_phase']
    eps=verifier.clopper_pearson_upper_bound(k,sums['n'],-128)
    r=verifier.repetition_overhead(eps)
    dqi=r*900**2*mean
    archive=json.loads(Path(f'a{arm}.log').read_text().splitlines()[-1])
    chem=chem294 if arm=='294' else fixed['chemistry_expected_cost']
    inv=ic294 if arm=='294' else fixed['invsqrt_expected_cost']
    score=s*((ref_chem/chem)*(ref_inv/inv)*(ref_dqi/dqi))**(1/3)
    asset=j({'294':'zip294.json','299':'zip306.json','8':'zip8.json'}[arm])
    assert asset['member_hashes']['dqi.kmb']==archive['sha256']
    comparison[arm]=dict(ordinary=dict(**sums,mean_paid=mean,official_formula_dqi_cost=dqi,repetition_factor=r),archived_kickmix=archive,chemistry_cost=chem,invsqrt_cost=inv,conditional_local_score=score,mean_paid_needed_for_33p36=mean*(score/33.36)**3,archive=asset)
if '294' in comparison and '299' in comparison:
    identical=all(Path(f'r294_{i}.csv').read_bytes()==Path(f'r299_{i}.csv').read_bytes() for i in range(4))
    print('294/299 all 200 score batches identical:',identical)
result=dict(salt='paired-complete-review-v1',seed_parent_dqi_sha256=comparison['294']['archived_kickmix']['sha256'],packed_standard_panel_sha256={f'panel{i}.bin':hashlib.file_digest(open(f'panel{i}.bin','rb'),'sha256').hexdigest() for i in range(4)},archive_panel_n=622,archived_kickmix_error_columns=['value','raw phase','dirty Q','mask','union','phase exclusive'],scope='independent paired ordinary replay; full native KickMix on archival stress; older hash-matched other-task receipts; conditional local score, unsubmitted',arms=comparison)
Path('paired_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
for a,r in comparison.items():print(a,r['ordinary'],r['archived_kickmix']['errors'],r['conditional_local_score'])
