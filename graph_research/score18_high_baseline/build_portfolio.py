#!/usr/bin/env python3
"""Assemble the default-verified graph chemistry with the unchanged other tasks."""
from argparse import ArgumentParser
from hashlib import file_digest,sha256
from io import BytesIO
import json
from math import prod
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED


def main():
    p=ArgumentParser(description=__doc__)
    for name in ('zip','scorecard','family','chemistry-receipt','out','receipt'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    base=json.loads(a.scorecard.read_text())
    verified=json.loads(a.chemistry_receipt.read_text())
    assert verified['status']=='PASS' and verified['verified_shots']==78080
    assert verified['score']<base['costs']['chemistry']
    assert (verified['num_ops'],verified['toffoli_count'],verified['num_qubits'])==(306105,14722,427)
    assert sha256(a.zip.read_bytes()).hexdigest()==base['zip_sha256']
    loaders=[f'dfthcsos/angle_k_{i}.kmb' for i in range(15)]
    npz_name='dfthcsos/submission.npz'
    chemistry={n:(a.family/n.split('/')[-1]).read_bytes() for n in [*loaders,npz_name]}
    canonical=sha256()
    for n in loaders:canonical.update(chemistry[n])
    with ZipFile(BytesIO(chemistry[npz_name])) as new_npz:
        for k in ('U','W','H2_I','H1_I','Hsym_lower','tree_edges'):
            canonical.update(new_npz.read(k+'.npy'))
    assert canonical.hexdigest()==verified['submission_sha256']
    unchanged=('dqi.kmb','invsqrt.kmb')
    expected={*chemistry,*unchanged}
    member_hash={n:sha256(data).hexdigest() for n,data in chemistry.items()}
    with ZipFile(a.zip) as source,ZipFile(a.out,'x',compression=ZIP_DEFLATED,compresslevel=6) as dst:
        assert set(source.namelist())==expected and len(source.namelist())==18
        with ZipFile(BytesIO(source.read(npz_name))) as old, ZipFile(BytesIO(chemistry[npz_name])) as new:
            assert set(old.namelist())==set(new.namelist())
            diff={n for n in old.namelist() if old.read(n)!=new.read(n)}
            assert diff=={'W.npy','H2_I.npy'},diff
        for n in unchanged:
            h=sha256()
            with source.open(n) as reader,dst.open(n,'w') as writer:
                for chunk in iter(lambda:reader.read(1<<20),b''):
                    h.update(chunk);writer.write(chunk)
            member_hash[n]=h.hexdigest()
            assert member_hash[n]==base['members'][n]
        for n,data in chemistry.items():dst.writestr(n,data)
    with ZipFile(a.out) as dst:
        assert set(dst.namelist())==expected and len(dst.namelist())==18
        for n,h in member_hash.items():
            with dst.open(n) as f: assert file_digest(f,'sha256').hexdigest()==h
    costs={**base['costs'],'chemistry':verified['score']}
    refs=base['reference_costs']
    score=prod(refs[t]/costs[t] for t in refs)**(1/3)
    receipt=dict(local_score=score,baseline_local_score=base['local_score'],
                 local_improvement=score-base['local_score'],costs=costs,reference_costs=refs,
                 chemistry_verified_shots=verified['verified_shots'],
                 chemistry_submission_digest=verified['submission_sha256'],
                 dqi_invsqrt='byte-identical score11; inherited verified costs',
                 kaggle_submitted=False,members=member_hash,
                 zip_size=a.out.stat().st_size,zip_sha256=sha256(a.out.read_bytes()).hexdigest())
    a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print({k:v for k,v in receipt.items() if k!='members'})

if __name__=='__main__':
    main()
