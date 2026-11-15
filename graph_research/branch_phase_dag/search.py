#!/usr/bin/env python3
"""Search dependency-closed AND banks for outcome-dependent phase synthesis.
The 32 measurement outcomes are legitimate classical feed-forward, not test
inputs. No verifier seed, circuit-hash reward, or sampled correctness is used.
"""
import argparse,itertools,json,random,time
from pathlib import Path
from build import ONE,FUNCTIONS,bits,branch,verify_branch

def insert(basis,value):
    while value:
        pivot=value.bit_length()-1
        if basis[pivot]: value^=basis[pivot]
        else: basis[pivot]=value; return

def contains(basis,value):
    while value:
        pivot=value.bit_length()-1
        if basis[pivot]: value^=basis[pivot]
        else: return False
    return True

def quadratic_span(features):
    basis=[0]*64;insert(basis,ONE)
    for i,f in enumerate(features):
        insert(basis,f)
        for g in features[:i]:insert(basis,f&g)
    return basis

def search(banks,seed,initial=None):
    rng=random.Random(seed);data=[bits(i) for i in range(6)];targets=[]
    for outcome in range(32):
        t=0
        for j,f in enumerate(FUNCTIONS):
            if outcome>>j&1:t^=f
        targets.append(t)
    valid=[m for m in range(256) if (not m&8 or m&7) and (not m&128 or m&112)]
    valid.sort(key=int.bit_count)
    plans={} if initial is None else json.loads(Path(initial).read_text())['plans']
    best=[0]+[plans.get(str(i),{}).get('cost',99) for i in range(1,32)]
    start=time.monotonic();partitions=[p for p in itertools.combinations(range(6),3) if 0 in p]
    for step in range(banks):
        if step<10:
            ids=list(partitions[step])+[i for i in range(6) if i not in partitions[step]]
            forms=[1<<i for i in ids];fs=[data[i] for i in ids]
        else:
            forms=[1<<i for i in range(6)];fs=data.copy()
            for _ in range(24):
                a,b=rng.sample(range(6),2);forms[b]^=forms[a];fs[b]^=fs[a]
        monomials=[]
        for off in (0,3):
            a,b,c=fs[off:off+3];monomials.extend((a&b,a&c,b&c,a&b&c))
        for mask in valid:
            cost=mask.bit_count();needed=[i for i in range(1,32) if best[i]>cost]
            if not needed:break
            span=quadratic_span(data+[monomials[j] for j in range(8) if mask>>j&1])
            for i in needed:
                if contains(span,targets[i]):
                    best[i]=cost;plans[str(i)]={'forms':forms.copy(),'mask':mask,'cost':cost}
        if step%1000==0:print(json.dumps({'banks':step,'mean':sum(best)/32,'seconds':time.monotonic()-start}),flush=True)
    if max(best)==99:raise RuntimeError('Search did not find every outcome')
    for i in range(1,32):verify_branch(branch(targets[i],plans[str(i)]['forms'],plans[str(i)]['mask']),targets[i])
    return {'plans':plans,'branch_costs':best,'mean':sum(best)/32,'sum':sum(best),'banks':banks,'seed':seed,'seconds':time.monotonic()-start,'exact_phase_proof':'PASS','official_verifier_run':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--banks',type=int,default=1500);p.add_argument('--seed',type=int,default=20261116);p.add_argument('--initial',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.banks<=0 or a.output.exists():raise ValueError('Positive bank count and fresh output required')
    r=search(a.banks,a.seed,a.initial);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='plans'},indent=2))
