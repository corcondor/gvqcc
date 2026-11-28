"""Packed return for odd-degree locator P=A^2+X B^2, deg B=m, monic.
Input quantum words A[0:m+1], B[0:m], G[0:m], H[0:m], c.
G,H are the already-solved quotient residues, c is the high even RHS quotient.
Output A,B preserved; G'=F, H'=E[1:], c'=E[0].
All words arbitrary, not just consistent decoder states. No new scratch or HMR.
"""
from functools import lru_cache
from pathlib import Path
import json, hashlib, random
import numpy as np
import kickmix as km
from rank42 import CODES
DIR=Path(__file__).parent
Q=4096
EXP=[0]*8190
LOG=[-1]*4096
v=1
for i in range(4095):
    assert LOG[v]==-1
    LOG[v]=i;EXP[i]=EXP[i+4095]=v
    v<<=1
    if v&4096:v^=0x1053
assert v==1
def mul(a,b):return EXP[LOG[a]+LOG[b]] if a and b else 0
def inv(a):
    assert a
    return EXP[4095-LOG[a]]
def xor(xs):
    r=0
    for x in xs:r^=x
    return r
def pmul(a,b):
    c=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):c[i+j]^=mul(x,y)
    return c
def quo(a,b):
    a=list(a);z=[0]*max(0,len(a)-len(b)+1)
    assert b[-1]==1
    for k in reversed(range(len(z))):
        z[k]=a[k+len(b)-1]
        for j,v in enumerate(b):a[k+j]^=mul(z[k],v)
    return z
def bits(x):
    while x:
        l=x&-x;yield l.bit_length()-1;x^=l
# Exact ANF verification of the pinned multiplication, not only sampled words.
def check_rank42():
    f=[{1<<i} for i in range(36)]
    for c in CODES:
        a=c%64;b=(c//64)%64
        if c<4096:f[b]^=f[a]
        else:
            z=set()
            for x in f[a]:
                for y in f[b]:
                    k=x|y
                    if k in z:z.remove(k)
                    else:z.add(k)
            f[c//4096-1]^=z
    assert f[:24]==[{1<<i} for i in range(24)]
    for k in range(12):
        want={1<<(24+k)}|{(1<<i)|(1<<(12+j)) for i in range(12) for j in range(12) if (mul(1<<i,1<<j)>>k)&1}
        assert f[24+k]==want
    assert sum(c>=4096 for c in CODES)==42

@lru_cache(None)
def scale_ops(k):
    assert k
    rows=[sum(((mul(k,1<<j)>>i)&1)<<j for j in range(12)) for i in range(12)]
    ops=[]
    for j in range(12):
        i=next(i for i in range(j,12) if (rows[i]>>j)&1)
        if i!=j:
            rows[i],rows[j]=rows[j],rows[i]
            ops.extend([(i,j),(j,i),(i,j)])
        for i in range(12):
            if i!=j and (rows[i]>>j)&1:
                rows[i]^=rows[j];ops.append((j,i))
    assert rows==[1<<i for i in range(12)]
    return tuple(reversed(ops))

@lru_cache(None)
def interpolation(n):
    # r distinct GF4096 points. Each row is a Lagrange polynomial.
    pts=list(range(n))
    powers=[];rows=[]
    for p in pts:
        z=[1]
        for j in range(1,n):z.append(mul(z[-1],p))
        powers.append(z)
        a=[1];den=1
        for x in pts:
            if x!=p:a=pmul(a,[x,1]);den=mul(den,x^p)
        rows.append([mul(x,inv(den)) for x in a])
    for i in range(n):
        for j in range(n):
            assert xor(mul(powers[k][i],rows[k][j]) for k in range(n))==int(i==j)
    return powers,rows

@lru_cache(None)
def schedule(n):
    if n<=1:return 0,0
    return min((schedule(l)[0]+schedule(n-l)[0]+min(l*(n-l),n-1),l) for l in range(1,n))

class Tape:
    def __init__(self):
        self.ops=[];self.products=0
    def cx(self,a,b):self.ops.append((0,a,b))
    def ccx(self,a,b,t):self.ops.append((1,a,b,t))
    def scale(self,a,k):
        for i,j in scale_ops(k):self.cx(a[i],a[j])
    def linear(self,a,b,k):
        if not k:return
        assert not set(a)&set(b)
        for i in range(12):
            for j in bits(mul(1<<i,k)):self.cx(a[i],b[j])
    def madd(self,a,b,t):
        w=list(a)+list(b)+list(t)
        assert len(set(w))==36
        self.products+=1
        for c in CODES:
            i=c%64;j=(c//64)%64
            if c<4096:self.cx(w[i],w[j])
            else:self.ccx(w[i],w[j],w[c//4096-1])
    def source(self,words,coeff):
        p=next(i for i,c in enumerate(coeff) if c)
        start=len(self.ops)
        self.scale(words[p],coeff[p])
        for i,c in enumerate(coeff):
            if i!=p:self.linear(words[i],words[p],c)
        return words[p],self.ops[start:]
    def rankterm(self,a,ac,b,bc,t,tc):
        if not any(ac) or not any(bc) or not any(tc):return
        assert len({q for w in a+b+t for q in w})==12*(len(a)+len(b)+len(t))
        x,fx=self.source(a,ac);y,fy=self.source(b,bc)
        k=next(i for i,c in enumerate(tc) if c)
        wp=t[k];s=len(self.ops)
        self.scale(wp,inv(tc[k]))
        for j,c in enumerate(tc):
            if j!=k:self.linear(wp,t[j],c)
        ft=self.ops[s:]
        self.madd(x,y,wp)
        self.ops.extend(reversed(ft));self.ops.extend(reversed(fy));self.ops.extend(reversed(fx))
    def toeplitz(self,t,x,y,k,si,sj,blocked):
        l,h=len(y),len(x);r=l+h-1
        ids=[[k+si*i+sj*j for j in range(h)] for i in range(l)]
        assert min(map(min,ids))>=0 and max(map(max,ids))<len(t)
        if not blocked or l*h<=r:
            for i,u in enumerate(y):
                for j,v in enumerate(x):self.madd(t[ids[i][j]],v,u)
            return
        lo=min(map(min,ids))
        a=t[lo:lo+r]
        powers,rows=interpolation(r)
        for pw,co in zip(powers,rows):
            self.rankterm(a,co,x,[pw[j if sj==1 else h-1-j] for j in range(h)],y,[pw[i if si==1 else l-1-i] for i in range(l)])
    def divide(self,a,b,blocked):
        # a = reversed top m A coefficients, b = reversed lower B coefficients.
        def rec(lo,hi):
            if hi-lo<=1:return
            mid=lo+schedule(hi-lo)[1]
            rec(lo,mid)
            self.toeplitz(b,a[lo:mid],a[mid:hi],mid-lo-1,1,-1,True)
            rec(mid,hi)
        if blocked:rec(0,len(a))
        else:
            for i in range(len(a)):
                for j in range(i):self.madd(b[i-j-1],a[j],a[i])
    def couple(self,t,g,h,c,blocked):
        m=len(g)
        for j in range(m):self.madd(t[j],g[j],c)
        if not blocked:
            for i in range(m):
                for j in range(i,m):self.madd(t[j-i],h[j],g[i])
                for j in range(i+1,m):self.madd(t[j-i-1],g[j],h[i])
            return
        def rec(lo,hi):
            if hi-lo==1:
                self.madd(t[0],h[lo],g[lo]);return
            mid=lo+schedule(hi-lo)[1];rec(lo,mid)
            self.toeplitz(t,h[mid:hi],g[lo:mid],mid-lo,-1,1,True)
            self.toeplitz(t,g[mid:hi],h[lo:mid],mid-lo-1,-1,1,True)
            rec(mid,hi)
        rec(0,m)
def generate(m,blocked):
    tape=Tape();Q=12*(4*m+2)
    w=[tuple(range(12*i,12*i+12)) for i in range(4*m+2)]
    a=w[:m+1];b=w[m+1:2*m+1];g=w[2*m+1:3*m+1];h=w[3*m+1:4*m+1];c=w[-1]
    t=a[::-1][:m]
    tape.divide(t,b[::-1],blocked)
    end=len(tape.ops);count=tape.products
    tape.couple(t,g,h,c,blocked)
    tape.ops.extend(reversed(tape.ops[:end]))
    tape.products+=count
    assert sum(o[0]==1 for o in tape.ops)==42*tape.products
    assert tape.products==(4*schedule(m)[0]+2*m if blocked else 2*m*m)
    cb=km.CircuitBuilder();cb.set_max_qubits(Q)
    qs=list(cb.create_quantum_register(Q,'W'))
    for op,*a in tape.ops:
        if op==0:cb.cx(qs[a[0]],qs[a[1]])
        else:cb.ccx(qs[a[0]],qs[a[1]],qs[a[2]])
    circ=cb.finish_circuit()
    return tape,circ
def reference(m,row):
    a=row[:m+1];b=row[m+1:2*m+1]+[1]
    g=row[2*m+1:3*m+1];h=row[3*m+1:4*m+1];c=row[-1]
    qg=quo(pmul(a,g),b);qh=quo(pmul(a,h),b)
    assert len(qg)==len(qh)==m
    E=qg+[0];E[0]^=c
    for j in range(m):E[j+1]^=h[j]
    F=[x^y for x,y in zip(g,qh)]
    return row[:2*m+1]+F+E[1:]+[E[0]]
def verify(m,blocked,rows):
    tape,circ=generate(m,blocked);Q=12*(4*m+2)
    path=DIR/f'return_m{m}_{"blocked" if blocked else "plain"}.kmb'
    circ.to_file(str(path),format='kmb');circ=km.Circuit.from_file(str(path))
    assert circ.num_qubits==Q and int(circ.operation_statistics().num_toffoli_like)==42*tape.products
    rev=km.CircuitBuilder();rev.set_max_qubits(Q);qs=list(rev.create_quantum_register(Q,'W'))
    for op,*a in reversed(tape.ops):
        if op==0:rev.cx(qs[a[0]],qs[a[1]])
        else:rev.ccx(qs[a[0]],qs[a[1]],qs[a[2]])
    ic=rev.finish_circuit()
    def packed(r):
        return ((np.array(r,dtype=np.uint16)[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(r),Q).T.astype(bool)
    A=packed(rows);B=packed([reference(m,r) for r in rows]);q=km.array([km.q(i) for i in range(Q)])
    for seed in (19,97):
        for i in range(0,len(rows),64):
            n=min(64,len(rows)-i)
            s=km.Simulator(batch_size=n,seed=seed+i,debug_print=False,counting_operations=True)
            s.use_same_registers_as(circ);s.write_across_shots(q,A[:,i:i+n]);s.do(circ)
            assert np.array_equal(s.read_across_shots(q),B[:,i:i+n])
            assert not np.any(s.read_phase_flipped_across_shots())
            s.do(ic);assert np.array_equal(s.read_across_shots(q),A[:,i:i+n])
            assert not np.any(s.read_phase_flipped_across_shots())
    rec=dict(m=m,blocked=blocked,Q=Q,field_products=tape.products,CCX=42*tape.products,ops=len(circ),shots=4*len(rows),errors=0,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    print(json.dumps(rec),flush=True);return rec
if __name__=='__main__':
    check_rank42()
    rng=random.Random(32420261128);out=[]
    for m in (4,8,17):
        n=4*m+2;rows=[[rng.randrange(4096) for _ in range(n)] for _ in range(96)]
        rows += [[0]*n,[4095]*n]
        for _ in range(30):
            r=[rng.randrange(4096) for _ in range(n)]
            for j in range(n):
                if rng.randrange(3)==0:r[j]=0
            rows.append(r)
        for v in (False,True):out.append(verify(m,v,rows))
    (DIR/'native_receipt.json').write_text(json.dumps(out,indent=2)+'\n')
