"""Exact full-domain comparison of two distinct low-rotation specifications.

V55 B34 retained-product specification is reproduced exactly. A separate,
fully defined rounded-Horner construction uses the V61 repaired coefficients;
it is not asserted identical to the historical V61 phase hash.
"""
from pathlib import Path
import hashlib,json,math
import numpy as np

P=Path(__file__).resolve().parent
N=3133452

def reference():
    x=np.arange(1,N+1,dtype=np.int64);e=np.zeros(N,np.int64)
    for j in range(1,11):e[x>=1<<(2*j)]=j
    U=x<<(2*(10-e));a=(U>>17)-8;t=U&((1<<17)-1)
    target=np.empty(N,np.uint64);tol=np.empty(N,np.int64)
    for i,xx in enumerate(range(1,N+1)):
        r=math.isqrt((1<<130)//xx);target[i]=((r+1)//2)%(1<<64);tol[i]=r>>25
    return x,e,a,t,target,tol

def finish(v,e,B,target,tol):
    sh=32+e-B;q=np.zeros_like(v)
    for k in np.unique(sh):
        m=sh==k;q[m]=(v[m]+(1<<(int(k)-1)))>>int(k) if k>0 else v[m]<<int(-k)
    phase=q.astype(np.uint64)<<np.uint64(64-B);err=np.abs((phase-target).view(np.int64))
    return dict(B=B,generic_rotation_spec=B-3,bad=int((err>tol).sum()),max_ratio=float(np.max(err/tol)),
        min_slack=int((tol-err).min()),phase_hash=hashlib.sha256(phase.astype('<u8').tobytes()).hexdigest(),
        code_hash=hashlib.sha256(q.astype('<i8').tobytes()).hexdigest()),q

def evaluate_rounded(C,z,k,a,t):
    v=C[a,4]
    for j in range(3,-1,-1):
        kk=int(k[j]);zz=int(z[j]);T=t>>(17-kk);mid=int(kk<17)
        v=C[a,j]+(((v*(2*T+mid)+(1<<(kk+zz)))>>(kk+zz+1))<<zz)
    return v

def main():
    x,e,a,t,target,tol=reference();out={"legal_inputs":N,"full_native31R_oracle":False}
    D=np.load(P/'sources/B34_model1.npz');C=D['C'].copy()
    for j,z in enumerate([1,2,3,4,5]):C[:,j]=((C[:,j]+(1<<(z-1)))>>z)<<z
    v=C[a,4]
    for j in range(3,-1,-1):
        mag=np.abs(v);prod=np.zeros(N,np.int64)
        for i in range(int(mag.max()).bit_length()):
            for k in range(max(0,17-i),17):prod+=(((mag>>i)&1)*((t>>k)&1))<<(i+k-17)
        v=C[a,j]+np.sign(v)*prod
    r,q=finish(v,e,34,target,tol);assert r['bad']==0 and r['min_slack']==54096592
    out['V55_B34_retained_products_exact']=r
    full=np.zeros(1<<22,np.int64);full[1:N+1]=q;full[0]=q[0];full[N+1:]=q[-1]
    out['truth_table_interval_screen']={"extension":"repeat endpoint code outside legal domain",
        "bit_transitions":[int(np.count_nonzero(((full[1:]>>j)&1)!=((full[:-1]>>j)&1)))for j in range(34)],
        "scope":"Boolean representation complexity screen; not a native circuit cost or lower bound"}
    D=np.load(P/'v61_sources/pr141/repaired_k12.npz');C=D['C'].copy();v=evaluate_rounded(C,D['z'],D['k'],a,t)
    out['V61_coefficient_new_ordinary_model']={"donor_phase_hash":str(D['phase_sha']),
        "definition":"midpoint only for truncated input k<17; exact ordinary product then stage rounding to z; coefficients unchanged",
        "historical_V61_phase_identity_claimed":False,"results":[finish(v,e,B,target,tol)[0]for B in [34,35]]}
    offsets=[];after=v.copy()
    for addr in range(24):
        sel=a==addr;vv=v[sel];ee=e[sel];tt=target[sel];to=tol[sel];best=None
        for delta in range(-256,257,4):
            rr,_=finish(vv+delta,ee,34,tt,to)
            score=(rr['bad'],rr['max_ratio'],abs(delta))
            if best is None or score<best[0]:best=(score,delta,rr)
        offsets.append(best[1]);after[sel]+=best[1];C[addr,0]+=best[1]
    r,q=finish(after,e,34,target,tol)
    out['new_ordinary_B34_C0_refit']={"offsets":offsets,"grid":"24 independent C0 offsets from -256 to256 step4; 3096 exact segment trials",**r}
    np.savez(P/'ordinary_B34_refit_coefficients.npz',C=C,z=D['z'],k=D['k'],F=32,B=34,b=3)
    (P/'rotation_spec_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)

if __name__=='__main__':main()
