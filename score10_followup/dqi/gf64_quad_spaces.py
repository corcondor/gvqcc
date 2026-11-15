#!/usr/bin/env python3
"""Enumerate quadratic scaffold spaces for GF64 cubic inverse."""
import argparse
from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path

from gf64_probe import bases, mix, probe, table, solve

def reduce_against(value, basis):
    for key, (row, _) in basis:
        if value >> key & 1:
            value ^= row
    return value

def rem_basis(items):
    return sorted(bases(items)[0].items(),reverse=True)

def quadratic_anf(values):
    monomials = [(1 << i) | (1 << j) for i in range(6) for j in range(i+1,6)]
    def coefficient(index):
        i = index & -index
        j = index ^ i
        return ((values >> index) ^ (values >> i) ^ (values >> j) ^ values) & 1
    return sum(coefficient(index)<<k for k,index in enumerate(monomials))

def quadratic_spaces(source):
    import sys
    sys.path.insert(0,source)
    import kickmix as km
    import cubic_inverse130 as cubic
    bits=[table(lambda x:(x>>i)&1) for i in range(6)]
    field=km.GF2Field(6)
    adjugate=[table(lambda x:(field.pow(x,20)>>i)&1) for i in range(6)]
    target=rem_basis([quadratic_anf(t) for t in adjugate])
    assert len(target)==6
    fields={}
    for a,b in combinations(range(1,64),2):
        truth=mix(bits,a)&mix(bits,b)
        q=quadratic_anf(truth)
        fields.setdefault(q,(a,b,truth))
    assert len(fields)==651
    buckets=defaultdict(list)
    for q in fields:
        buckets[reduce_against(q,target)].append(q)
    assert not buckets[0]
    viable_seven = [space for space,forms in buckets.items() if len(bases(forms)[0]) >= 7]
    quotients=sorted({reduce_against(x,target) for x in range(1<<15)}-{0})
    assert len(quotients)==511
    spaces=[]
    ranks=Counter()
    for u,v in combinations(quotients,2):
        w=u^v
        if w<v:
            continue
        forms=buckets[u]+buckets[v]+buckets[w]
        if len(forms)<8:
            ranks[len(forms)]+=1
            continue
        independent=[]
        linear=[]
        for form in forms:
            if solve(form,bases(independent)[0]) is None:
                independent.append(form)
                linear.append(fields[form])
        r=len(independent)
        ranks[r]+=1
        if r==8:
            spaces.append((u,v,linear))
    assert sum(ranks.values())==43435
    print('quotient bucket distribution',Counter(len(v) for v in buckets.values()))
    print('forms count or exact rank distribution',ranks, 'rank7 scaffold spaces',len(viable_seven),'rank8',len(spaces),flush=True)
    assert not viable_seven
    core,_,_,_=probe(source)
    norms=core[-2:]
    found=[]
    for u,v,terms in spaces:
        sig=[*core[:7],*(term[2] for term in terms)]
        remainder=rem_basis(sig)
        norm_classes=[reduce_against(mix(norms,mask),remainder) for mask in (1,2,3)]
        candidates=[None]*3
        for control in range(1,64):
            first=mix(bits,control)
            right_space,_=bases([reduce_against(first&word,remainder) for word in sig[1:]])
            for i,target_class in enumerate(norm_classes):
                if candidates[i] is None:
                    right=solve(target_class,right_space)
                    if right is not None:
                        output_mask=i+1
                        correction=solve((first&mix(sig[1:],right))^mix(norms,output_mask),bases(sig)[0])
                        assert correction is not None
                        candidates[i]=dict(first=control,second=right,
                                           output_mask=output_mask,correction=correction)
        if sum(c is not None for c in candidates)>=2:
            found.append(dict(u=u,v=v,quadratics=[term[:2] for term in terms],norm_products=candidates))
            print('Found 2-gate norm scaffold',found[-1],flush=True)
    return dict(status='COMPLETE',candidates=found,rank7_spaces=len(viable_seven),
                rank8_spaces=len(spaces),rank_histogram=dict(ranks),
                rank8_bases=[dict(plane=[u,v],terms=[term[:2] for term in terms]) for u,v,terms in spaces])

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    ans=quadratic_spaces(args.source)
    args.output.write_text(json.dumps(ans,indent=2)+'\n')
