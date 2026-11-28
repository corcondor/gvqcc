"""GF4096 guard regression with legal support and independent native replay."""
import json, sys
from random import Random
from functools import reduce
from operator import xor
from pathlib import Path
from collections import Counter
import numpy as np
import direct_codec as D
import verify_submission_dqi as V
import kickmix as km

G=[1]
for c in range(2048,2057):
    assert all(D.ev([c,1,1],x) for x in range(4096))
    G=D.pmul(G,[c,1,1])
def filt(s):return [reduce(xor,(D.mul(a,s[i+j]) for j,a in enumerate(G)),0) for i in range(52)]
def poly(xs):
    p=[1]
    for x in xs:p=D.pmul(p,[x,1])
    return p
def interpolation_amplitudes(xs):
    u=poly(xs); du=[a if i%2==0 else 0 for i,a in enumerate(u[1:])]
    return {x:D.inv(D.mul(D.mul(x,D.ev(G,x)),D.ev(du,x))) for x in xs}
def rk(M):
    rows=[list(r) for r in M];rank=0
    for j in range(len(rows[0])):
        pivot=next((i for i in range(rank,len(rows)) if rows[i][j]),None)
        if pivot is None:continue
        rows[pivot],rows[rank]=rows[rank],rows[pivot]
        w=rows[rank]; u=D.inv(w[j]); w=[D.mul(y,u) for y in w]
        for i in range(rank+1,len(rows)):
            r=rows[i];v=r[j]
            if v:rows[i]=[a^D.mul(b,v) for a,b in zip(r,w)]
        rank+=1
        if rank==len(rows):break
    return rank
def hankel(t,n):return [t[i:i+n] for i in range(18)]
def bm_gate(s):
    C=[1]+[0]*len(s); B=C[:]; L=0;m=1;b=1;paid=0
    for i,a in enumerate(s):
        d=a
        for j in range(1,L+1):
            if C[j] and s[i-j]:paid+=1
            d^=D.mul(C[j],s[i-j])
        if not d:m+=1;continue
        if 2*L<=i and i+1-L>=18:return False,paid,i+1
        T=C[:]; t=D.div(d,b);paid+=1
        for j in range(len(s)+1-m):
            if B[j]:paid+=1
            C[j+m]^=D.mul(t,B[j])
        if 2*L<=i:L=i+1-L;B=T;b=d;m=1
        else:m+=1
    return L<18,paid,len(s)
r=Random(334); counts=Counter(); totals=Counter()
for k in range(36):
    for _ in range(10):
        e={x:r.randrange(1,4096) for x in r.sample(range(1,4096),k)}
        t=filt(D.moments(e)); expected=min(k,18); actual=rk(hankel(t,35))
        assert expected==actual
        low,products,used=bm_gate(t);assert low==(k<18)
        counts[(k,used)]+=1;totals[k]+=products
e19=interpolation_amplitudes(list(range(1,20))); t19=filt(D.moments(e19))
assert t19[:18]==[0]*18 and t19[18]==1 and rk(hankel(t19,18))==17 and rk(hankel(t19,35))==18
e52=interpolation_amplitudes(list(range(1,53))); a17={x:a for x,a in e52.items() if x<=17};b35={x:a for x,a in e52.items() if x>17}
ta,tb=map(lambda e:filt(D.moments(e)),(a17,b35));assert ta[:51]==tb[:51] and ta[51]^tb[51]==1
assert [bm_gate(t)[0] for t in (t19,ta,tb)]==[False,True,False]
print('adversarial', [(len(e),rk(hankel(t,18)),rk(hankel(t,35)),bm_gate(t)) for e,t in [(e19,t19),(a17,ta),(b35,tb)]],flush=True)
print('classical oracle only, GF12 product mean',dict((k,totals[k]/10) for k in range(36)),flush=True)
if len(sys.argv)==1:sys.exit(0)
N=64; sp=V.ProblemSpecDQI.benchmark_instance(num_shots=N); qcs=km.Circuit.from_file(sys.argv[1]);q,b,z=map(km.array,V.validate_registers(qcs,sp)); rr=np.random.default_rng(334)
cases=[e19,a17,b35,{}]
s=np.array([D.moments(cases[i%4]) for i in range(N)])
mask=rr.integers(0,4096,size=(N,sp.m),dtype=np.uint16);mask[:32]=0
mask[32:]=np.broadcast_to(mask[33],(32,sp.m))
phase=np.array([sum((a&int(mask[i,D.LOG[x]])).bit_count() for x,a in cases[i%4].items())%2 for i in range(N)],bool)
sx=V.to_bits(s,12);mx=V.to_bits(mask,12)
for seed in (17334, 334173, 1):
    sim=km.Simulator(batch_size=N,seed=seed,debug_print=False,counting_operations=True);sim.use_same_registers_as(qcs)
    sim.write_across_shots(q,sx);sim.write_across_shots(b,mx);sim.do(qcs)
    er=[np.any(sim.read_across_shots(q)!=sx,axis=0),np.asarray(sim.read_phase_flipped_across_shots())!=phase,np.any(sim.read_across_shots(z),axis=0),np.any(sim.read_across_shots(b)!=mx,axis=0)]
    d={str(len(e)):[[int(np.count_nonzero(a[i:32:4])) for a in er],[int(np.count_nonzero(a[32+i::4])) for a in er]] for i,e in enumerate(cases)}
    print(json.dumps(dict(seed=seed,zero_then_fixed_nonzero=d,shots_per_mask=8)),flush=True)
