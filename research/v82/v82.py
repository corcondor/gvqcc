"""Reproduce PR171 additive FFT with dual source/destination GF(2) frames.
Writes KMB v2; verifies emitted affine gates at every nonzero field point.
Derived from corcondor/gvqcc PR171, research/v81/{field_scan.py,emit_opt.cpp,check_scan.cpp}.
"""
import struct, array, functools, hashlib, json, random, sys, time
from pathlib import Path
from collections import Counter
F=4096; M=4095; N=35; FLAG=49140; HM=49141; Q=851
BETA=[1,70,1971,2939,2,140,3942,1701,4,280,3743,3402]
EXP=[]; LOG=[0]*F;x=1
for i in range(M):
    EXP.append(x);LOG[x]=i;x<<=1
    if x&F:x^=0x1053
assert x==1 and len(set(EXP))==M;EXP*=2
def mul(a,b):return EXP[LOG[a]+LOG[b]] if a and b else 0
def inv(a):return EXP[M-LOG[a]]
def ev(p,x):
    z=0
    for a in reversed(p):z=mul(z,x)^a
    return z
def prod(a,b):
    z=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):z[i+j]^=mul(x,y)
    return z
T=[0,1];S=[];TAB=[]
for b in BETA:
    t=ev(T,b);assert t;s=[mul(v,inv(t)) for v in T];S.append(s)
    col=[ev(s,1<<i) for i in range(12)];r=[0]*F
    for x in range(1,F):
        a=x&-x;r[x]=r[x^a]^col[a.bit_length()-1]
    TAB.append(r);tt=[0]*(2*len(T)-1)
    for i,c in enumerate(T):tt[2*i]=mul(c,c)
    for i,c in enumerate(T):tt[i]^=mul(c,t)
    T=tt
B=[[1]]
for i in range(1,N+1):
    a=i&-i;B.append(prod(B[i^a],S[a.bit_length()-1]));assert len(B[i])==i+1 and B[i][-1]
def trans(rows):return [sum(((v>>j)&1)<<i for i,v in enumerate(rows)) for j in range(12)]
def wt(rows):return sum(v.bit_count() for v in rows)
def mat(v):return trans([mul(1<<i,v) for i in range(12)])
def opt(rows,mode,seed):
    r=rows[:];sp=[];dp=[];best=(wt(r),r[:],[],[]);rng=random.Random(seed);seen={tuple(r)};neutral=0
    for _ in range(40):
        bg=-1;moves=[]
        for side in range(2):
            if mode==0 and side or mode==1 and not side:continue
            a=r if side else trans(r)
            for i in range(12):
                for j in range(12):
                    if i==j:continue
                    g=a[i].bit_count()-(a[i]^a[j]).bit_count()-2
                    if g<0 or (g==0 and (mode!=3 or neutral>=3)):continue
                    if g>bg:bg=g;moves=[]
                    if g==bg:moves.append((side,i,j))
        if mode==3:rng.shuffle(moves)
        found=False
        for side,i,j in moves:
            rr=r[:]
            if side:rr[i]^=rr[j]
            else:rr=[v^((1<<i) if v>>j&1 else 0) for v in rr]
            if tuple(rr) in seen:continue
            seen.add(tuple(rr));r=rr
            (dp if side else sp).append((j,i) if side else (i,j));cost=wt(r)+2*(len(sp)+len(dp))
            if cost<best[0]:best=(cost,r[:],sp[:],dp[:])
            neutral=neutral+1 if bg==0 else 0;found=True;break
        if not found:break
    return best
@functools.lru_cache(None)
def plan(v,dual):
    rows=mat(v);p=opt(rows,0,0)
    if dual:
        for mode,seed in [(1,0),(2,0)]+[(3,v*31+s) for s in range(5)]:
            q=opt(rows,mode,seed)
            if q[0]<p[0]:p=q
    cost,r,sp,dp=p;z=[1<<i for i in range(24)]
    for a,b in sp:z[b]^=z[a]
    for a,b in dp:z[12+b]^=z[12+a]
    for i,x in enumerate(r):
        for j in range(12):
            if x>>j&1:z[12+i]^=z[j]
    for a,b in dp[::-1]:z[12+b]^=z[12+a]
    for a,b in sp[::-1]:z[b]^=z[a]
    assert z==[1<<i for i in range(12)]+[(1<<(12+i))|rows[i] for i in range(12)]
    return p
class Writer:
    def __init__(self,dual):
        self.dual=dual;self.c=[None,bytearray()]+[array.array('I') for _ in range(8)];self.stats=Counter();self.s=[1<<i for i in range(840)];self.seen=set();self.field=Counter();self.original_field=0;self.final_field=0
    def g(self,t,a=-1,b=-1,c=-1,m=0,k=0):
        self.c[1].append(t);self.stats[t]+=1;ar=(t>>4)&3
        if ar==1:self.c[7].append(a)
        if ar==2:self.c[5].append(a);self.c[6].append(b)
        if ar==3:self.c[2].append(a);self.c[3].append(b);self.c[4].append(c)
        if t&64:self.c[8].append(m)
        if t&128:self.c[9].append(k)
        if t==33:self.s[b]^=self.s[a]
        if t==34:self.s[a],self.s[b]=self.s[b],self.s[a]
        if t==17:self.s[a]^=1<<840
    def cx(self,a,b):assert a!=b;self.g(33,a,b)
    def const(self,d,v):
        for b in range(12):
            if v>>b&1:self.g(17,d+b)
    def fieldadd(self,s,d,v):
        if not v:return
        self.field[v]+=1;cost,r,sp,dp=plan(v,self.dual);self.original_field+=plan(v,False)[0];self.final_field+=cost
        for a,b in sp:self.cx(s+a,s+b)
        for a,b in dp:self.cx(d+a,d+b)
        for i,x in enumerate(r):
            for j in range(12):
                if x>>j&1:self.cx(s+j,d+i)
        for a,b in dp[::-1]:self.cx(d+a,d+b)
        for a,b in sp[::-1]:self.cx(s+a,s+b)
    def scale(self,q,v):
        if v==1:return
        r=mat(v);g=[]
        for j in range(12):
            i=next(i for i in range(j,12) if r[i]>>j&1)
            if i!=j:r[i],r[j]=r[j],r[i];g.append((34,q+i,q+j))
            for i in range(12):
                if i!=j and r[i]>>j&1:r[i]^=r[j];g.append((33,q+j,q+i))
        assert r==[1<<i for i in range(12)]
        for t,a,b in g[::-1]:self.g(t,a,b)
    def leaf(self,x):
        if not x:return
        j=LOG[x];assert j not in self.seen;self.seen.add(j)
        # Independent exact affine-row oracle for P(x) XOR 4095 and V(x).
        p=[0]*12;v=[0]*12;y=1
        for a in range(N):
            for b in range(12):
                z=mul(y,1<<b)
                while z:
                    t=z&-z;i=t.bit_length()-1;p[i]|=1<<(a*12+b);v[i]|=1<<(420+a*12+b);z^=t
            y=mul(y,x)
        for b in range(12):
            if (y^4095)>>b&1:p[b]|=1<<840
        assert self.s[:12]==p and self.s[420:432]==v
        self.g(64,m=FLAG)
        for b in range(12):self.g(193,m=FLAG,k=j*12+b)
        self.g(129,k=FLAG);self.g(49,0,1,840)
        for b in range(2,12):self.g(49,838+b,b,839+b)
        for b in range(12):self.g(160,850,420+b,k=j*12+b)
        for b in range(11,1,-1):self.g(80,839+b,m=HM);self.g(160,838+b,b,k=HM)
        self.g(80,840,m=HM);self.g(160,0,1,k=HM);self.g(1);self.g(64,m=FLAG)
    def basischange(self,reverse):
        for i in (range(N+1) if reverse else range(N,-1,-1)):
            a=inv(B[i][i]);p=i*12;v=420+p
            if not reverse and i<N:self.scale(p,a);self.scale(v,a)
            for j in (range(i-1,-1,-1) if reverse else range(i)):
                if B[i][j]:
                    if i==N:self.const(12*j,mul(a,B[i][j]))
                    else:self.fieldadd(p,12*j,B[i][j]);self.fieldadd(v,420+12*j,B[i][j])
            if reverse and i<N:self.scale(p,B[i][i]);self.scale(v,B[i][i])
    def split(self,k,c):
        if not c:return
        h=1<<(k-1)
        for i in range(min(h,N-h+1)):
            j=i+h
            if j==N:self.const(12*i,mul(c,inv(B[N][N])))
            else:self.fieldadd(12*j,12*i,c);self.fieldadd(420+12*j,420+12*i,c)
    def dfs(self,k,a):
        if not k:self.leaf(a);return
        c=TAB[k-1][a];self.split(k,c);self.dfs(k-1,a);self.split(k,1);self.dfs(k-1,a^BETA[k-1]);self.split(k,c^1)
    def build(self):
        self.basischange(False);self.const(0,4095);self.dfs(12,0);self.const(0,4095);self.basischange(True)
        assert len(self.seen)==M and self.s==[1<<i for i in range(840)]
    def save(self,path):
        c=self.c;st=self.stats
        with open(path,'wb') as f:
            f.write(struct.pack('<16s4I9Q',bytes.fromhex('d750c7d5c329d326e3cc9f6834f2b8bf'),2,Q,HM+1,2*N+M,len(c[1]),len(c[2]),len(c[5]),len(c[7]),len(c[8]),len(c[9]),0,0,0))
            for name,start,qu in [(f'P{i}',12*i,1) for i in range(N)]+[(f'V{i}',420+12*i,1) for i in range(N)]+[(f'E{i}',12*i,0) for i in range(M)]:
                b=name.encode();f.write(struct.pack('<QQII',0,8+len(b)+48,len(b),12));f.write(b);f.write(struct.pack('<12I',*((start+i)|(qu<<31) for i in range(12))))
            for k in range(1,10):
                b=bytes(c[k]);f.write(struct.pack('<QQ',k,len(b)));f.write(b)
        return dict(qubits=Q,ops=len(c[1]),CCX=st[49],HMR=st[80],CX=st[33],SWAP=st[34],scalar_types=len(self.field),fieldCX_old=self.original_field,fieldCX_new=self.final_field,affine_points=len(self.seen),restored=True,sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())
def main():
    dual=sys.argv[1]=='dual';w=Writer(dual);w.build();r=w.save(sys.argv[2]);print(json.dumps(r),flush=True);Path(sys.argv[2]+'.json').write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':main()
