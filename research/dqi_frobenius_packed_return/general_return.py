"""General sparse truncated rational return. Independent KickMix backend.
All normalized fixed even degree pairs and odd degree representatives.
No coherent degree selection or complete DQI splice."""
import json, random, hashlib
from functools import lru_cache
from pathlib import Path
import numpy as np
import kickmix as km
import packed_return as P
DIR=Path(__file__).parent
ONE=-1

def rectangles(y,x,coeff,step):
    for p in range(step):
        yy=tuple(i for i in y if i%step==p)
        if not yy:continue
        for q in range(step):
            xx=tuple(j for j in x if j%step==q)
            if xx and any(i-j in coeff for i in yy for j in xx):yield yy,xx
@lru_cache(None)
def plan(y,x,active,step):
    pairs=tuple((i,j,i-j) for i in y for j in x if i-j in active)
    if not pairs:return 0,False,()
    lo=y[0]-x[-1];r=len(y)+len(x)-1
    inds=tuple((k,lo+step*k) for k in range(r) if lo+step*k in active)
    if len(pairs)<r:return len(pairs),False,pairs
    _,lc=P.interpolation(r)
    nz=tuple(k for k in range(r) if any(lc[k][i] for i,d in inds))
    return (len(nz),True,(inds,nz)) if len(nz)<len(pairs) else (len(pairs),False,pairs)
def cost(y,x,d,step):return sum(plan(a,b,d,step)[0] for a,b in rectangles(y,x,d,step))
@lru_cache(None)
def split(n,d,step):
    if n<=1:return 0,0
    return min((split(k,d,step)[0]+split(n-k,d,step)[0]+cost(range(k,n),range(k),d,step),k) for k in range(1,n))
class T(P.Tape):
    def cross(self,w,c,y,x,step):
        for yy,xx in rectangles(y,x,c,step):
            for i in yy:
                for j in xx:
                    if c.get(i-j)==ONE:self.linear(w[j],w[i],1)
            d=tuple(sorted(k for k,v in c.items() if v!=ONE))
            n,interp,z=plan(yy,xx,d,step);old=self.products
            if interp:
                inds,nz=z;pw,lc=P.interpolation(len(yy)+len(xx)-1)
                for k in nz:self.rankterm([c[d] for i,d in inds],[lc[k][i] for i,d in inds],[w[j] for j in xx],list(reversed(pw[k][:len(xx)])),[w[i] for i in yy],pw[k][:len(yy)])
            else:
                for i,j,d in z:self.madd(c[d],w[j],w[i])
            assert self.products-old==n
    def tri(self,w,c,lo,hi,solve,step):
        d=tuple(sorted(k for k,v in c.items() if v!=ONE));old=self.products
        def rec(l,h):
            if h-l<=1:return
            mid=l+split(h-l,d,step)[1]
            rec(l,mid) if solve else rec(mid,h)
            self.cross(w,c,range(mid,h),range(l,mid),step)
            rec(mid,h) if solve else rec(l,mid)
        rec(lo,hi);assert self.products-old==split(hi-lo,d,step)[0]
    def rational(self,w,N,D,h):
        n=len(w)
        if not h:return
        self.tri(w,D,h,n,False,2)
        self.cross(w,N,range(h,n),range(h),2)
        self.tri(w,D,0,h,True,2)
        self.tri(w,N,0,h,False,2)
        self.cross(w,D,range(h,n),range(h),2)
        self.tri(w,D,h,n,True,2)

def even(a,b,direct):
    w=[tuple(range(12*i,12*i+12)) for i in range(3*a+b)]
    A,B,W=w[:a],w[a:a+b],w[a+b:];w=W[::-1];r=a-b;t=T()
    if not b:return t,12*(3*a+b)
    D={2*(i+1):v for i,v in enumerate(B[::-1])}
    if direct:
        N={2*(i+1):v for i,v in enumerate(A[::-1])}
        N[2*r-1]=ONE;N.update({2*r-1+d:v for d,v in D.items()})
        t.rational(w,N,D,2*b)
    else:
        z=A[::-1][:a-1];bv=B[::-1]
        for i in range(min(b,len(z))):t.linear(bv[i],z[i],1)
        t.tri(z,{i+1:v for i,v in enumerate(bv)},0,len(z),True,1)
        end=len(t.ops);n=t.products
        C={2*(i+1):v for i,v in enumerate(z)};C[2*r-1]=ONE
        t.cross(w,C,range(2*b,len(w)),range(2*b),2)
        t.tri(w,C,0,2*b,False,2)
        t.ops.extend(reversed(t.ops[:end]));t.products+=n
    return t,12*(3*a+b)
def odd(m):
    w=[tuple(range(12*i,12*i+12)) for i in range(4*m+2)]
    a=w[:m+1];b=w[m+1:2*m+1];g=w[2*m+1:3*m+1];j=w[3*m+1:4*m+1];c=w[-1]
    w=([c]+[u for pair in zip(g,j) for u in pair])[::-1]
    D={2*(i+1):v for i,v in enumerate(b[::-1])}
    N={**D,**{2*i+1:v for i,v in enumerate(a[::-1][:m])}}
    t=T();t.rational(w,N,D,len(w));return t,12*(4*m+2)

def ref_even(a,b,row):
    A=row[:a]+[1];B=row[a:a+b]+[1];W=row[a+b:];r=a-b
    E=W[0:2*r:2]+[0]*b;F=W[1:2*r:2]+[0]*b
    G=W[2*r::2];J=W[2*r+1::2]
    if b:
        E=[x^y for x,y in zip(E,P.quo(P.pmul(A,G),B))]
        F=[x^y for x,y in zip(F,P.quo(P.pmul(A,J),B))]
        for i in range(b):E[i+1]^=J[i];F[i]^=G[i]
    return row[:a+b]+[v for xy in zip(E,F) for v in xy]

def emit(t,Q,rev):
    cb=km.CircuitBuilder();cb.set_max_qubits(Q);q=list(cb.create_quantum_register(Q,'W'))
    for k,*a in (reversed(t.ops) if rev else t.ops):
        if k==0:cb.cx(q[a[0]],q[a[1]])
        else:cb.ccx(q[a[0]],q[a[1]],q[a[2]])
    return cb.finish_circuit()
def verify(t,Q,ref,tag,rng,keep=False):
    rows=[[rng.randrange(4096) for _ in range(Q//12)] for _ in range(30)]+[[0]*(Q//12),[4095]*(Q//12)]
    targets=[ref(r) for r in rows]
    def pack(r):return ((np.array(r,dtype=np.uint16)[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(r),Q).T.astype(bool)
    A,B=pack(rows),pack(targets);q=km.array([km.q(i) for i in range(Q)])
    c=emit(t,Q,False);ic=emit(t,Q,True);path=DIR/(tag+'.kmb')
    c.to_file(str(path),format='kmb');c=km.Circuit.from_file(str(path))
    assert int(c.operation_statistics().num_toffoli_like)==42*t.products and c.num_qubits==Q
    for seed in (19,97):
        for circ,inp,out in ((c,A,B),(ic,B,A)):
            s=km.Simulator(batch_size=len(rows),seed=seed,debug_print=False,counting_operations=True)
            s.use_same_registers_as(circ);s.write_across_shots(q,inp);s.do(circ)
            assert np.array_equal(s.read_across_shots(q),out),tag
            assert not np.any(s.read_phase_flipped_across_shots())
    rec=dict(tag=tag,Q=Q,CCX=42*t.products,ops=len(c),shots=4*len(rows),errors=0,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    if not keep:path.unlink()
    print(json.dumps(rec),flush=True);return rec

if __name__=='__main__':
    P.check_rank42();rng=random.Random(316089679);out=[]
    for a in range(1,18):
        for b in range(a):
            for direct in ([False,True] if (a,b) in [(17,13),(17,14),(10,9),(8,1)] else [False]):
                t,Q=even(a,b,direct)
                if a==17 and b==13 and not direct:assert t.products==204
                out.append(verify(t,Q,lambda r:ref_even(a,b,r),f'general_even_{a}_{b}_{int(direct)}',rng,(a,b) in [(17,13),(17,14),(10,9)]))
    for m in range(1,18):
        t,Q=odd(m);out.append(verify(t,Q,lambda r:P.reference(m,r),f'general_odd_{m}',rng,m==17))
    (DIR/'general_receipt.json').write_text(json.dumps(out,indent=2)+'\n')
