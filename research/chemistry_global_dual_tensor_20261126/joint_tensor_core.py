"""Dual-subspace tensor factorization. From the all-75-bank compiler.
Standalone version: conventional rank factorization is included below.
"""
import numpy as np
import numba

def rank_terms(rows):
    piv={}; B=[]; F=[]
    for i,z in enumerate(rows):
        v=z;c=0
        while v:
            k=v.bit_length()-1
            if k in piv:
                a,b=piv[k];v^=a;c^=b
            else:
                j=len(B);B.append(z);F.append(0);piv[k]=(v,c^(1<<j));c=1<<j;break
        while c:
            j=(c&-c).bit_length()-1;F[j]|=1<<i;c^=1<<j
    return list(zip(F,B))

@numba.njit(cache=True)
def add(piv,v):
    for i in range(23,-1,-1):
        if v>>i&1:
            if piv[i]:v^=piv[i]
            else:piv[i]=v;return 1
    return 0
@numba.njit(cache=True)
def reduced(piv,v):
    for i in range(23,-1,-1):
        if v>>i&1 and piv[i]:v^=piv[i]
    return v
@numba.njit(cache=True)
def parity(v):
    v^=v>>16;v^=v>>8;v^=v>>4;v^=v>>2;v^=v>>1;return v&1
@numba.njit(cache=True)
def nullspace(rows):
    piv=np.zeros(24,np.int64)
    for r in rows:add(piv,r)
    out=np.zeros(24,np.int64);n=0
    for j in range(24):
        if piv[j]:continue
        v=1<<j
        for i in range(j+1,24):
            if piv[i] and parity(piv[i]&v):v^=1<<i
        out[n]=v;n+=1
    return out[:n]
@numba.njit(cache=True)
def feature(b,c):
    v=0
    for i in range(4):
        if b>>i&1:v|=c<<(6*i)
    return v
@numba.njit(cache=True)
def iscovered(piv,rows):
    for v in rows:
        if reduced(piv,v):return False
    return True
@numba.njit(cache=True)
def search(rows,trials,seed,bestcost):
    np.random.seed(seed);ns=nullspace(rows);best=np.zeros((24,2),np.int64);bestn=0;bestcost0=bestcost
    allf=np.zeros((64,16),np.int64)
    for c in range(1,64):
        for b in range(1,16):allf[c,b]=feature(b,c)
    for it in range(trials):
        codim=2+it%4
        if len(ns)<codim:continue
        d=np.zeros(codim,np.int64);p=np.zeros(24,np.int64);q=0
        while q<codim:
            k=np.random.randint(1,1<<len(ns));v=0
            for j in range(len(ns)):
                if k>>j&1:v^=ns[j]
            if add(p,v):d[q]=v;q+=1
        B=np.zeros((64,4),np.int64);bc=np.zeros(64,np.int64)
        for c in range(1,64):
            pp=np.zeros(4,np.int64)
            for b in range(1,16):
                v=allf[c,b];ok=True
                for u in d:
                    if parity(u&v):ok=False;break
                if not ok:continue
                w=b
                for i in range(3,-1,-1):
                    if w>>i&1:
                        if pp[i]:w^=pp[i]
                        else:pp[i]=w;B[c,bc[c]]=b;bc[c]+=1;break
        order=np.random.permutation(63)+1;piv=np.zeros(24,np.int64);res=np.zeros((24,2),np.int64);nr=0;cost=0
        for pair_pass in range(2):
            if cost>=bestcost or iscovered(piv,rows):break
            for c in order:
                cand=np.zeros(4,np.int64);count=0;pp=piv.copy()
                for j in range(bc[c]):
                    b=B[c,j]
                    if add(pp,allf[c,b]):cand[count]=b;count+=1
                take=count if pair_pass else count//2*2
                if not take:continue
                for j in range(take):
                    b=cand[j];assert add(piv,allf[c,b]);res[nr,0]=b;res[nr,1]=c;nr+=1
                cost+=(take+1)//2
                if cost>=bestcost or iscovered(piv,rows):break
        if cost<bestcost and iscovered(piv,rows):
            bestcost=cost;bestn=nr;best[:nr]=res[:nr]
            if bestcost<=8:break
    return best[:bestn],bestcost0,bestcost

def terms(A,trials=64,seed=0):
    rows=np.array([sum(int(v)<<(6*h)for h,v in enumerate(a))for a in A],np.int64)
    per=[]
    for o in range(6):
        r=[sum(((int(v)>>o)&1)<<h for h,v in enumerate(a))for a in A];rt=rank_terms(r)
        if rt:per.append((rt,1<<o))
    base=sum((len(x)+1)//2 for x,c in per)
    F,_,cost=search(rows,trials,seed,base)
    if not len(F):return per,base,base
    piv={}
    for i,(b,c) in enumerate(F):
        v=int(feature(int(b),int(c)));u=1<<i
        while v:
            p=v.bit_length()-1
            if p in piv:a,d=piv[p];v^=a;u^=d
            else:piv[p]=(v,u);break
        assert v
    aa=[0]*len(F)
    for i,r in enumerate(rows):
        v=int(r);u=0
        while v:
            p=v.bit_length()-1;a,d=piv[p];v^=a;u^=d
        for j in range(len(F)):
            if u>>j&1:aa[j]|=1<<i
    out={}
    for a,(b,c) in zip(aa,F):
        if a:out.setdefault(int(c),[]).append((a,int(b)))
    result=[(v,c)for c,v in out.items()]
    check=np.zeros_like(rows)
    for v,c in result:
        for a,b in v:
            f=feature(b,c)
            for i in range(len(rows)):
                if a>>i&1:check[i]^=f
    assert np.array_equal(check,rows)
    return result,base,sum((len(v)+1)//2 for v,c in result)

if __name__=="__main__":
    rng=np.random.default_rng(149)
    for seed in range(32):
        A=rng.integers(0,64,size=(16,4)).tolist()
        result,base,cost=terms(A,128,seed)
        check=[[0]*4 for _ in range(16)]
        for factors,c in result:
            for a,b in factors:
                for i in range(16):
                    for j in range(4):
                        if (a>>i&1) and (b>>j&1):check[i][j]^=c
        assert check==A and cost<=base
    print("32 exact mixed tensor reconstruction tests passed")
