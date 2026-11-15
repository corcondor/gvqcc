#!/usr/bin/env python3
"""Find a smaller rank-two cofactor dictionary using the measured triple sums."""
import argparse
from collections import defaultdict, Counter
import json
from pathlib import Path
import random
import struct
import sys

def indices(mask):
    while mask:
        bit=mask&-mask
        yield bit.bit_length()-1
        mask^=bit

def add(basis, value):
    while value:
        pivot=value.bit_length()-1
        if pivot not in basis:
            basis[pivot]=value
            return True
        value^=basis[pivot]
    return False

def output_dependencies(direction):
    basis={}
    deps=[]
    for i,w in enumerate(direction):
        v=1<<i
        while w:
            p=w.bit_length()-1
            if p not in basis:
                basis[p]=w,v
                break
            w0,v0=basis[p]
            w^=w0
            v^=v0
        if not w: deps.append(v)
    return deps

def targeted_candidates(deps,rng):
    seen=set()
    def accept(x):
        if not x or x in seen: return False
        seen.add(x)
        return True
    for a in deps:
        if accept(a): yield a
    for i,a in enumerate(deps):
        for b in deps[:i]:
            x=a^b
            if accept(x): yield x
    if len(deps)>2:
        for _ in range(5000):
            a,b,c=rng.choices(deps,k=3)
            x=a^b^c
            if accept(x): yield x

def search(mats,dirs,triples,cap,rank2_sum):
    n=len(mats)
    forms=list(mats)
    masks=[1<<i for i in range(n)]
    known={m:i for i,m in enumerate(masks)}
    def append(mat, mask):
        if mask in known: return
        known[mask]=len(forms)
        forms.append(mat)
        masks.append(mask)
    for selected in triples:
        mat=(0,)*76
        for item in selected:
            mat=tuple(a^b for a,b in zip(mat,mats[item]))
        append(mat,sum(1<<item for item in selected))
    i=0
    while i<len(forms) and len(forms)<cap:
        for j in range(i):
            combo=masks[i]^masks[j]
            if combo in known: continue
            res=rank2_sum(forms[i],forms[j])
            if res is not None:
                append(res,combo)
                if len(forms)>=cap:break
        i+=1
    closure_complete=i==len(forms)
    groups=[1<<i for i in range(n)]
    for s in masks[n:]:
        g=0
        for i in indices(s):g|=groups[i]
        for i in indices(g):groups[i]=g
    components=sorted(set(groups))
    big=Counter()
    max_recovered=0
    checked=0
    improvement=None
    rng=random.Random(202611151361)
    for component in components:
        ids=list(indices(component))
        ds=output_dependencies([dirs[j] for j in ids])
        if not ds:continue
        d=len(ids)
        big[d]+=1
        deps=[sum(1<<ids[j] for j in indices(a)) for a in ds]
        eligible=[s for s in masks if s&component==s]
        for witness in targeted_candidates(deps,rng):
            checked+=1
            piv={}
            keep=[]
            for s in eligible:
                if (s&witness).bit_count()%2==0 and add(piv,s):
                    keep.append(s)
            missing=d-1-len(keep)
            max_recovered=max(max_recovered,len(keep))
            if missing==0:
                improvement=dict(component=ids,witness=hex(witness),replacement=[hex(s) for s in keep])
                break
        if improvement:break
    return dict(terms=n,triples=len(triples),dictionary=len(masks),pair_closure_complete=closure_complete,
                dependent_components=big,hyperplanes_tested=checked,max_hyperplane_rank=max_recovered,
                improvement=improvement)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder',required=True,type=Path)
    p.add_argument('--cap',type=int,default=1800)
    p.add_argument('--with-quads',action='store_true')
    a=p.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'score10_followup'/'chemistry'))
    from score11_j5_product_circuits import rank2_sum
    data=(a.folder/'segments.bin').read_bytes()
    segments=json.loads((a.folder/'segments.json').read_text())
    triples=defaultdict(list)
    for name in ['triples.txt']+(['quads.txt'] if a.with_quads else []):
        for line in (a.folder/name).read_text().splitlines():
            k,*items=map(int,line.split())
            triples[k].append(items)
    offset=0
    reports=[]
    for k,s in enumerate(segments):
        n=struct.unpack_from('<I',data,offset)[0]
        offset+=4
        assert n==len(s['directions'])
        mats=list(struct.iter_unpack('<76H',data[offset:offset+n*152]))
        offset+=n*152
        row=search(mats,s['directions'],triples[k],a.cap,rank2_sum)
        reports.append(dict(segment=k,batch=s['batch'],**row))
        print(json.dumps(reports[-1]),flush=True)
    assert offset==len(data)
    (a.folder/'result.json').write_text(json.dumps(reports,indent=2)+'\n')

if __name__=='__main__':
    main()
