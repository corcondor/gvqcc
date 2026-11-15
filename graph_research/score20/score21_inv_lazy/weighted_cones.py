"""Trade an unconditional operation for cheaper measurement-conditioned phases."""
import argparse
from bisect import bisect_right
from collections import Counter,defaultdict
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path

import kickmix as km
import numpy as np

from lazy import (PIN,DOMAIN,PAID,parse,initial_state,make_trace,tracks_for,
                  find_cone,product,quadratic_phase)

def insertion_ok(site,guards,track):
    scope,_,writes,cond=track
    existing={cond[q] for q in scope[site]}
    required=set(guards)
    return existing<=required and all(bisect_right(writes.get(b,[]),site)==v
                                      for b,v in required-existing)

def phase_basis(state,n,at):
    s=[(i,v) for i,v in enumerate(state) if v not in (0,n)]
    desc=[]
    basis={}
    for expr,value in [("NEG",n)]+[(f"Z q{i}",v) for i,v in s]+[
            (f"CZ q{i} q{j}",a&b) for (i,a),(j,b) in combinations(s,2)]:
        coeff=1<<len(desc)
        while value:
            p=value.bit_length()-1
            if p not in basis:
                basis[p]=value,coeff
                desc.append((at,expr))
                break
            v,c=basis[p]
            value^=v
            coeff^=c
    return basis,desc,s

def rid(v,basis):
    c=0
    rest=0
    while v:
        p=v.bit_length()-1
        node=basis.get(p)
        if node:
            w,k=node
            v^=w
            c^=k
        else:
            h=1<<p
            rest^=h
            v^=h
    return rest,c

def dual_filter(basis,n,required,count=8):
    cov=[]
    for k in range(n-1,-1,-1):
        if k in basis or not required>>k&1:
            continue
        code=1<<k
        for p in sorted(basis):
            if (code&basis[p][0]).bit_count()&1:
                code^=1<<p
        cov.append(code)
        if len(cov)>=count:
            break
    assert cov
    return cov

def try_cubic(pred,state,mask,cut):
    basis,desc,cols=phase_basis(state,mask,cut)
    rest,coef=rid(pred,basis)
    if not rest:
        return [desc[j] for j in range(len(desc)) if coef>>j&1]
    witness=dual_filter(basis,mask.bit_length(),rest)
    for (a,x),(b,y),(c,z) in combinations(cols,3):
        v=x&y&z
        if v and all((v&w).bit_count()&1 for w in witness):
            t,co=rid(v^pred,basis)
            if not t:
                return [(cut,f'CCZ q{a} q{b} q{c}'),
                        *[desc[j] for j in range(len(desc)) if co>>j&1]]
    return

def try_dense_cubic(pred,state,mask,cut,a,b):
    basis,desc,cols=phase_basis(state,mask,cut)
    product_ab=state[a]&state[b]
    for q,v in cols:
        if q in (a,b):
            continue
        value=v&product_ab
        coeff=1<<len(desc)
        while value:
            p=value.bit_length()-1
            if p not in basis:
                basis[p]=value,coeff
                desc.append((cut,f'FACTOR q{q}'))
                break
            v,c=basis[p]
            value^=v
            coeff^=c
    residual,c=rid(pred,basis)
    if residual:
        return None
    terms=[]
    parity=[]
    for j,(i,label) in enumerate(desc):
        if not c>>j&1:
            continue
        if label.startswith('FACTOR '):
            parity.append(label.split()[-1])
        else:
            terms.append((i,label))
    if parity:
        terms.append((cut,f'PARITY_CCZ q{a} q{b} '+" ".join(parity)))
    return terms

def max_probability(gates,track,terms):
    scopes,_,writes,_=track
    reliable=set()
    for b,v in terms:
        if not v or v>len(writes[b]):
            continue
        idx=writes[b][v-1]
        if gates[idx][0]=='HMR' and not scopes[idx]:
            reliable.add(idx)
    return Fraction(1,1<<len(reliable))

def trial(lines,gates,data,xs,track,start,span,counters):
    basics=find_cone(lines,gates,data,xs,track,start,span,counters)
    if basics is None:
        return None
    end,events,states,n=basics
    out=[]
    cost=Fraction(0)
    bad=[]
    for k,site,p in events:
        if not insertion_ok(site,k,track):
            return None
        view=states[site]
        terms=quadratic_phase(p,[(site,view)],n)
        if terms is None:
            delta=max_probability(gates,track,k)
            cost+=delta
            if cost>=1:
                counters['budget']+=1
                return None
            bad.append((k,site,p,view))
        else:
            out.append(dict(guards=k,site=site,terms=terms))
    if not bad:
        counters['free']+=1
    for k,site,p,view in bad:
        a,b,*_=gates[start][1]
        terms=try_dense_cubic(p,view,n,site,a,b)
        if terms is None:
            terms=try_cubic(p,view,n,site)
        if terms is None:
            counters['no_cubic']+=1
            return None
        out.append(dict(guards=k,site=site,terms=terms))
    counters['paid_savings_model']+=1
    return dict(start=start,end=end,corrections=out,run_on=[],pair=None,removed=lines[start],
                expected_cost_bound=str(cost),expected_saving_bound=str(1-cost))

def construct(lines,gates,track,selected):
    after=defaultdict(list)
    removed={row['start'] for row in selected}
    for row in selected:
        for r in row['corrections']:
            for j,label in r['terms']:
                active={track[3][i] for i in track[0][j]}
                extra=sorted(set(map(tuple,r['guards']))-active)
                for bit,_ in extra:
                    after[j].append(f'PUSH_CONDITION if {bit}')
                if label.startswith('PARITY_CCZ '):
                    _,a,b,c,*parity=label.split()
                    geom=[f'CX {q} {c}' for q in parity]
                    after[j]+=geom+[f'CCZ {a} {b} {c}']+geom[::-1]
                else:
                    after[j].append(label)
                after[j]+=['POP_CONDITION']*len(extra)
    result=[]
    for i,l in enumerate(lines):
        if i not in removed:
            result.append(l)
        result.extend(after[i])
    return '\n'.join(result)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--span',type=int,default=1400)
    p.add_argument('--target',type=int,nargs='+')
    args=p.parse_args()
    assert sha256(args.source.read_bytes()).hexdigest()==PIN
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    g=list(map(parse,lines))
    track=tracks_for(g,lines)
    rng=np.random.default_rng(167131)
    xs=np.unique(np.r_[np.arange(1,1200),rng.integers(1,DOMAIN+1,1600),DOMAIN]).astype(np.uint32)
    trace=list(make_trace(g,xs))
    counters=Counter()
    hits=[]
    for i,(op,qs,guard) in enumerate(g):
        if op in PAID and not track[0][i] and (args.target is None or i in args.target):
            hit=trial(lines,g,trace,xs,track,i,args.span,counters)
            if hit is not None:
                hits.append(hit)
                print('sample',i,hit['expected_saving_bound'],len(hit['corrections']),flush=True)
    print('counts',counters,'hits',len(hits),flush=True)
    valid=[]
    if hits:
        whole=np.arange(1,DOMAIN+1,dtype=np.uint32)
        need={j for r in hits for j in range(r['start']-1,r['end']+1)}
        full={j:v for j,v in enumerate(make_trace(g,whole)) if j in need}
        for row in hits:
            if find_cone(lines,g,full,whole,track,row['start'],args.span,Counter(),approved=row):
                valid.append(row)
                print('full domain',row['start'],row['expected_saving_bound'],flush=True)
    selected=[]
    for row in sorted(valid,key=lambda x:x['end']):
        if not selected or row['start']>selected[-1]['end']:
            selected.append(row)
    report=dict(source=PIN,samples=len(xs),counts=counters,hits=hits,validated=valid,selected=selected)
    if selected:
        q=km.Circuit(construct(lines,g,track,selected))
        assert q.num_qubits==46
        dest=args.out.with_suffix('.kmb')
        q.to_file(dest,format='kmb')
        report['candidate_sha']=sha256(dest.read_bytes()).hexdigest()
        report['exact_minimum_expected_savings']=str(sum(Fraction(r['expected_saving_bound']) for r in selected))
    args.out.write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':
    main()
