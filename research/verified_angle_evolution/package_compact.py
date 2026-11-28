"""Exact isometry-preserving KMB compaction; no scoring Toffoli savings.

Produces a complete 18-member ZIP, but **NOT** a new score record or an
inherited official verification for these newly serialized KMB files.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile,shutil
from pathlib import Path
from kmb_v2 import load
from exact_angle import verify
from heuristics import optimize

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args();src=zipfile.ZipFile(a.baseline)
    expected={f'dfthcsos/angle_k_{i}.kmb' for i in range(15)}|{'dfthcsos/submission.npz','invsqrt.kmb','dqi.kmb'}
    assert set(src.namelist())==expected,'Unrecognized baseline member set'
    import tempfile
    with tempfile.TemporaryDirectory() as root:
        root=Path(root)
        originals=[]
        for i in range(15):
            nm=f'dfthcsos/angle_k_{i}.kmb';p=root/f'old{i}.kmb';p.write_bytes(src.read(nm));originals.append(load(p))
        before,ref=verify(originals)
        candidates,changes=optimize(originals,window=48)
        check,_=verify(candidates,reference=ref)
        assert before.ccx==check.ccx==4030
        assert before.outputs_digest==check.outputs_digest
        saved=sum(x['free_deleted'] for x in changes)
        assert saved>=0
        newbytes={};hashes={};oldops=[];newops=[]
        for i,c in enumerate(candidates):
            output=root/f'new{i}.kmb';raw=c.write(output)
            assert load(output).ops==c.ops,'serialization mismatch'
            nm=f'dfthcsos/angle_k_{i}.kmb';newbytes[nm]=raw;hashes[nm]=sha(raw)
            oldops.append(len(originals[i].ops));newops.append(len(c.ops))
        # Verify roundtrip serialized candidate again, not only in memory.
        loaded=[load(root/f'new{i}.kmb') for i in range(15)]
        final,_=verify(loaded,reference=ref)
        assert final==check
        with zipfile.ZipFile(a.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as dst:
            for name in sorted(expected):
                if name in newbytes:dst.writestr(name,newbytes[name]);continue
                with src.open(name) as reader,dst.open(name,'w') as writer:
                    shutil.copyfileobj(reader,writer,length=1<<20)
        with zipfile.ZipFile(a.output) as post:
            assert set(post.namelist())==expected
            assert post.testzip() is None
            assert all(sha(post.read(n))==sha(src.read(n)) for n in expected if n not in newbytes)
        receipt={'status':'REACHABLE_ISOMETRY_EXACT_PASS_SAME_SCORE_OFFICIAL_UNVERIFIED',
                 'baseline_sha256':sha(a.baseline.read_bytes()),
                 'output_sha256':sha(a.output.read_bytes()),
                 'output_size':a.output.stat().st_size,'member_sha256':hashes,
                 'total_original_loader_ops':sum(oldops),'total_new_loader_ops':sum(newops),
                 'removed_free_ops':saved,'original_CCX':before.ccx,'new_CCX':final.ccx,
                 'Q_loader_max':final.max_qubits,'all_address_transitions':final.transitions,
                 'HMR_variables':final.measurement_phases,
                 'reference_output_sha256':final.outputs_digest,
                 'predicted_local_score':27.327844395957978,
                 'official_verifier_run':False,'kaggle_submitted':False,
                 'notes':'X/CX cancellation is an arbitrary-state commutation identity; all 1220 addresses and measurement phases independently checked; no change to costs in competition formula'}
        a.receipt.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({k:v for k,v in receipt.items() if k!='member_sha256'},indent=2,ensure_ascii=False))
if __name__=='__main__':main()
