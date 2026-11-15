#!/usr/bin/env python3
"""Find eligible cleanup pairs whose difference is a Clifford phase."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'graph_inv'))
from temporal_phase_graph import DATA, MAX_X, SOURCE_SHA, advance, columns, gate, product

PAID={'CCX','CSWAP','CCZ'}


def packed_trace(ops, xs, active, cuts, check=False):
    n=len(xs)
    one=(1<<n)-1
    v=columns(xs)
    stack=[]
    snapshots={}
    values={}
    for i,(op,qs) in enumerate(ops):
        if i in cuts:
            assert not stack
            snapshots[i]=v[:]
        if i in active:
            values[i]=product(v,qs,one)
        if op=='PUSH_CONDITION':
            stack.append(v[:])
        elif op=='POP_CONDITION':
            before=stack.pop()
            assert before==v, i
        elif op in DATA:
            if op=='R':
                assert not v[qs[0]],i
            advance(op,qs,v,one)
    assert not stack
    if check:
        assert v==columns(xs)
    return values,snapshots,one


def make_basis(vectors, one):
    features=[]
    basis={}
    unique=set()
    def add(w, inds):
        if not w or w in unique:
            return
        unique.add(w)
        coeff=0
        while w:
            leading=w.bit_length()-1
            if leading not in basis:
                basis[leading]=w,coeff^(1<<len(features))
                features.append(inds)
                return
            h,c=basis[leading]
            w^=h
            coeff^=c
    add(one,())
    for i,w in enumerate(vectors):
        add(w,(i,))
    for i,w in enumerate(vectors):
        if w:
            for j,u in enumerate(vectors[:i]):
                add(w&u,(j,i))
    return basis,features


def solve(basis, w):
    coeff=0
    while w:
        k=w.bit_length()-1
        if k not in basis:
            return None
        h,c=basis[k]
        w^=h
        coeff^=c
    return coeff


def xor_all(xs):
    v=0
    for x in xs:
        v^=x
    return v


def phase_records(records, data):
    """Keep only independently dead correction scopes with exact sampled phase."""
    accepted=[]
    for r in records:
        f=data[r['index']]
        if f!=xor_all(data[j] for j in r['phase_indices']):
            continue
        if any(xor_all(data[j] for j in idxs) for idxs in r['nonconstant_phase_terms'].values()):
            continue
        accepted.append(r)
    return accepted


def check_exact(ops, records, hits):
    sample=np.arange(1,MAX_X+1,dtype=np.uint32)
    cuts={h['cut'] for h in hits}
    ids={h[k] for h in hits for k in ('earlier','later')}
    active={j for r in records if r['index'] in ids for j in
            ([r['index']]+r['phase_indices']+
             [i for seq in r['nonconstant_phase_terms'].values() for i in seq])}
    v,s,one=packed_trace(ops,sample,active,cuts,True)
    verified=phase_records([r for r in records if r['index'] in ids],v)
    okay={r['index'] for r in verified}
    out=[]
    for h in hits:
        i,j=h['earlier'],h['later']
        if i in okay and j in okay:
            f=v[i]^v[j]
            f^=xor_all(product(s[h['cut']],qs,one) for qs in h['quadratics'])
            if not f:
                out.append(h)
    return out


def render(lines, earlier, later, hit):
    fresh=max(map(int,re.findall(r'\bb(\d+)\b','\n'.join(lines))))+1
    m=f'b{fresh}'
    new=f'b{fresh+1}'
    src=[]
    rem=set(earlier['remove_indices'])
    owners=set(later['remove_indices'])
    b0=earlier['bit']
    b1=later['bit']
    for i,line in enumerate(lines):
        if i==hit['cut']:
            src.extend(f'{("NEG","Z","CZ")[len(qs)]}{"".join(f" q{q}" for q in qs)} if {m}'
                       for qs in hit['quadratics'])
        if i in rem:
            continue
        if i in owners and ' if '+b1 in line:
            line=re.sub(rf' if {b1}$',f' if {new}',line)
        src.append(line)
        if i==earlier['index']:
            src.extend((f'BIT_STORE0 {m}',f'BIT_INVERT {m} if {b0}'))
        if i==later['index']:
            src.extend((f'BIT_STORE0 {new}',f'BIT_INVERT {new} if {m}',
                        f'BIT_INVERT {new} if {b1}'))
    return '\n'.join(src)+'\n'


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
    h=sha256(args.source.read_bytes()).hexdigest()
    assert h==SOURCE_SHA
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
    records=[r for r in raw if any(ops[j][0] in PAID for j in r['remove_indices'])]
    active={j for r in records for j in ([r['index']]+r['phase_indices']+
             [i for seq in r['nonconstant_phase_terms'].values() for i in seq])}
    cuts={z for r in records for z in
          (r['index']+1,max(r['remove_indices'])+1) if z<len(lines)}
    rng=np.random.default_rng(552019)
    inputs=np.unique(np.r_[np.arange(1,513),
                           rng.integers(1,MAX_X+1,size=3584)]).astype(np.uint32)
    values,frames,one=packed_trace(ops,inputs,active,cuts)
    usable=phase_records(records,values)
    bases={i:make_basis(v,one) for i,v in frames.items()}
    hits=[]
    checked=0
    for i, a in enumerate(usable):
        for b in usable[i+1:]:
            if set(a['remove_indices'])&set(b['remove_indices']):
                continue
            for cut in (a['index']+1,b['index']+1,max(b['remove_indices'])+1):
                if cut not in bases:
                    continue
                checked+=1
                basis,features=bases[cut]
                coeff=solve(basis,values[a['index']]^values[b['index']])
                if coeff is not None:
                    hits.append(dict(earlier=a['index'],later=b['index'],cut=cut,
                                     quadratics=[f for j,f in enumerate(features) if coeff>>j&1]))
    exact=check_exact(ops,usable,hits) if hits else []
    info=dict(baseline_sha256=h, paid_correction_records=len(records), sampled_usable_records=len(usable),
              samples=len(inputs), checked=checked, sample_hits=hits, exact_hits=exact,
              seconds=time.monotonic()-t0)
    if exact:
        best=min(exact,key=lambda rec:len(rec['quadratics']))
        ids={r['index']:r for r in usable}
        alt=km.Circuit(render(lines,ids[best['earlier']],ids[best['later']],best))
        assert alt.num_qubits==circ.num_qubits
        assert alt.operation_statistics().num_toffoli_like < circ.operation_statistics().num_toffoli_like
        out=args.out.parent/'candidate.kmb'
        alt.to_file(out,format='kmb')
        info.update(candidate_sha256=sha256(out.read_bytes()).hexdigest(),chosen=best)
    args.out.write_text(json.dumps(info,indent=2)+'\n')
    print({k:len(v) if isinstance(v,list) else v for k,v in info.items()},flush=True)


if __name__=='__main__':
    main()
