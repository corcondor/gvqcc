"""Route a cached product through rank-deficient logical registers."""
import argparse
from bisect import bisect_left
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import kickmix as km

from conditional_cache import MAX_X, SOURCE_SHA, advance, columns, enumerate_sample, gate, info

def dependency(values, mask):
    """Each relation uses bit 0 for the constant and q+1 for wire q."""
    basis = {}
    relations = []
    for i,value in enumerate((mask,*values)):
        support = 1 << i
        while value:
            c = value.bit_length()-1
            if c not in basis:
                basis[c]=value,support
                break
            v, f = basis[c]
            value ^= v
            support ^= f
        else:
            relations.append(support)
    return relations

def relation(dep, q, avoid=None):
    x = 1 << (q+1)
    b = (1 << (avoid+1)) if avoid is not None else 0
    hit = aux = 0
    for v in dep:
        if v&x:
            if not v&b:
                return v^x
            hit=v
        elif v&b:
            aux=v
    if hit and aux:
        return hit^aux^x
    return None

def affine_value(values, target, mask, skip=None):
    bases={mask.bit_length()-1:(mask,1)}
    for j,v in enumerate(values):
        if j==skip:
            continue
        c=1<<(j+1)
        while v:
            p=v.bit_length()-1
            if p not in bases:
                bases[p]=v,c
                break
            a,b=bases[p]
            v^=a
            c^=b
    coeff=0
    while target:
        p=target.bit_length()-1
        if p not in bases:
            return None
        a,b=bases[p]
        target^=a
        coeff^=b
    return coeff

def terms_at(w, p, ordered):
    orig = [(0,())]
    orig += [(v,(q,)) for q,v in ordered]
    orig += [(u&v,(q,r)) for j,(q,v) in enumerate(ordered) for r,u in ordered[:j]]
    basis={}
    for j,(v,qs) in enumerate(orig):
        if not j:
            v=w
        m=1<<j
        while v:
            piv=v.bit_length()-1
            if piv not in basis:
                basis[piv]=(v,m)
                break
            x,s=basis[piv];v^=x;m^=s
    s=0
    while p:
        piv=p.bit_length()-1
        if piv not in basis:
            return None
        v,m=basis[piv];p^=v;s^=m
    return [t for j,(_,t) in enumerate(orig) if s>>j&1]

def routes(lines, ops, children, owner, refs, x, distance):
    pairs, const, states, mask=enumerate_sample(lines,ops,children,owner,refs,x,distance)
    records = []
    counts = Counter()
    @lru_cache(maxsize=None)
    def rel(cut):
        return dependency(states[cut],mask)
    for p,i in pairs:
        counts['equal_product_pairs']+=1
        begin,stop=owner[i],children[owner[i]]+1
        a,b,t=ops[p][1]
        pred=states[p][a]&states[p][b]
        correction=terms_at(mask,pred,list(enumerate(states[stop])))
        if correction is None:
            continue
        counts['fit_quadratic_correction']+=1
        def pick(at,old=None):
            choices=[]
            for q,uses in enumerate(refs):
                if q==old:
                    continue
                expr=relation(rel(at),q,old)
                orig_old=relation(rel(at),old,q) if old is not None else 0
                if expr is None or orig_old is None:
                    continue
                k=bisect_left(uses,at)
                until=uses[k] if k<len(uses) else len(ops)
                if until>at:
                    choices.append((until,q,expr,orig_old))
            return choices
        @lru_cache(maxsize=None)
        def build(q, until):
            if until>=stop:
                close=relation(rel(stop),q)
                if close is not None:
                    return [],(q,close)
            until=min(until,begin)
            for cut in range(until,p,-1):
                if owner[cut] is not None and cut!=begin:
                    continue
                for nxt,r,expr,restore in sorted(pick(cut,q),reverse=True):
                    if nxt<=until:
                        continue
                    if ans:=build(r,nxt):
                        h,fin=ans
                        return [(cut,q,r,restore,expr)]+h,fin
            return None
        for j in range(begin,p,-1):
            if owner[j] is not None and j!=begin:
                continue
            if affine_value(states[j],pred,mask) is None:
                continue
            for until,q,initial,_ in sorted(pick(j),reverse=True):
                src=affine_value(states[j],pred,mask,skip=q)
                if src is None:
                    continue
                cand=build(q,until)
                if cand:
                    hops,fin=cand
                    if any(cut<j for cut,*_ in hops):
                        continue
                    records.append(dict(producer=p,consumer=i,branch_begin=begin,branch_end=stop,
                                        start=j,src=src,initial=(q,initial),hops=hops,
                                        final=fin,correction=correction))
                    break
            else:
                continue
            break
    return counts,records

def aff_code(target, coeff):
    code = ['X q'+str(target)] if coeff&1 else []
    for q in range(46):
        if coeff>>(q+1)&1:
            assert q!=target
            code.append(f'CX q{q} q{target}')
    return code

def patch(lines,ops,plans):
    active={j for r in plans for j in range(r['start'],r['branch_end']+1)}
    active.update(r['producer'] for r in plans)
    m = (1<<MAX_X)-1
    baseline=columns(np.arange(1,MAX_X+1,dtype=np.uint32))
    data={}
    for i,(op,qs) in enumerate(ops):
        if i in active:
            data[i]=baseline[:]
        advance(op,qs,baseline,m)
    chosen=[]
    fresh=max(int(b) for l in lines for b in re.findall(r'\bb(\d+)\b',l))+1
    replacements={}
    inserts={}
    last=-1
    for r in sorted(plans,key=lambda z:z['branch_end']):
        p,i,start,stop=(r[k] for k in ('producer','consumer','start','branch_end'))
        if start<=last:
            continue
        a,b,t=ops[p][1]
        prod=data[p][a]&data[p][b]
        def expression(cut,expr):
            v=m if expr&1 else 0
            for a in range(46):
                if expr>>(a+1)&1:
                    v ^= data[cut][a]
            return v
        def check(cut,q,expr):
            return expression(cut,expr)==data[cut][q]
        if expression(start,r['src']) != prod:
            continue
        h, initial=r['initial']
        if not check(start,h,initial):
            continue
        if any(not check(pos,old,form0) or not check(pos,new,form1)
               for pos,old,new,form0,form1 in r['hops']):
            continue
        h2,final=r['final']
        if not check(stop,h2,final):
            continue
        c,d,t2=ops[i][1]
        if data[i][c]&data[i][d]!=prod:
            continue
        off=0
        for pair in r['correction']:
            a=m
            for q in pair:
                a &= data[stop][q]
            off ^= a
        if off!=prod:
            continue
        sl = {start:aff_code(h,initial^r['src'])}
        hop_at={}
        for pos,old,new,form0,form1 in r['hops']:
            sl[pos]=sl.get(pos,[])+aff_code(new,form1)+[f'CX q{old} q{new}',f'CX q{new} q{old}']+aff_code(old,form0)
            hop_at[pos]=new
        tag=f'b{fresh}'
        sl[stop]=[f'HMR q{h2} {tag}']+aff_code(h2,final)
        for term in r['correction']:
            text=['NEG','Z','CZ'][len(term)]
            if term:
                text+=' '+' '.join(f'q{q}' for q in term)
            sl[stop].append(f'{text} if {tag}')
        local_replace={i:[f'CX q{h2} q{t2}']}
        actual=data[start][:]
        owner=-1
        for j in range(start,stop+1):
            for op,qs in map(gate,sl.get(j,[])):
                advance(op,qs,actual,m)
            if j==start:
                owner=h
            owner=hop_at.get(j,owner)
            if j==stop:
                assert actual==data[stop]
                break
            if j in local_replace:
                assert owner==h2 and owner not in ops[j][1]
                for op,qs in map(gate,local_replace[j]):
                    advance(op,qs,actual,m)
            else:
                assert owner not in ops[j][1]
                advance(*ops[j],actual,m)
            assert actual[owner]==prod
            assert all(v==w for q,(v,w) in enumerate(zip(actual,data[j+1])) if q!=owner)
        chosen.append(r)
        replacements.update(local_replace)
        inserts.update(sl)
        last=stop
        fresh+=1
    new=[]
    for i,l in enumerate(lines):
        new.extend(inserts.get(i,[]))
        new.extend(replacements.get(i,[l]))
    return '\n'.join(new)+'\n',chosen

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    ops=list(map(gate,lines))
    rng=np.random.default_rng(668)
    xs=np.unique(np.r_[np.arange(1,500),rng.integers(1,MAX_X+1,2500),MAX_X]).astype(np.uint32)
    counts,candidates=routes(lines,ops,*info(lines,ops),xs,1600)
    print(counts,'sample plans',len(candidates),flush=True)
    selected=[]
    if candidates:
        new,selected=patch(lines,ops,candidates)
        print('full exact',len(selected),flush=True)
        if selected:
            kmb=args.out.with_suffix('.kmb')
            c=km.Circuit(new)
            assert c.num_qubits==46 and c.operation_statistics().num_toffoli_like==1550-len(selected)
            c.to_file(kmb,format='kmb')
            print('candidate SHA',hashlib.sha256(kmb.read_bytes()).hexdigest(),flush=True)
    args.out.write_text(json.dumps(dict(source=SOURCE_SHA,counts=counts,legal_inputs=MAX_X,
                                       sample_plans=candidates,selected=selected),indent=2)+'\n')

if __name__=='__main__':
    main()
