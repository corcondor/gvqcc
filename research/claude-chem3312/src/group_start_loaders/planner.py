# dual cover planner on a frame: A subset Theta-perp (structured), chip pool, matroid-parity matching over GF(2^16).
import numpy as np, random, itertools, time, sys
from frame import *
from gf2 import *
NO=30
class Gf:
    POLY=0x1002D
    def __init__(self):
        Q=65535
        EXP=np.zeros(4*Q+8,dtype=np.int64); LOG=np.zeros(Q+1,dtype=np.int64)
        x=1
        for i in range(Q):
            EXP[i]=x; LOG[x]=i; x<<=1
            if x&0x10000: x^=self.POLY
        EXP[Q:2*Q]=EXP[:Q]
        LOG[0]=2*Q+2
        EXP[2*Q:]=0
        self.EXP=EXP; self.LOG=LOG; self.Q=Q
    def rank(self, M):
        M=M.copy(); EXP,LOG,Q=self.EXP,self.LOG,self.Q
        nr,nc=M.shape; r=0
        for c in range(nc):
            if r>=nr: break
            nz=np.nonzero(M[r:,c])[0]
            if len(nz)==0: continue
            p=r+nz[0]
            if p!=r: M[[r,p]]=M[[p,r]]
            inv=EXP[(Q-LOG[M[r,c]])%Q]
            M[r]=EXP[LOG[M[r]]+LOG[inv]]
            rows=np.nonzero(M[r+1:,c])[0]+r+1
            if len(rows):
                M[rows]^=EXP[LOG[M[rows,c]][:,None]+LOG[M[r]][None,:]]
            r+=1
        return r
gf=Gf()

def parity(x): return x.bit_count()&1

class Space:
    """Theta-perp for a frame: Psi = int over 30*NX bits (bit o*NX+m)."""
    def __init__(self, F):
        self.F=F; self.NX=F.NX; self.NB=NO*F.NX
        cols=[F.col_int(y) for y in F.full]
        piv={}
        for v in cols:
            while v:
                h=v.bit_length()-1
                if h in piv: v^=piv[h]
                else: piv[h]=v; break
        self.theta=len(piv)
        # nullspace
        keys=sorted(piv)
        for h in keys:
            r=piv[h]
            for h2 in keys:
                if h2!=h and (piv[h2]>>h)&1: piv[h2]^=r
        free=[c for c in range(self.NB) if c not in piv]
        self.perp=[]
        for f in free:
            v=1<<f
            for h,r in piv.items():
                if (r>>f)&1: v|=1<<h
            self.perp.append(v)
        self.cols=cols
        # coefficient kernels
        self.Ku={}
    def psi_u(self, psi, u):
        out=0; NX=self.NX; mask=(1<<NX)-1
        for o in range(NO):
            if ((psi>>(o*NX))&mask & u).bit_count()&1: out|=1<<o
        return out
    def K(self, u):
        """basis of {Psi in perp : Psi u = 0} (as ints)"""
        if u not in self.Ku:
            imgs=[self.psi_u(p,u) for p in self.perp]
            m=len(imgs)
            rows=[0]*NO
            for a,im in enumerate(imgs):
                for o in range(NO):
                    if (im>>o)&1: rows[o]|=1<<a
            x,null=solve_linear(rows,[0]*NO,m)
            out=[]
            for c in null:
                v=0; i=0; cc=c
                while cc:
                    if cc&1: v^=self.perp[i]
                    cc>>=1; i+=1
                out.append(v)
            self.Ku[u]=out
        return self.Ku[u]

def random_sub(basis,k,rng):
    out=[]; e=Ech()
    while len(out)<k:
        v=0
        for b in basis:
            if rng.random()<0.5: v^=b
        if e.add(v): out.append(v)
    return out

def all_U(NX):
    subs=[]
    N=1<<NX
    for a in range(1,N):
        for b in range(a+1,N):
            c=a^b
            if c>b: subs.append((a,b))
    return subs

def pool_of(S, A):
    N=1<<S.NX
    img=[None]*N
    for u in range(1,N):
        img[u]=[S.psi_u(p,u) for p in A]
    res=[]
    for U in all_U(S.NX):
        eqs=img[U[0]]+img[U[1]]
        sol=solve_linear(eqs,[0]*len(eqs),NO)
        null=sol[1]
        if null: res.append((U,null))
    return res

def chips_from_pool(pool, cap, rng):
    # sample up to cap chips (s,U) from the pool kernels, fair across U
    chips=[]
    sizes=[(1<<len(n))-1 for _,n in pool]
    total=sum(sizes)
    if total<=cap:
        for U,null in pool:
            for mask in range(1,1<<len(null)):
                s=0
                for i,b in enumerate(null):
                    if mask>>i&1: s^=b
                chips.append((s,U))
        return chips,total
    seen=set()
    while len(chips)<cap:
        U,null=pool[rng.randrange(len(pool))]
        mask=rng.randrange(1,1<<len(null))
        s=0
        for i,b in enumerate(null):
            if mask>>i&1: s^=b
        if (s,U) not in seen:
            seen.add((s,U)); chips.append((s,U))
    return chips,total

def chip_vecs(s,U,NX):
    out=[]
    for u in U:
        v=0; ss=s; o=0
        while ss:
            if ss&1: v|=u<<(o*NX)
            ss>>=1; o+=1
        out.append(v)
    return out

def tobits(v,n):
    return np.unpackbits(np.frombuffer(v.to_bytes((n+7)//8,'little'),np.uint8),bitorder='little')[:n]

class Parity:
    def __init__(self, chips, NX, nrng):
        NB=NO*NX
        self.NB=NB
        A=np.zeros((len(chips),NB),np.uint8); B=np.zeros_like(A)
        for i,(s,U) in enumerate(chips):
            a,b=chip_vecs(s,U,NX)
            A[i]=tobits(a,NB); B[i]=tobits(b,NB)
        self.A=A; self.B=B
        self.x=nrng.integers(1,65536,size=len(chips))
    def matrix(self, idx):
        M=np.zeros((self.NB,self.NB),np.int64)
        for i in idx:
            ai=np.nonzero(self.A[i])[0]; bi=np.nonzero(self.B[i])[0]
            xi=self.x[i]
            M[np.ix_(ai,bi)]^=xi
            M[np.ix_(bi,ai)]^=xi
        return M
    def nu(self, idx):
        return gf.rank(self.matrix(idx))//2

def extract(P, idx, target, rng):
    cur=list(idx)
    M=P.matrix(cur)
    assert gf.rank(M)//2==target
    chunk=max(1,len(cur)//4)
    def contrib(sub):
        return P.matrix(sub)
    while len(cur)>target:
        rng.shuffle(cur); progress=False; pos=0
        while pos<len(cur) and len(cur)>target:
            sub=cur[pos:pos+chunk]
            if len(cur)-len(sub)<target:
                pos+=chunk; continue
            Mt=M^contrib(sub)
            if gf.rank(Mt)//2==target:
                M=Mt; cur=cur[:pos]+cur[pos+chunk:]; progress=True
            else: pos+=chunk
        if not progress:
            if chunk==1: break
            chunk=max(1,chunk//2)
    return cur

def check_independent(chips, idx, NX):
    e=Ech()
    for i in idx:
        for v in chip_vecs(*chips[i],NX):
            if not e.add(v): return False
    return True

def design_A(S, alloc, rng):
    """alloc: list of (u, k). Returns independent basis or None"""
    A=[]; e=Ech()
    for u,k in alloc:
        K=S.K(u)
        sub=random_sub(K,k,rng)
        for v in sub:
            if not e.add(v): return None
            A.append(v)
    return A

def trial(S, alloc, rng, nrng, cap=6000, need=None):
    A=design_A(S,alloc,rng)
    if A is None: return None
    pool=pool_of(S,A)
    chips,total=chips_from_pool(pool,cap,rng)
    P=Parity(chips,S.NX,nrng)
    nu=P.nu(range(len(chips)))
    return dict(A=A,chips=chips,P=P,nu=nu,total=total,npool=len(pool))
