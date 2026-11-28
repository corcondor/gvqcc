"""Source-level 72-anchor reconstruction and algebra audit. No KMB needed.
Does NOT identify the historical 316084.668 circuit or claim a full splice.
The fixed eight extra anchors are not selected from verification inputs.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

N=4024; Q=4096; MOD=0x1053
E=[1]
for _ in range(4094):
    x=E[-1]<<1; E.append(x^MOD if x&Q else x)
assert len(set(E))==4095
E=np.array(E*2,dtype=np.int32); L=np.zeros(Q,dtype=np.int32); L[E[:4095]]=np.arange(4095)
def mul(a,b):
    return np.where((a==0)|(b==0),0,E[L[a]+L[b]])
def m(a,b):
    return int(E[L[a]+L[b]]) if a and b else 0
def inv(a):
    assert np.all(a!=0); return E[4095-L[a]]
def mat(c): return mul(np.asarray(c)[...,None],1<<np.arange(12))
def tr(x):
    t=0
    for _ in range(12): t^=x; x=m(x,x)
    assert t in (0,1); return t
F2D=np.array([sum(tr(m(a,1<<j))<<j for j in range(12)) for a in range(Q)],dtype=np.int32)
assert len(set(F2D))==Q
D2F=np.argsort(F2D)
def pmul(a,b):
    c=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b): c[i+j]^=m(x,y)
    return c
def ev(a,x):
    z=0
    for v in reversed(a): z=m(z,x)^v
    return z
def read_maps(path=None,source=None):
    if source:
        sys.path.insert(0,str(source)); import selector
        return [(int(i),int(j),[int(x) for x in a]) for i,j,a in selector.matrix_rows()]
    return [(int(i),int(j),[int(x,16) for x in a]) for i,j,*a in (line.split() for line in Path(path).read_text().splitlines() if line and not line.startswith('#'))]
def derive(path=None,source=None):
    rows=read_maps(path,source); assert len(rows)==N*72
    i=np.array([v[0] for v in rows]); j=np.array([v[1] for v in rows]); A=np.array([v[2] for v in rows],dtype=np.int32)
    assert np.array_equal(i,np.repeat(np.arange(N),72))
    assert np.array_equal(A,mat(A[:,0]))
    J=j.reshape(N,72); C=A[:,0].reshape(N,72)
    common=set.intersection(*(set(row) for row in J)); assert len(common)==71 and {0,1330}<=common
    assert np.all(C[J==1330]==1)
    c=C[J==0]; assert c.shape==(N,) and len(set(c))==N and not np.any(c==0)
    coeff=np.r_[c,0]; polys=[]
    for a in (1330,0):
        p=[0,1]
        for j in sorted(common-{a}): p=pmul(p,[int(E[j]),1])
        scale=int(inv(ev(p,int(E[a])))); p=[m(x,scale) for x in p]
        assert len(p)==72 and all(ev(p,int(E[j]))==int(j==a) for j in common)
        polys.append(p)
    for d in range(1,72):
        assert not np.any(np.bitwise_xor.reduce(mul(C,E[(J*d)%4095]),axis=1)),d
    p,q=polys; k=m(q[-1],int(inv(p[-1]))); assert (p[-1],q[-1],k)==(1447,3282,2131)
    T=mat(np.arange(Q))
    for bit in range(12):
        y=F2D[1<<bit]; z=np.bitwise_and(T,y)
        pbits=np.zeros_like(z)
        for kbit in range(12): pbits^=(z>>kbit)&1
        got=np.sum(pbits*(1<<np.arange(12)),axis=1)
        assert np.array_equal(got,F2D[mul(np.arange(Q),1<<bit)])
    return coeff,J,C,polys

OLD=[0,503,1006,1509,2012,2515,3018,3521]
A64=OLD+[a for a in [round(N*j/64) for j in range(64)] if a not in OLD]
EXTRA=[round(N*(2*j+1)/128) for j in range(0,64,8)]
A72=A64+EXTRA
assert len(A64)==64 and len(set(A72))==72

def plan(c,out):
    checks=0
    with open(out,'w') as f:
        print(len(A72)-len(OLD),file=f)
        for a in A72[8:]:
            print(a,*mat(c[a]),file=f)
            ids=np.delete(np.arange(N+1),a); ids=ids[(np.arange(1024)*N)//1024]
            rows=mat(inv(c[ids]^c[a])); assert len(set(ids))==1024 and a not in ids
            assert np.all(mul(inv(c[ids]^c[a]),c[ids]^c[a])==1)
            np.savetxt(f,np.column_stack((ids,rows)),fmt='%d'); checks+=len(ids)
        print(*c,file=f)
    return checks

def select(r,c):
    # Reference scores for nonzero slopes ONLY. Existing zero-slope branch is not modeled.
    n=len(r); best=np.zeros(n,dtype=np.int32); lam=best.copy(); mu=best.copy(); base=None; s64=None
    offsets=np.arange(n)[:,None]*Q
    for k,a in enumerate(A72):
        ids=np.delete(np.arange(N+1),a)
        sl=mul(r[:,ids]^r[:,a,None],inv(c[ids]^c[a])[None,:]); full=np.bincount((sl+offsets).ravel(),minlength=n*Q).reshape(n,Q);full[:,0]=0
        if k<8:
            v=np.argmax(full,axis=1); sc=full[np.arange(n),v]
        else:
            sub=sl[:,(np.arange(1024)*N)//1024]; h=np.bincount((sub+offsets).ravel(),minlength=n*Q).reshape(n,Q); h[:,0]=0
            key=np.minimum(h,15)*Q-np.arange(Q)[None,:]; key[:,0]=-Q
            top=np.argpartition(key,-4,axis=1)[:,-4:]; top=np.take_along_axis(top,np.argsort(-np.take_along_axis(key,top,axis=1),axis=1),axis=1)
            cand=np.take_along_axis(full,top,axis=1); cand=np.where(np.take_along_axis(h,top,axis=1)>0,cand,0)
            ix=np.argmax(cand,axis=1); v=top[np.arange(n),ix]; sc=cand[np.arange(n),ix]
        accepted=sc>best
        best=np.where(accepted,sc,best);mu=np.where(accepted,v,mu);lam=np.where(accepted,r[:,a]^mul(c[a],v),lam)
        assert np.all(mu!=0)
        assert np.array_equal(best,np.count_nonzero((r^lam[:,None]^mul(c[None,:],mu[:,None]))==0,axis=1)-1)
        if k==7: base=best.copy()
        if k==63: s64=best.copy()
    assert np.all(best>=s64) and np.all(s64>=base)
    return {'cases':n,'8_mean_support':float(base.mean()),'64_mean_support':float(s64.mean()),'72_mean_support':float(best.mean()),'72_vs_64_improved':int(np.count_nonzero(best>s64)),'72_vs_64_total_support_gain':int((best-s64).sum()),'72_vs_64_worsened':int(np.count_nonzero(best<s64))},lam,mu

def phase_audit(polys):
    rng=np.random.default_rng(33772); p,q=polys; cases=0
    for w in range(36):
        for _ in range(16):
            xs=rng.choice(np.arange(1,Q),w,replace=False); es=rng.integers(1,Q,w)
            l,d=map(int,rng.integers(0,Q,2)); a=[m(l,u)^m(d,v) for u,v in zip(p,q)]
            s=np.zeros(71,dtype=np.int32); power=xs.copy()
            for k in range(71): s[k]=np.bitwise_xor.reduce(mul(es,power),initial=0); power=mul(power,xs)
            direct=0
            for x,e in zip(xs,es): direct^=m(int(e),ev(a,int(x)))
            pair=int(np.bitwise_xor.reduce(mul(np.array(a[1:]),s),initial=0)); assert direct==pair and tr(direct)==tr(pair)
            cases+=1
    return cases

def main():
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--maps',type=Path);g.add_argument('--selector-dir',type=Path);ap.add_argument('--out',type=Path,default=Path('source72_out')); args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    c,J,C,polys=derive(args.maps,args.selector_dir); checks=plan(c,args.out/'plan72.txt')
    rng=np.random.default_rng(20261129072); r=rng.integers(0,Q,(128,N+1),dtype=np.int32);r[:,-1]=0
    scores,_,_=select(r,c)
    receipt={'scope':'source-level reference; not historical Gray72 exact, physical splice, or paid measurement','matrix_basis_checks':N*72*12,'annihilation_checks':N*71,'trace_dual_checks':Q*12,'anchor_matrix_checks':checks,'anchors':len(A72),'extra_anchors':EXTRA,'plan_sha256':hashlib.sha256((args.out/'plan72.txt').read_bytes()).hexdigest(),'phase_pairings':phase_audit(polys),'synthetic_nonzero_slope_support':scores}
    (args.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n'); print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
