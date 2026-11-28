"""Native packed two-RHS modular division for fixed Euclidean degree profiles.
No data-dependent host selection in an emitted circuit. Every profile is a
separate research chart; unsupported pivots/degree drops must not be submitted.
Uses 70 coefficient words + 5 workspace words at m=17.
"""
import json,random,hashlib,sys
from pathlib import Path
from functools import lru_cache
import numpy as np
import kickmix as km
from packed_return import Tape, CODES, mul, inv, bits, EXP, LOG, schedule, check_rank42
from reference_solve import div, rem, egcd, trim, add, mul as pmul, scale, join, ev, trace
DIR=Path(__file__).parent

def powf(a,e):return EXP[(LOG[a]*e)%4095] if a else (1 if e==0 else 0)
def parity(x):return x.bit_count()&1

@lru_cache(None)
def frob_cols(k):return tuple(powf(1<<i,1<<(k%12)) for i in range(12))
@lru_cache(None)
def linops(cols):
    n=len(cols);r=[sum(((v>>i)&1)<<j for j,v in enumerate(cols)) for i in range(n)];ops=[]
    for j in range(n):
        i=next(i for i in range(j,n) if (r[i]>>j)&1)
        if i!=j:r[i],r[j]=r[j],r[i];ops.extend(((i,j),(j,i),(i,j)))
        for i in range(n):
            if i!=j and (r[i]>>j)&1:r[i]^=r[j];ops.append((j,i))
    assert r==[1<<i for i in range(n)]
    return tuple(reversed(ops))
def factors():
    f=[1<<(i%12) for i in range(24)];terms=[]
    for k,c in enumerate(CODES):
        a=c%64;b=(c//64)%64
        if c<4096:
            if a<24:
                assert b//12==a//12
                f[b]^=f[a]
            continue
        z=1<<(c//4096-1-24)
        for d in CODES[k+1:]:
            if d<4096:
                i=d%64;j=(d//64)%64
                if i>=24 and z>>(i-24)&1:z^=1<<(j-24)
        assert a<12<=b<24;terms.append((f[a],f[b],z))
    assert len(terms)==42
    for i in range(12):
        for j in range(12):
            z=0
            for a,b,c in terms:
                if (a>>i)&(b>>j)&1:z^=c
            assert z==mul(1<<i,1<<j)
    return terms
TERMS=factors()

class Packed(Tape):
    def __init__(self,work,blocked=True):
        super().__init__();self.work=work;self.blocked=blocked;self.scales=0;self.reciprocals=0
    def frame(self,w,cols):
        for i,j in linops(tuple(cols)):self.cx(w[i],w[j])
    def frob(self,w,k):self.frame(w,frob_cols(k))
    def xorword(self,a,b):
        for x,y in zip(a,b):self.cx(x,y)
    def swapword(self,a,b):
        for x,y in zip(a,b):
            self.cx(x,y);self.cx(y,x);self.cx(x,y)
    def affine_product(self,w,a,b,z,c):
        if not a or not b:return
        assert not set(w)&set(z)
        if a==b:
            for i in bits(a):
                for j in bits(c):self.cx(w[i],z[j])
            return
        # Choose two independent control forms, including mixed self-products.
        p=next(bits(a))
        bb=b^(a if (b>>p)&1 else 0)
        q=next(bits(bb))
        assert q!=p
        s=len(self.ops)
        for i in bits(a^(1<<p)):self.cx(w[i],w[p])
        for i in bits(bb^(1<<q)):self.cx(w[i],w[q])
        if (b>>p)&1:self.cx(w[p],w[q])
        t=next(bits(c))
        for i in bits(c^(1<<t)):self.cx(z[t],z[i])
        pre=self.ops[s:]
        self.ccx(w[p],w[q],z[t]);self.ops.extend(reversed(pre))
    def selfpower_add(self,a,z,k):
        cols=frob_cols(k)
        for l,m,v in TERMS:
            b=sum(parity(m&c)<<i for i,c in enumerate(cols))
            self.affine_product(a,l,b,z,v)
    def frob_prod(self,a,b,z,k,out=0):
        self.frob(b,k)
        if out:self.frob(z,-out)
        self.madd(a,b,z)
        if out:self.frob(z,out)
        self.frob(b,-k)
    def inverse_add(self,a,z):
        # Itoh–Tsujii 1,2,4,8,10,11 with only three clean work words.
        # Last multiply is directly accumulated in Frobenius-squared output.
        b,c,d=self.work[1:4]
        assert len({q for w in (a,z,b,c,d) for q in w})==60
        start=len(self.ops)
        self.selfpower_add(a,b,1)
        self.selfpower_add(b,c,2)
        self.selfpower_add(c,d,4)
        self.selfpower_add(b,c,2)
        self.frob_prod(d,b,c,8)
        end=len(self.ops)
        self.frob_prod(c,a,z,10,1)
        self.ops.extend(reversed(self.ops[start:end]))
        self.reciprocals+=1
    def word_scale(self,w,d,di):
        # Logical macro: exact only when d*di=1 and work[4] is clean.
        # Expander can use either unitary inverse cleanup or measured dual cleanup.
        assert len({q for a in (w,d,di,self.work[4]) for q in a})==48
        self.ops.append(('S',tuple(w),tuple(d),tuple(di)));self.scales+=1
    def divide_monic(self,row,Y,implicit_top=False):
        # Quotient occupies retired high coefficients, remainder the low ones.
        n=len(row);k=len(Y)
        if implicit_top:
            for i in range(k):self.xorword(Y[i],row[n-k+i])
        for j in range(n-1,k-1,-1):
            for i,y in enumerate(Y):self.madd(row[j],y,row[j-k+i])
    def upper(self,t,row):
        # row[i] += sum_{j>i} t[j-i-1]*row[j], old higher controls preserved.
        if not self.blocked:
            for i in range(len(row)):
                for j in range(i+1,len(row)):self.madd(t[j-i-1],row[j],row[i])
            return
        def rec(lo,hi):
            if hi-lo<=1:return
            mid=lo+schedule(hi-lo)[1];rec(lo,mid)
            self.toeplitz(t,row[mid:hi],row[lo:mid],mid-lo-1,-1,1,True)
            rec(mid,hi)
        rec(0,len(row))
    def rotate_words(self,row,k):
        # Physical output order (q,t) from current (t,q).
        n=len(row);perm=list(range(k,n))+list(range(k))
        order=list(range(n))
        for i,p in enumerate(perm):
            j=order.index(p)
            if i!=j:self.swapword(row[i],row[j]);order[i],order[j]=order[j],order[i]
    def solve(self,X,Y,rhs,profile):
        # X is monic degree len(X); Y degree k, with leading coefficient Y[k].
        # Y may contain known-zero unused high coefficient slots.
        n=len(X);k=profile[0];assert len(Y)>k and all(len(row)==n for row in rhs)
        assert 0<=k<n
        Y=Y[:k+1];lead=Y[-1];lower=Y[:-1];r=self.work[0]
        self.inverse_add(lead,r)
        if not k:
            assert len(profile)==1
            for row in rhs:
                for w in row:self.word_scale(w,r,lead)
            self.inverse_add(lead,r)
            return
        for w in lower:self.word_scale(w,r,lead)
        self.inverse_add(lead,r)
        start=len(self.ops);self.divide_monic(X,lower,True);end=len(self.ops)
        for row in rhs:self.divide_monic(row,lower)
        assert len(profile)>1 and 0<=profile[1]<k
        self.solve(lower,X[:k],[row[:k] for row in rhs],profile[1:])
        # X=q*Y_normalized+R. Reuse the R bank for negative Laurent
        # coefficients. Leading quotient 1 is implicit; X[0] not needed.
        neg=X[1:k][::-1];start2=len(self.ops)
        self.divide(neg,lower[::-1],self.blocked)
        end2=len(self.ops)
        t=X[1:][::-1];d=n-k
        for row in rhs:
            if d and k:self.toeplitz(t,row[:k],row[k:],d-1,-1,1,self.blocked)
            self.upper(t,row[:k]);self.rotate_words(row,k)
        self.ops.extend(reversed(self.ops[start2:end2]))
        self.ops.extend(reversed(self.ops[start:end]))
        # The normalized solution is lead times the desired solution.
        self.inverse_add(lead,r)
        for row in rhs:
            for w in row:self.word_scale(w,r,lead)
        for w in lower:self.word_scale(w,lead,r)
        self.inverse_add(lead,r)

def layout(m):
    w=[tuple(range(12*i,12*i+12)) for i in range(4*m+7)]
    A=w[:m+1];B=w[m+1:2*m+1];C=w[2*m+1:3*m+1];D=w[3*m+1:4*m+1];c=w[4*m+1];work=w[4*m+2:]
    return A,B,C,D,c,work

def construct(m,profile,blocked):
    A,B,C,D,c,work=layout(m);t=Packed(work,blocked)
    # Reduce C and A modulo the monic B while retaining their top words.
    for i in range(m):t.madd(B[i],c,C[i])
    s=len(t.ops)
    for i in range(m):t.madd(B[i],A[-1],A[i])
    e=len(t.ops)
    t.solve(B,A[:-1],[C,D],profile)
    t.ops.extend(reversed(t.ops[s:e]))
    # #326 packed two-RHS return.
    tr=A[::-1][:m];s=len(t.ops);t.divide(tr,B[::-1],blocked);e=len(t.ops)
    t.couple(tr,C,D,c,blocked);t.ops.extend(reversed(t.ops[s:e]))
    return t

def inverse_ops(ops):
    for g in reversed(ops):
        if g[0]=='S':yield ('S',g[1],g[3],g[2])
        else:yield g

def prodphase(cb,qs,a,b,meas,parbit):
    # #302 contraction: a classical measurement covector against product.
    for i,u in enumerate(a):
        for j,v in enumerate(b):
            cb.bit_store(parbit,False)
            for k in bits(mul(1<<i,1<<j)):cb.cx(meas[k],parbit)
            cb.ccz(qs[u],qs[v],parbit)
    cb.bit_store(parbit,False)

def emit(cb,qs,ops,work,measured):
    temp=work[4];buf=Tape()
    def plain(g):
        if g[0]==0:cb.cx(qs[g[1]],qs[g[2]])
        elif g[0]==1:cb.ccx(qs[g[1]],qs[g[2]],qs[g[3]])
        else:raise ValueError(g)
    def prod(a,b,t):
        buf.ops=[];buf.madd(a,b,t)
        for g in buf.ops:plain(g)
    # One reusable set of classical measurement bits; explicitly clear.
    mb=list(cb.alloc_bits(12)) if measured else []
    pb=list(cb.alloc_bits(1)) if measured else []
    for g in ops:
        if g[0]!='S':plain(g);continue
        _,a,d,di=g;prod(a,d,temp)
        for u,v in zip(a,temp):
            cb.cx(qs[u],qs[v]);cb.cx(qs[v],qs[u]);cb.cx(qs[u],qs[v])
        if measured:
            cb.hmr([qs[i] for i in temp],mb)
            prodphase(cb,qs,a,di,mb,pb[0])
            for bit in mb:cb.bit_store(bit,False)
        else:prod(a,di,temp)
    if measured:cb.free(mb);cb.free(pb)
def build(m,profile,blocked,measured,reverse=False):
    t=construct(m,profile,blocked);Q=12*(4*m+7)
    cb=km.CircuitBuilder();cb.set_max_qubits(Q)
    qs=list(cb.create_quantum_register(Q,'W'))
    emit(cb,qs,inverse_ops(t.ops) if reverse else t.ops,layout(m)[-1],measured)
    return cb.finish_circuit(),t
def make_case(rng,m,profile,structured=True):
    # Construct a monic Euclidean chain backwards with prescribed degrees.
    # Ensures all pivots nonzero, including forced multi-degree gaps.
    assert profile[-1]==0
    # Start with constant remainder, choose successive quotient polynomials.
    Y=[rng.randrange(1,4096)];X=[]
    degs=[m]+list(profile)
    for i in range(len(degs)-2,-1,-1):
        gap=degs[i]-degs[i+1]
        q=[rng.randrange(4096) for _ in range(gap)]+[rng.randrange(1,4096)]
        X,Y=Y,add(pmul(q,Y),X)
    # Y is degree m, X is degree profile[0]. Normalize B only.
    B=scale(Y,inv(Y[-1]));A=X+[0]*(m-len(X))
    hi=rng.randrange(4096)
    A=[x^mul(hi,y) for x,y in zip(A,B[:-1])]+[hi]
    C=[rng.randrange(4096) for _ in range(m)];D=[rng.randrange(4096) for _ in range(m)];c=rng.randrange(4096)
    # Independent reference from the full polynomial derivative inverse.
    from reference_solve import derivative
    P=join(A,B);N=join(C+[c],D)
    h,_,u=egcd(P,derivative(P),two=False)
    assert h==[1]
    V=rem(pmul(N,u),P)
    from reference_solve import split
    E,F=split(V)
    E=E+[0]*(m+1-len(E));F=F+[0]*(m-len(F))
    # V order in physical output: F, E_1...E_m, E_0.
    row=A+B[:-1]+C+D+[c]+[0]*5
    out=A+B[:-1]+F+E[1:]+[E[0]]+[0]*5
    return row,out

def check(m,profile,blocked,measured,rows,targets):
    circ,t=build(m,profile,blocked,measured);ic,_=build(m,profile,blocked,measured,True)
    Q=12*(4*m+7);assert circ.num_qubits==Q and ic.num_qubits==Q
    name=f'quot_m{m}_'+','.join(map(str,profile))+f'_b{int(blocked)}_h{int(measured)}'
    path=DIR/(name+'.kmb');circ.to_file(str(path),format='kmb');circ=km.Circuit.from_file(str(path))
    def pack(a):return ((np.array(a,dtype=np.uint16)[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(a),Q).T.astype(bool)
    A,B=pack(rows),pack(targets);qs=km.array([km.q(i) for i in range(Q)])
    for seed in (19,97):
        for i in range(0,len(rows),32):
            n=min(32,len(rows)-i);s=km.Simulator(batch_size=n,seed=seed+i,debug_print=False,counting_operations=True)
            s.use_same_registers_as(circ);s.write_across_shots(qs,A[:,i:i+n]);s.do(circ)
            assert np.array_equal(s.read_across_shots(qs),B[:,i:i+n]),('forward',m,profile,blocked,measured)
            assert not np.any(s.read_phase_flipped_across_shots())
            # Fresh simulator avoids depending on measurement allocator histories.
            u=km.Simulator(batch_size=n,seed=seed+i+1103,debug_print=False,counting_operations=True)
            u.use_same_registers_as(ic);u.write_across_shots(qs,B[:,i:i+n]);u.do(ic)
            assert np.array_equal(u.read_across_shots(qs),A[:,i:i+n]),('inverse',m,profile,blocked,measured)
            assert not np.any(u.read_phase_flipped_across_shots())
    rec=dict(m=m,profile=profile,blocked=blocked,measured=measured,Q=Q,ops=len(circ),paid=int(circ.operation_statistics().num_toffoli_like),scales=t.scales,reciprocals=t.reciprocals,shots=4*len(rows),errors=0,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    print(json.dumps(rec),flush=True);return rec

def main():
    check_rank42()
    rng=random.Random(32820261128);results=[]
    for m,profile in [(3,[2,1,0]),(5,[3,1,0]),(8,[7,6,5,4,3,2,1,0]),(17,list(range(16,-1,-1))),(17,[14,9,5,2,0])]:
        rows,targets=zip(*(make_case(rng,m,profile) for _ in range(32)))
        for blocked,measured in [(False,False),(True,False),(True,True)]:
            results.append(check(m,profile,blocked,measured,rows,targets))
    (DIR/'quotient_receipt.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
