"""Classify the exact #257 wrong syndrome using field minimal recurrences."""
import argparse, collections, json
from pathlib import Path
import numpy as np
import kickmix as km
import paired_mask as P

KS=(3134,3169,3257,3302,3384,3431,3519,3552,3592,3633,3671,3727,3792,3854,3921,3977,4054)

def rem(f,q):
    f=f[:]
    while f and not f[-1]:f.pop()
    while len(f)>=len(q):
        j=len(f)-len(q); a=P.mul(f[-1],P.inv(q[-1]))
        for i,v in enumerate(q):f[j+i]^=P.mul(a,v)
        while f and not f[-1]:f.pop()
    return f

def quotient(f,q):
    f=f[:]; out=[0]*max(0,len(f)-len(q)+1)
    while len(f)>=len(q):
        j=len(f)-len(q); a=P.mul(f[-1],P.inv(q[-1]))
        out[j]=a
        for i,v in enumerate(q):f[j+i]^=P.mul(a,v)
        while f and not f[-1]:f.pop()
    assert not f
    return out


def inspect(d):
    p=P.bm(d)
    if len(p)<=1:return dict(degree=0,roots=0,poles=[],repeated=False,zero_root=False)
    d1=[p[i] if i%2 else 0 for i in range(1,len(p))]
    while d1 and not d1[-1]:d1.pop()
    a,b=p,d1
    while b:a,b=b,rem(a,b)
    z=np.zeros(4095,np.int32)
    for t in reversed(p):z=P.vm(z,P.EXP)^t
    f=p.copy()
    mult={}
    for k in KS:
        q=[k,1,1]
        while len(f)>=len(q) and not rem(f,q):
            f=quotient(f,q);mult[k]=mult.get(k,0)+1
    return dict(degree=len(p)-1,roots=int((z==0).sum()),poles=list(mult),multiplicity=mult,
                unaccounted_degree=len(f)-1,repeated=len(a)>1,zero_root=p[0]==0)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tape',type=Path);ap.add_argument('archive',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args()
    import hashlib
    assert hashlib.file_digest(a.tape.open('rb'),'sha256').hexdigest()==P.PIN
    tape=km.Circuit.from_file(str(a.tape))
    q,m,_=map(km.array,P.V.validate_registers(tape,P.SPEC))
    stats=collections.Counter(); rr=[]
    for j,(S,M,_) in enumerate(P.load_archive(a.archive)):
        X=P.V.to_bits(S,12);Y=P.V.to_bits(M,12)
        sim=km.Simulator(batch_size=len(S),seed=102362+j,debug_print=False)
        sim.use_same_registers_as(tape)
        sim.write_across_shots(q,X);sim.write_across_shots(m,Y);sim.do(tape)
        got=sim.read_across_shots(q)
        dd=((got^X).T.reshape(len(S),70,12)@(1<<np.arange(12))).astype(np.int32)
        H=dd^S
        for k in np.flatnonzero(dd.any(1)):
            # With 70 moments, arbitrary sequences can have BM complexity
            # >35; keep them explicitly outside the locator regime.
            try: d=inspect(dd[k])
            except AssertionError:d={'degree':'>35','roots':None,'poles':[],'repeated':None,'zero_root':None}
            rr.append(dict(batch=j,lane=int(k),input_weight=len(P.bm(S[k]))-1,
                returns_zero=bool(not H[k].any()),**d))
            stats[d['degree']]+=1
        print(j,len(rr),dict(stats),flush=True)
    a.out.write_text(json.dumps(dict(sha=P.PIN,nonzero_value_residuals=len(rr),rows=rr),separators=(',',':'))+'\n')

if __name__=='__main__':main()
