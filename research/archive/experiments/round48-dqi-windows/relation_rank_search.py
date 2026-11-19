"""Probe coupled 3/4-output lifts: redistribute one alternating rank-2 atom.
Usage: python relation_rank_search.py FILE.kmb > receipt.json
Uses prefix anchored to known 42-CCX template; validates paired motif spans.
Outputs exact algebraic upper bounds only, not bidirectional KMB scheduling.
"""
import collections, hashlib, itertools, json, sys, time
from pathlib import Path
import numpy as np
from dqi_kernel_motif_audit import arrays_from_kmb,canonical_ccx

def rank(rows):
    b={}
    for x in rows:
        while x:
            hi=x.bit_length()-1
            if hi in b: x^=b[hi]
            else: b[hi]=x;break
    return len(b)

def bitpos(x):
    while x:
        b=x&-x; yield b.bit_length()-1;x^=b

def polar(u,v):
    return {i:(v if u>>i&1 else 0)^(u if v>>i&1 else 0) for i in bitpos(u|v)}

def xorrows(a,b):
    return [a.get(i,0)^b.get(i,0) for i in a.keys()|b.keys()]

def span(v):
    o={0}
    for x in v:o|={x^y for y in o}
    return sorted(o-{0})

def relation_sets(dirs):
    buckets=collections.defaultdict(list)
    ix={d:i for i,d in enumerate(dirs)}
    out=set()
    for i,j in itertools.combinations(range(len(dirs)),2):
        sums=dirs[i]^dirs[j]
        if sums in ix:out.add(tuple(sorted((i,j,ix[sums]))))
        for a,b in buckets[sums]:
            if len({a,b,i,j})==4:out.add(tuple(sorted((a,b,i,j))))
        buckets[sums].append((i,j))
    return sorted(out)

def search(groups):
    dirs=sorted(groups); p=[];atoms=set()
    for d in dirs:
        row=collections.defaultdict(int)
        for x,y in groups[d]:
            for i,v in polar(x,y).items(): row[i]^=v
        row={i:v for i,v in row.items() if v}
        p.append(row)
        ss=span(row.values())
        for x,y in itertools.combinations(ss,2):
            if x<y<(x^y): atoms.add((x,y))
    r=[rank(q.values())//2 for q in p]
    rel=relation_sets(dirs)
    if not rel or not atoms:return sum(r),sum(r),len(rel),len(atoms),None
    best=sum(r); proof=None
    for x,y in sorted(atoms):
        delta={};a=polar(x,y)
        for i,q in enumerate(p):
            if rank([*q.values(),x,y])==2*r[i]+2:
                delta[i]=1 # new control plane direct sum
            else:delta[i]=rank(xorrows(q,a))//2-r[i]
        for inds in rel:
            m=sum(r)+sum(delta[i] for i in inds)
            if m<best:
                best=m
                proof=dict(atom=[hex(x),hex(y)],directions=[hex(dirs[i]) for i in inds],
                           rank_before=[2*r[i] for i in inds],rank_after=[2*(r[i]+delta[i]) for i in inds])
    return sum(r),best,len(rel),len(atoms),proof

def windows(path):
    h,v=arrays_from_kmb(path);op,q30,q31,q32,q20,q21,*_=v
    p3=np.flatnonzero((op&48)==48);m=op[p3]==49;pc=p3[m];a,b,t=q30[m],q31[m],q32[m]
    cand=np.arange(len(pc)-41,dtype=np.int32);cand=cand[(t[cand]==t[cand+1])&(a[cand]==a[cand+3])&(b[cand]==b[cand+3])&(a[cand]==a[cand+4])&(b[cand]==b[cand+4])]
    ref=canonical_ccx(0,a,b,t)
    hits=np.array([i for i in cand if canonical_ccx(int(i),a,b,t)==ref],dtype=np.int32)
    assert len(hits)>0,'template does not match this parent'
    p2=np.flatnonzero((op&48)==32)
    for k in np.flatnonzero(np.diff(hits)==42):
        start, end=map(int,(pc[hits[k]],pc[hits[k+1]]))
        if int(pc[hits[k]+41])-start!=1292 or int(pc[hits[k+1]+41])-end!=1292:continue
        if not np.all(op[start:end+1293]==33) and np.any((op[start:end+1293]!=33)&(op[start:end+1293]!=49)):continue
        aff=[1<<w for w in range(h['qubits'])];dep=[0]*h['qubits'];terms=[]
        i2,i3=int(np.searchsorted(p2,start)),int(np.searchsorted(p3,start))
        for i in range(start,end+1293):
            if op[i]==33:
                x,y=int(q20[i2]),int(q21[i2]);i2+=1;aff[y]^=aff[x];dep[y]^=dep[x]
            else:
                x,y,z=int(q30[i3]),int(q31[i3]),int(q32[i3]);i3+=1
                if dep[x] or dep[y]:break
                terms.append((aff[x],aff[y]));dep[z]^=1<<(len(terms)-1)
        if len(terms)!=84:continue
        dirs=[0]*84
        for w,mask in enumerate(dep):
            for j in bitpos(mask):dirs[j]|=1<<w
        if rank(dirs)!=12:continue
        groups=collections.defaultdict(list)
        for d,pair in zip(dirs,terms):
            if d:groups[d].append(pair)
        yield start,end,dict(groups)

def main():
    pa=Path(sys.argv[1])
    if '--self-test' in sys.argv:
        assert rank(list(polar(1,2).values()))==2
        # Three mutually coupled, rank-2 quadratics all add the same atom.
        a,b,c,ab=1,2,4,3
        groups={a:[(1,2)],b:[(1,2)],ab:[(1,2)]}
        s=search(groups)
        assert s[:2]==(3,0) and s[-1],s
        return
    res=[];s=time.monotonic();cache={}
    for x,y,g in windows(pa):
        # Normalize physical wire numbers, allowing identical windows to share a result.
        wsp=sorted({i for d,fac in g.items() for z in [d,*[v for f in fac for v in f]] for i in bitpos(z)})
        coords={i:j for j,i in enumerate(wsp)}
        def keymap(d):return sum(1<<coords[i] for i in bitpos(d))
        k=tuple(sorted((keymap(d),tuple(sorted(tuple(sorted((keymap(a),keymap(b)))) for a,b in pairs))) for d,pairs in g.items()))
        if k not in cache:
            before,after,n,na,proof=search(dict(k));cache[k]=(before,after,n,na,proof)
        before,after,n,na,proof=cache[k]
        row=dict(first_start=x,second_start=y,independent_rank_upper=before,after_relation_rank_upper=after,relations_3_or_4=n,atom_candidates=na)
        if after<84:row.update(affine_coordinate_wires=wsp,proof=proof)
        res.append(row)
        print(json.dumps(row),file=sys.stderr,flush=True)
    with pa.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    print(json.dumps(dict(scope='quadratic-map factor-count upper bound only',sha256=h,seconds=round(time.monotonic()-s,3),windows=len(res),unique_coordinate_types=len(cache),rows=res),indent=2))
if __name__=='__main__':main()
