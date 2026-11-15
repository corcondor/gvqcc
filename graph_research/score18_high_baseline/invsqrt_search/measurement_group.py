#!/usr/bin/env python3
"""Find exact relations between multiple paid measurement corrections."""
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
from measurement_two_cut import causal_basis, restrict


def find_relation(masks,basis,features):
    """Test equality of the first truth mask to later masks modulo Z/CZ span."""
    for i,w in enumerate(masks[1:],start=1):
        coeff=0
        while w:
            k=w.bit_length()-1
            if k not in basis:
                basis[k]=w,coeff^(1<<len(features))
                features.append((None,(i,)))
                break
            u,c=basis[k]
            w^=u
            coeff^=c
    mask=solve(basis,masks[0])
    if mask is None:
        return None
    return [feature for i,feature in enumerate(features) if mask>>i&1]


def fit(group,cuts,full,snapshots,samples):
    one=(1<<len(samples))-1
    v={i:[restrict(w,samples) for w in vectors] for i,vectors in snapshots.items() if i in cuts}
    basis,features=causal_basis(cuts,v,one)
    masks=[restrict(full[i],samples) for i in group]
    return find_relation(masks,basis,features)


def generate(lines,records,group,retained,corrections):
    indices=[group[0],*retained]
    specs={r['index']:r for r in records if r['index'] in indices}
    first=specs[group[0]]
    ctr=max(map(int,re.findall(r'\bb(\d+)\b','\n'.join(lines))))+1
    primary=f'b{ctr}'
    own={}
    fresh={}
    for j,i in enumerate(retained):
        rec=specs[i]
        fresh[i]=f'b{ctr+1+j}'
        for k in rec['remove_indices']:
            assert k not in own
            own[k]=i
    emitted=[]
    dropped=set(first['remove_indices'])
    at={}
    for i,qs in corrections:
        at.setdefault(i,[]).append(qs)
    for i,line in enumerate(lines):
        if i in at:
            emitted.extend(f'{("NEG","Z","CZ")[len(qs)]}{"".join(f" q{q}" for q in qs)} if {primary}'
                           for qs in at[i])
        if i in dropped:
            continue
        if i in own:
            r=specs[own[i]]
            line=re.sub(rf" if {r['bit']}$",f' if {fresh[own[i]]}',line)
        emitted.append(line)
        if i==group[0]:
            emitted.extend((f'BIT_STORE0 {primary}',f"BIT_INVERT {primary} if {first['bit']}"))
        if i in fresh:
            f=fresh[i]
            b=specs[i]['bit']
            emitted.extend((f'BIT_STORE0 {f}',f'BIT_INVERT {f} if {primary}',f'BIT_INVERT {f} if {b}'))
    return '\n'.join(emitted)+'\n'


def main():
    import kickmix as km
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--code',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    sys.path.insert(0,str(args.code))
    from score4_invsqrt_block_cleanup import cleanup_records
    t0=time.monotonic()
    assert sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    circ=km.Circuit.from_file(args.source,format='kmb')
    lines=str(circ).splitlines()
    ops=list(map(gate,lines))
    depth=[]
    d=0
    for op,_ in ops:
        depth.append(d)
        d+=(op=='PUSH_CONDITION')-(op=='POP_CONDITION')
    assert not d
    clean,_=cleanup_records(lines,ops,depth)
    paid=[r for r in clean if any(ops[j][0] in PAID for j in r['remove_indices'])]
    indexed={r['index']:r for r in paid}
    groups=[]
    cuts=set()
    accepted=[]
    for pos,r in enumerate(paid):
        i=r['index']
        current=[i]
        blocked=set(r['remove_indices'])
        for s in paid[pos+1:pos+9]:
            if s['index']-i>550:
                break
            owned=set(s['remove_indices'])
            if blocked&owned:
                continue
            blocked|=owned
            current.append(s['index'])
        if len(current)<3:
            continue
        at=sorted({k for j in current for k in
                   (j,j+1,max(indexed[j]['remove_indices'])+1)
                   if k>i and k<len(lines) and depth[k]==0})
        if len(at)>14:
            # Retain the earliest and latest cuts. This bounds memory above.
            at=at[:7]+at[-7:]
        cuts.update(at)
        groups.append((current,at))
    subset={i for g,_ in groups for i in g}
    rset=[r for r in paid if r['index'] in subset]
    active={j for r in rset for j in ([r['index']]+r['phase_indices']+
             [i for seq in r['nonconstant_phase_terms'].values() for i in seq])}
    print('groups',len(groups),'cuts',len(cuts),flush=True)
    v,s,one=packed_trace(ops,np.arange(1,MAX_X+1,dtype=np.uint32),active,cuts,True)
    holds={r['index'] for r in phase_records(rset,v)}
    rng=np.random.default_rng(900925)
    initial=np.unique(np.r_[np.arange(1,4097),
                            rng.integers(1,MAX_X+1,size=8192)]).astype(np.uint32)
    rejected=[]
    for selected, at in groups:
        group=[i for i in selected if i in holds]
        if len(group)!=len(selected) or len(group)<3:
            continue
        i=group[0]
        sample=initial
        discrepancy=[]
        for step in range(5):
            result=fit(group,at,v,s,sample)
            if result is None:
                break
            retained=[group[qs[0]] for cut,qs in result if cut is None]
            corrections=[(cut,qs) for cut,qs in result if cut is not None]
            failure=v[i]^xor_all(v[j] for j in retained)
            failure^=xor_all(product(s[k],qs,one) for k,qs in corrections)
            if not failure:
                accepted.append(dict(group=group,retained=retained,corrections=corrections))
                break
            discrepancy.append(failure.bit_count())
            extra=[]
            while failure and len(extra)<256:
                bit=failure&-failure
                extra.append(bit.bit_length())
                failure^=bit
            sample=np.unique(np.r_[sample,np.array(extra,dtype=np.uint32)])
        else:
            result='refinement_limit'
        if result is None or result=='refinement_limit':
            rejected.append(dict(group=group,cuts=at,rounds=discrepancy))
    output=dict(source_sha256=SOURCE_SHA,groups=len(groups),cut_count=len(cuts),
                confirmed_cleanup_records=len(holds),accepted=accepted,rejected=rejected,
                first_samples=len(initial),elapsed_s=time.monotonic()-t0)
    if accepted:
        best=min(accepted,key=lambda h:len(h['corrections']))
        c=km.Circuit(generate(lines,paid,best['group'],best['retained'],best['corrections']))
        assert c.num_qubits==circ.num_qubits
        assert c.operation_statistics().num_toffoli_like<circ.operation_statistics().num_toffoli_like
        out=args.out.parent/'candidate.kmb'
        c.to_file(out,format='kmb')
        output.update(selected=best,candidate_sha256=sha256(out.read_bytes()).hexdigest())
    args.out.write_text(json.dumps(output,indent=2)+'\n')
    print({k:len(v) if isinstance(v,list) else v for k,v in output.items()},flush=True)


if __name__=='__main__':
    main()
