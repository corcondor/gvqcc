"""Screen coherent CCX/CSWAP windows by nonlinear output-span codimension."""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'quick_inv'))
from measure_linear import MAX_X, SOURCE_SHA, columns, affine_basis, advance
from drop_reconcile import encode_common
import re
PAID={'CCX','CSWAP'}
OPS={'X','CX','SWAP',*PAID}

def scan(lines, xs):
    n=len(xs); mask=(1<<n)-1; v=columns(xs); stack=[]; old=[]; hits=[]; counts={}; pat=re.compile(r'\bq(\d+)\b')
    for i,l in enumerate(lines):
        op=l.split()[0]; qs=tuple(map(int,pat.findall(l)))
        if op not in OPS: old=[]
        if op=='PUSH_CONDITION': stack.append(v[:]); continue
        if op=='POP_CONDITION': assert stack.pop()==v; continue
        if op in OPS|{'HMR','R'}:
            if op in PAID: old.append((i,v[:],affine_basis([mask,*v])))
            advance('HMR' if op=='R' else op,qs,v,mask)
            if op not in PAID: continue
            old=old[-12:]
            for j,(start,entry,b) in enumerate(old[:-1]):
                k=len(old)-j
                new=dict(b)
                for u in v:
                    while u and u.bit_length()-1 in new: u ^= new[u.bit_length()-1][0]
                    if u: new[u.bit_length()-1]=(u,0)
                r=len(new)-len(b)
                counts[k]=counts.get(k,0)+1
                if r<k:
                    hits.append(dict(start=start,end=i,depth=len(stack),paid=k,rank=r))
    return counts,hits

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert hashlib.sha256(a.source.read_bytes()).hexdigest()==SOURCE_SHA
    import kickmix as km
    lines=str(km.Circuit.from_file(a.source,format='kmb')).splitlines()
    rng=np.random.default_rng(20261115)
    xs=np.unique(np.r_[np.arange(1,1025),rng.integers(1,MAX_X+1,2400),MAX_X]).astype(np.uint32)
    c,h=scan(lines,xs)
    print(c,len(h),h[:25],flush=True)
    a.out.write_text(json.dumps(dict(queries=c,samples=len(xs),hits=h),indent=2)+'\n')
if __name__=='__main__':main()
