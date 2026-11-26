"""Apply previously proved affine substitutions to their exact source KMB.

The report authenticates the source SHA256. Identities may only hold on a
restricted input domain: the output metadata preserves that limitation.
Always run verify_domain.py (or an appropriate official verifier) afterwards.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'recovered/V79'))
from native_kmb import NativeKMB, Op

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True, help='Source stem, without extension.')
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--stem', type=Path, required=True)
    p.add_argument('--max-ops', type=int, default=3)
    args=p.parse_args()
    source=args.source.with_suffix('.kmb')
    report=json.loads(args.audit.read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest()==report['source_sha256']
    K=NativeKMB.read(source)
    representations=report['full_affine_span_audit']['candidates']
    changes={r['index']:r for r in representations
             if int(r['constant'])+len(r['controls'])<=args.max_ops}
    out=[]
    for index,op in enumerate(K.ops):
        if index not in changes:
            out.append(op)
            continue
        r=changes[index]
        assert op.raw==49 and tuple(r['old_wires'])==op.wires
        target=op.wires[2]
        assert target not in r['controls']
        if r['constant']: out.append(Op(17,(target,)))
        out.extend(Op(33,(q,target)) for q in r['controls'])
    K.ops=out
    args.stem.parent.mkdir(parents=True,exist_ok=True)
    target=args.stem.with_suffix('.kmb')
    target.write_bytes(K.to_bytes())
    metadata=json.loads(args.source.with_suffix('.json').read_text())
    metadata['domain_rewrite']={
        'source':str(args.source), 'domain':report['domain'],
        'source_sha256':report['source_sha256'],
        'rewrites':[changes[i] for i in sorted(changes)],
        'full_cube_equivalence_claimed':report['domain']=='full_22_bit_cube',
    }
    args.stem.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
    counts=Counter(op.raw for op in out)
    receipt=dict(source=str(source),output=str(target),domain=report['domain'],
                 rewrites=len(changes),width=K.header[1],ops=len(out),
                 ccx=counts[49],cx=counts[33],x=counts[17],hmr=counts[80],
                 rotations=counts[19],sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                 independent_verification_pending=True)
    metadata['source_stats_before_domain_rewrite']=metadata.pop('stats',None)
    metadata['stats']=receipt.copy()
    args.stem.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
    args.stem.with_suffix('.rewrite.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__': main()
