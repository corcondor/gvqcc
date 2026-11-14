#!/usr/bin/env python3
"""Unrestricted one-AND phase-feature synthesis over all retained live wires."""
from functools import reduce
import json
from pathlib import Path
import random
import sys
import time
import numpy as np
import score_invsqrt_retire as r
from score2_invsqrt_feature_dense import states
sys.path.insert(0,'/workspace/scratch/3815fb5fae06/score_invsqrt_solver_deps')
import z3

def search(values,target,domain,samples,timeout=30):
    qs=[q for q,v in enumerate(values) if q!=21 and v];n=len(qs)
    records=[];began=time.monotonic()
    for iteration in range(3):
        width=len(samples);one=(1<<width)-1
        sig=[sum(((values[q]>>x)&1)<<i for i,x in enumerate(samples)) for q in qs]
        ts=sum(((target>>x)&1)<<i for i,x in enumerate(samples))
        solver=z3.SolverFor('QF_BV');solver.set(timeout=int(timeout*1000),random_seed=31,max_memory=768)
        aa=[z3.Bool('a%d'%j) for j in range(n)];bb=[z3.Bool('b%d'%j) for j in range(n)];ll=[z3.Bool('l%d'%j) for j in range(n+1)]
        def form(coefs,vs,w):return reduce(lambda a,b:a^b,[z3.If(c,z3.BitVecVal(v,w),z3.BitVecVal(0,w)) for c,v in zip(coefs,vs)],z3.BitVecVal(0,w))
        ai=form(aa,[1<<j for j in range(n)],n);bi=form(bb,[1<<j for j in range(n)],n)
        solver.add(ai!=0,z3.ULT(ai,bi),z3.ULT(bi,ai^bi))
        solver.add((form(aa,sig,width)&form(bb,sig,width))^form(ll,sig+[one],width)==z3.BitVecVal(ts,width))
        t=time.monotonic();status=solver.check();record={'iteration':iteration,'samples':width,'status':str(status),'seconds':time.monotonic()-t}
        records.append(record)
        if status!=z3.sat:
            if status==z3.unknown:record['reason']=solver.reason_unknown()
            return {'status':str(status),'iterations':records,'elapsed_seconds':time.monotonic()-began}
        model=solver.model();yes=lambda b:z3.is_true(model.eval(b,model_completion=True))
        left=[q for q,b in zip(qs,aa) if yes(b)];right=[q for q,b in zip(qs,bb) if yes(b)];linear=[q for q,b in zip(qs,ll[:-1]) if yes(b)];constant=int(yes(ll[-1]))
        def xor(wires):return reduce(int.__xor__,(values[q] for q in wires),0)
        actual=(xor(left)&xor(right))^xor(linear)^(domain if constant else 0);difference=actual^target
        identity={'left':left,'right':right,'linear':linear,'constant':constant}
        if not difference:return {'status':'SAT_FULL_DOMAIN_VERIFIED','identity':identity,'iterations':records,'legal_inputs':r.MAX_X,'elapsed_seconds':time.monotonic()-began}
        bits=np.unpackbits(np.frombuffer(difference.to_bytes((r.MAX_X+8)//8,'little'),dtype=np.uint8),bitorder='little')[:r.MAX_X+1]
        counterexamples=np.flatnonzero(bits);indices=np.linspace(0,len(counterexamples)-1,min(128,len(counterexamples)),dtype=int)
        samples+=counterexamples[indices].tolist();samples=list(dict.fromkeys(samples));record['counterexamples_added']=len(indices)
    return {'status':'CEGIS_LIMIT','iterations':records,'elapsed_seconds':time.monotonic()-began}

def main():
    base=Path(__file__).parent;rng=random.Random(112959);samples=list(range(1,129))+[rng.randrange(1,r.MAX_X+1) for _ in range(384)]
    records=[]
    for item,values,domain in states():
        print(json.dumps({'starting':item['name'],'live_inputs':sum(bool(v) for q,v in enumerate(values) if q!=21)}),flush=True)
        result=search(values,values[21],domain,samples[:]);record={k:v for k,v in item.items() if k!='entry'}|result
        records.append(record);print(json.dumps(record),flush=True)
        (base/'score2_invsqrt_feature_sat.json').write_text(json.dumps({'scope':'arbitrary one-AND factors and affine remainder over every retained live wire','records':records},indent=2)+'\n')

if __name__=='__main__':main()
