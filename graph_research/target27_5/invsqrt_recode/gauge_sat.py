"""Solve globally for branch-marker masks with coherent data and sign transport."""
import argparse
from functools import reduce
import hashlib
import json
from pathlib import Path

import kickmix as km
import numpy as np
import z3

from gauge_probe import MAX_X, SOURCE_SHA, gate, physical_trace, propagate
from peak_probe import dependencies, snapshots

def xor(*xs):
    if not xs:
        return z3.BoolVal(False)
    return reduce(z3.Xor, xs)

def toggle_by(d,signature,m):
    return [d[q] if signature>>q&1 else z3.Not(d[q]) for q in range(len(d))]

def solve_interval(ops,states,mask,start,stop,lo,signs,timeout):
    s=z3.SolverFor('QF_FD')
    s.set(timeout=timeout)
    f=[z3.Bool(f'g{q}') if q!=25 else z3.BoolVal(False) for q in range(46)]
    d=f[:]
    stack=[]
    def update(i,q,form):
        tmp=z3.Bool(f'u{i}_{q}')
        s.add(tmp==form)
        d[q]=tmp
    def require_consistent(i,qs):
        nonlocal d
        patterns={}
        for j in range(63):
            old=tuple((states[i][q]>>j)&1 for q in qs)
            if old not in patterns:
                values=[z3.Not(d[q]) if v else d[q] for q,v in zip(qs,old)]
                applied=z3.And(*values)
                patterns[old] = z3.Not(applied) if all(old) else applied
        top,*other=patterns.values()
        for b in other:
            s.add(b==top)
        return top
    for i in range(start,stop):
        op,qs=ops[i]
        assert 25 not in qs
        if op=='PUSH_CONDITION':
            stack.append(d[:])
        elif op=='POP_CONDITION':
            orig=stack.pop()
            for a,b in zip(orig,d):
                if not a.eq(b):
                    s.add(a==b)
            d=orig
        elif op=='CX':
            a,b=qs; update(i,b,xor(d[a],d[b]))
        elif op=='SWAP':
            a,b=qs; d[a],d[b]=d[b],d[a]
        elif op=='CCX':
            a,b,t=qs
            g=require_consistent(i,(a,b))
            update(i,t,xor(d[t],g))
        elif op=='CSWAP':
            a,b,t=qs
            signatures=set((states[i][a]>>k&1,(states[i][b]^states[i][t])>>k&1) for k in range(63))
            y=xor(d[b],d[t])
            def select(a0,y0):
                h=z3.And(z3.Not(d[a]) if a0 else d[a],z3.Not(y) if y0 else y)
                return z3.Not(h) if (a0 and y0) else h
            h,*fs=[select(*t0) for t0 in signatures]
            for z in fs:
                s.add(z==h)
            update(i,b,xor(d[b],h));update(i,t,xor(d[t],h))
        elif op=='HMR':
            q,=qs
            d[q]=z3.BoolVal(False)
        elif op=='R':
            q,=qs
            s.add(z3.Not(d[q]))
        elif signs and op in {'Z','CZ','CCZ','Z_POW'}:
            debt=require_consistent(i,qs)
            if op=='Z_POW':
                s.add(z3.Not(debt))
    assert not stack
    if lo:
        projections=[xor(*(d[j] for j in range(46) if u>>(j+1)&1)) for u in lo]
        s.add(z3.Or(*projections))
    else:
        s.add(z3.Or(*d))
    answer=s.check()
    if answer!=z3.sat:
        return dict(result=str(answer).upper(),reason=s.reason_unknown() if answer==z3.unknown else None)
    m=s.model()
    origins=[q for q,a in enumerate(f) if z3.is_true(m.eval(a,model_completion=True))]
    result=[q for q,a in enumerate(d) if z3.is_true(m.eval(a,model_completion=True))]
    if signs:
        final,d0,status,stats=propagate(ops,states,mask,sum(1<<q for q in origins),start,stop)
        assert final==stop and status=='success'
        assert d0==sum(1<<q for q in result)
        assert not stats.get('nonconstant_sign_offsets')
    return dict(result='SAT',start_mask=origins,finish_mask=result)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--timeout',type=int,default=9000)
    args=p.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    ops=list(map(gate,lines))
    small,mask=physical_trace(ops)
    cases=((632,7630),(632,7644),(8400,23638))
    reached,one=snapshots(ops,np.arange(1,MAX_X+1,dtype=np.uint32),{b for a,b in cases})
    rows=[]
    for a,b in cases:
        no25=list(reached[b])
        no25[25]=0
        affine=dependencies(no25,one)
        for constrain_end in (False,True):
            row=dict(start=a,stop=b,decode_required=constrain_end,available_affine_dependencies=len(affine))
            if constrain_end and not affine:
                row.update(result='NO_AFFINE_KERNEL')
            else:
                row.update(solve_interval(ops,small,mask,a,b,affine if constrain_end else [],True,args.timeout))
            print(row,flush=True)
            rows.append(row)
    args.out.write_text(json.dumps(dict(source=SOURCE_SHA,cases=rows),indent=2)+'\n')

if __name__=='__main__':
    main()
