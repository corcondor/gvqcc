"""Residual-preserving two-RHS packed solve for fixed Euclid profiles.
No host dispatch on input, no full raw-syndrome splice. All source coefficients
may be nonmonic. Return rho and U, including inconsistent right hand sides.
Uses #329 native inverse/cache and HMR word scale."""
import json,random,hashlib
from pathlib import Path
import numpy as np
import kickmix as km
import packed_quotient as P
import reference_solve as R
DIR=Path(__file__).parent

def program(ds):
    b,a=ds[:2];n=a+b+2+2*b
    ops=[]
    def emit(k,t,x,y=-1):ops.append((k,t,x,y))
    def undo(seg):
        for k,t,x,y in reversed(seg):emit({'ix':'sx','sx':'ix'}.get(k,k),t,x,y)
    def divide(A,X,top,stop,low):
        a=len(A)-1
        for i in range(top,stop-1,-1):
            emit('ix',X[i],A[a])
            for j in range(1,min(a,i-low)+1):emit('mx',X[i-j],X[i],A[a-j])
    def rotate(w,g,a):
        cur=list(w);want=w[a:a+g]+w[:a]
        for i,v in enumerate(want):
            j=cur.index(v)
            if j!=i:emit('sw',w[i],w[j]);cur[i],cur[j]=cur[j],cur[i]
    def solve(A,B,ps,profile):
        a,b=len(A)-1,len(B)-1
        if a==0:
            assert not profile
            for row in ps:
                for v in row:emit('ix',v,A[0])
            return 0
        g=b-a
        for row in ps:divide(A,row,b-1,a,0)
        i=len(ops);divide(A,B,b,a,0);first=ops[i:]
        if not profile:
            undo(first);return a
        k=profile[0];assert 0<=k<a
        h=solve(B[:k+1],A,[row[:a] for row in ps],profile[1:])
        i=len(ops);divide(A,B,a-1,h+1,h+1);tail=ops[i:]
        for row in ps:
            w=row[h:];rotate(w,g,a-h)
            for j in range(a-h):
                i=g+j
                for k in range(i):emit('mx',w[k],w[i],B[b-i+k])
                emit('sx',w[i],B[b])
        undo(tail);undo(first);return h
    A=list(range(a+1));B=list(range(a+1,a+b+2))
    ps=[list(range(a+b+2+i*b,a+b+2+(i+1)*b)) for i in range(2)]
    assert solve(A,B,ps,ds[2:])==ds[-1]
    return ops,n

def lower(ds):
    ops,n=program(ds)
    w=[tuple(range(12*i,12*i+12)) for i in range(n+5)]
    work=w[n:];r=work[0];t=P.Packed(work)
    cached=None
    def clear():
        nonlocal cached
        if cached is not None:t.inverse_add(w[cached],r);cached=None
    for k,v,x,y in ops:
        if cached in ({v,x} if k=='sw' else {v}):clear()
        if k in ('ix','sx'):
            if cached!=x:clear();t.inverse_add(w[x],r);cached=x
            t.word_scale(w[v],r if k=='ix' else w[x],w[x] if k=='ix' else r)
        elif k=='mx':t.madd(w[x],w[y],w[v])
        elif k=='sw':t.swapword(w[v],w[x])
        else:raise ValueError(k)
    clear();return t,work,12*(n+5)

def build(ds,measured,reverse):
    t,work,Q=lower(ds);assert Q<=900
    cb=km.CircuitBuilder();cb.set_max_qubits(Q)
    q=list(cb.create_quantum_register(Q,'W'))
    P.emit(cb,q,P.inverse_ops(t.ops) if reverse else t.ops,work,measured)
    return cb.finish_circuit()

def poly(rng,n):return [rng.randrange(4096) for _ in range(n)]+[rng.randrange(1,4096)]
def pad(a,n):assert len(a)<=n;return a+[0]*(n-len(a))
def make(rng,ds,i):
    Y=poly(rng,ds[-1]);X=[]
    for k in range(len(ds)-2,-1,-1):X,Y=Y,R.add(R.mul(poly(rng,ds[k]-ds[k+1]),Y),X)
    A,B=X,Y;b=ds[0];h=ds[-1]
    H,_,_=R.egcd(B,A);assert len(H)==h+1
    AA=R.exact(A,H);BB=R.exact(B,H);g,_,u=R.egcd(BB,AA,two=False);assert g==[1]
    ps=[[rng.randrange(4096) for _ in range(b)] for j in range(2)]
    if i%4==0:ps[0]=[0]*b
    if i%4==1:ps[0]=pad(R.rem(R.mul(A,[rng.randrange(4096) for _ in range(b-h)]),B),b)
    out=[]
    for p in ps:
        k,r=R.div(p,H);U=R.rem(R.mul(k,u),BB)
        assert R.rem(R.add(R.mul(A,U),R.add(p,r)),B)==[]
        out+=pad(r,h)+pad(U,b-h)
    return A+B+sum(ps,[])+[0]*5,A+B+out+[0]*5

def verify(ds,measured,rng):
    rows,targets=zip(*(make(rng,ds,i) for i in range(32)))
    c=build(ds,measured,False);ic=build(ds,measured,True);Q=c.num_qubits
    def pack(r):return ((np.array(r,dtype=np.uint16)[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(r),Q).T.astype(bool)
    A,B=pack(rows),pack(targets);q=km.array([km.q(i) for i in range(Q)])
    path=DIR/('residue_'+'_'.join(map(str,ds))+f'_h{int(measured)}.kmb')
    c.to_file(str(path),format='kmb');c=km.Circuit.from_file(str(path))
    for seed in (19,97):
        for circ,inp,out in ((c,A,B),(ic,B,A)):
            s=km.Simulator(batch_size=len(rows),seed=seed,debug_print=False,counting_operations=True)
            s.use_same_registers_as(circ);s.write_across_shots(q,inp);s.do(circ)
            assert np.array_equal(s.read_across_shots(q),out),(ds,measured)
            assert not np.any(s.read_phase_flipped_across_shots())
    rec=dict(profile=ds,measured=measured,Q=Q,paid=int(c.operation_statistics().num_toffoli_like),ops=len(c),shots=4*len(rows),errors=0,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    if ds not in ([17,13,7,3],[17,16,12,8,4,0],[8,5,3]):path.unlink()
    print(json.dumps(rec),flush=True);return rec

if __name__=='__main__':
    rng=random.Random(316089678);rows=[]
    for ds in ([17,13,7,3],[17,16,12,8,4,0],[8,5,3],[17,16],[17,1],[17,0],[12,11,10,9,8,7,6,5,4,3,2,1],[12,10,8,6,4,2,0],[8,7,6,5,4,3,2,1,0],[5,4,1],[5,3,0],[1,0]):
        rows.append(verify(ds,True,rng))
        if ds in ([17,13,7,3],[8,5,3]):rows.append(verify(ds,False,rng))
    (DIR/'residue_receipt.json').write_text(json.dumps(rows,indent=2)+'\n')
