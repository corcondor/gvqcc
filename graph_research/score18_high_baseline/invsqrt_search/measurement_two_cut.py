#!/usr/bin/env python3
"""Multi-cut measurement-coordinate rewrite with full-domain certificates."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import re
import sys
import time

import numpy as np
from measurement_basis import (PAID, SOURCE_SHA, MAX_X, gate, product,
                               packed_trace, phase_records, solve, xor_all)


def causal_basis(cuts, snapshots, one):
    features,basis,unique=[],{},set()
    def add(w,cut,qs):
        if not w or w in unique:
            return
        unique.add(w)
        coefficients=0
        while w:
            high=w.bit_length()-1
            if high not in basis:
                basis[high]=w,coefficients^(1<<len(features))
                features.append((cut,qs))
                return
            f,c=basis[high]
            w^=f
            coefficients^=c
    for cut in cuts:
        v=snapshots[cut]
        add(one,cut,())
        for i,w in enumerate(v):
            add(w,cut,(i,))
        for i,w in enumerate(v):
            if w:
                for j,u in enumerate(v[:i]):
                    add(w&u,cut,(j,i))
    return basis,features


def render(lines, a, b, hit):
    fresh=max(map(int,re.findall(r'\bb(\d+)\b','\n'.join(lines))))+1
    m=f'b{fresh}'
    new=f'b{fresh+1}'
    src=[]
    rem=set(a['remove_indices'])
    owners=set(b['remove_indices'])
    b0=a['bit']
    b1=b['bit']
    at={}
    for i,qs in hit['quadratics']:
        at.setdefault(i,[]).append(qs)
    for i,line in enumerate(lines):
        if i in at:
            src.extend(f'{("NEG","Z","CZ")[len(qs)]}{"".join(f" q{q}" for q in qs)} if {m}'
                       for qs in at[i])
        if i in rem:
            continue
        if i in owners:
            line=re.sub(rf' if {b1}$',f' if {new}',line)
        src.append(line)
        if i==a['index']:
            src.extend((f'BIT_STORE0 {m}',f'BIT_INVERT {m} if {b0}'))
        if i==b['index']:
            src.extend((f'BIT_STORE0 {new}',f'BIT_INVERT {new} if {m}',
                        f'BIT_INVERT {new} if {b1}'))
    return '\n'.join(src)+'\n'


def restrict(bits,xs):
    # xs are addresses starting at 1
    offs=(xs-1).astype(np.uint32)
    raw=bits.to_bytes((MAX_X+7)//8,'little')
    v=np.frombuffer(raw,dtype=np.uint8)
    picked=((v[offs//8]>>(offs%8))&1).astype(np.uint8)
    return int.from_bytes(np.packbits(picked,bitorder='little').tobytes(),'little')


def smaller_solve(a,b,terms,full,xs,one):
    initial={i:[restrict(v,xs) for v in full[i]] for i in terms}
    basis,features=causal_basis(terms,initial,one)
    f=restrict(a^b,xs)
    c=solve(basis,f)
    return None if c is None else [t for k,t in enumerate(features) if c>>k&1]


def run_candidate(terms,full,a,b,samples):
    tested=[]
    unique=set(map(int,samples))
    while len(tested)<8:
        one=(1<<len(samples))-1
        q=smaller_solve(a,b,terms,full,samples,one)
        if q is None:
            return False,tested
        mask=(1<<MAX_X)-1
        delta=a^b^xor_all(product(full[i],qs,mask) for i,qs in q)
        if not delta:
            return dict(quadratics=q,samples=len(samples),iterations=len(tested)+1),tested
        tested.append(delta.bit_count())
        n=0
        while delta and n<256:
            bit=delta&-delta
            address=bit.bit_length()
            unique.add(address)
            n+=1
            delta^=bit
        samples=np.array(sorted(unique),dtype=np.uint32)
    return False,tested


def main():
    import kickmix as km
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--code',type=Path,required=True)
    p.add_argument('--priors',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    sys.path.insert(0,str(args.code))
    from score4_invsqrt_block_cleanup import cleanup_records
    t=time.monotonic()
    assert sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    circ=km.Circuit.from_file(args.source,format='kmb')
    lines=str(circ).splitlines()
    ops=list(map(gate,lines))
    depth=[]
    d=0
    for op,_ in ops:
        depth.append(d)
        if op=='PUSH_CONDITION':
            d+=1
        elif op=='POP_CONDITION':
            d-=1
    assert not d
    raw,_=cleanup_records(lines,ops,depth)
    recs=[r for r in raw if any(ops[j][0] in PAID for j in r['remove_indices'])]
    prior=json.loads(args.priors.read_text())
    by={r['index']:r for r in recs}
    near=[(i,j) for i in by for j in by if 0<j-i<200]
    pairs=sorted(set((h['earlier'],h['later']) for h in prior['sample_hits'])|set(near))
    plans=[]
    for i,j in pairs:
        a,b=by[i],by[j]
        if set(a['remove_indices'])&set(b['remove_indices']):
            continue
        stop=max(b['remove_indices'])+1
        cuts=sorted({z for z in (i+1,max(a['remove_indices'])+1,j,j+1,stop)
                     if z<len(lines) and depth[z]==0})
        plans.append((i,j,tuple(cuts)))
    ids={q for i,j,_ in plans for q in (i,j)}
    cuts={z for _,_,c in plans for z in c}
    print('plans',len(plans),'cuts',len(cuts),flush=True)
    rset=[r for r in recs if r['index'] in ids]
    active={j for r in rset for j in ([r['index']]+r['phase_indices']+
             [i for seq in r['nonconstant_phase_terms'].values() for i in seq])}
    v,s,one=packed_trace(ops,np.arange(1,MAX_X+1,dtype=np.uint32),active,cuts,True)
    ok={r['index'] for r in phase_records(rset,v)}
    rng=np.random.default_rng(552019)
    xs=np.unique(np.r_[np.arange(1,1025),np.arange(MAX_X-127,MAX_X+1),
                       rng.integers(1,MAX_X+1,size=3584)]).astype(np.uint32)
    hits=[]
    rejects=[]
    for i,j,c in plans:
        if i not in ok or j not in ok:
            continue
        h,counts=run_candidate(c,s,v[i],v[j],xs)
        if h:
            hits.append(dict(h,earlier=i,later=j,cuts=c))
        else:
            rejects.append(dict(earlier=i,later=j,cuts=c,failed_addresses_after_each_fit=counts))
    output=dict(source_sha256=SOURCE_SHA,pairs=len(plans),cut_count=len(cuts),
                first_samples=len(xs),confirmed_cleanup_records=len(ok),results=hits,rejects=rejects,
                elapsed_s=time.monotonic()-t)
    if hits:
        best=min(hits,key=lambda h:len(h['quadratics']))
        out=args.out.parent/'candidate.kmb'
        candidate=render(lines,by[best['earlier']],by[best['later']],best)
        alt=km.Circuit(candidate)
        assert alt.num_qubits==circ.num_qubits
        assert alt.operation_statistics().num_toffoli_like<circ.operation_statistics().num_toffoli_like
        alt.to_file(out,format='kmb')
        output.update(candidate_sha256=sha256(out.read_bytes()).hexdigest(),selected=best)
    args.out.write_text(json.dumps(output,indent=2)+'\n')
    print({k:len(v) if isinstance(v,list) else v for k,v in output.items()},flush=True)


if __name__=='__main__':
    main()
