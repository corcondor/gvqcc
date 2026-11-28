"""Native SDK reproduction of blocked residual GCD, with exact same fixed profiles.
No dynamic degree selection, no full DQI splice."""
import json,random,hashlib
from pathlib import Path
from functools import lru_cache
import numpy as np
import kickmix as km
import packed_quotient as P
import residue_gcd as S
import general_return as T
DIR=Path(__file__).parent

@lru_cache(None)
def plan(n,active):
    if n<=1:return 0,0
    return min((plan(k,active)[0]+plan(n-k,active)[0]+T.cost(range(k),range(k,n),active,1),k) for k in range(1,n))

def program(ds):
    b,a=ds[:2];n=a+b+2+2*b;ops=[]
    def emit(k,t,x,y=-1):ops.append((k,t,x,y))
    def undo(seg):
        for k,t,x,y in reversed(seg):emit({'ix':'sx','sx':'ix'}.get(k,k),t,x,y)
    def shear(w,c,y,x):
        if y and x and any(i-j in c for i in y for j in x):
            ops.append(('rect',tuple(w),tuple(sorted(c.items())),(tuple(y),tuple(x))))
    def divide(A,X,top,stop,low):
        if top<stop:return
        a=len(A)-1;c={-j:A[a-j] for j in range(1,a+1)};ds=tuple(sorted(c))
        def rec(l,h):
            if h-l==1:emit('ix',X[l],A[-1]);return
            mid=l+plan(h-l,ds)[1];rec(mid,h);shear(X,c,range(l,mid),range(mid,h));rec(l,mid)
        rec(stop,top+1);shear(X,c,range(low,stop),range(stop,top+1))
    def ret(w,B,g):
        c={-j:B[len(B)-1-j] for j in range(1,len(w))};ds=tuple(sorted(c))
        shear(w,c,range(g),range(g,len(w)))
        def rec(l,h):
            if h-l==1:emit('sx',w[l],B[-1]);return
            mid=l+plan(h-l,ds)[1];rec(l,mid);shear(w,c,range(l,mid),range(mid,h));rec(mid,h)
        if g<len(w):rec(g,len(w))
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
        if not profile:undo(first);return a
        k=profile[0];assert 0<=k<a
        h=solve(B[:k+1],A,[row[:a] for row in ps],profile[1:])
        i=len(ops);divide(A,B,a-1,h+1,h+1);tail=ops[i:]
        for row in ps:
            w=row[h:];rotate(w,g,a-h);ret(w,B,g)
        undo(tail);undo(first);return h
    A=list(range(a+1));B=list(range(a+1,a+b+2))
    ps=[list(range(a+b+2+i*b,a+b+2+(i+1)*b)) for i in range(2)]
    assert solve(A,B,ps,ds[2:])==ds[-1]
    return ops,n

def lower(ds,blocked):
    ops,n=(program if blocked else S.program)(ds)
    w=[tuple(range(12*i,12*i+12)) for i in range(n+5)]
    work=w[n:];r=work[0];t=P.Packed(work);cached=None
    def clear():
        nonlocal cached
        if cached is not None:t.inverse_add(w[cached],r);cached=None
    for k,v,x,y in ops:
        if k=='rect':
            yy,xx=y
            if cached in [v[i] for i in yy]:clear()
            a=T.T();a.cross([w[i] for i in v],{k:w[i] for k,i in x},yy,xx,1)
            t.ops.extend(a.ops);t.products+=a.products
            continue
        if cached in ({v,x} if k=='sw' else {v}):clear()
        if k in ('ix','sx'):
            if cached!=x:clear();t.inverse_add(w[x],r);cached=x
            t.word_scale(w[v],r if k=='ix' else w[x],w[x] if k=='ix' else r)
        elif k=='mx':t.madd(w[x],w[y],w[v])
        elif k=='sw':t.swapword(w[v],w[x])
        else:raise ValueError(k)
    clear();return t,work,12*(n+5)

def build(ds,blocked,reverse):
    t,work,Q=lower(ds,blocked);assert Q<=900
    cb=km.CircuitBuilder();cb.set_max_qubits(Q);q=list(cb.create_quantum_register(Q,'W'))
    P.emit(cb,q,P.inverse_ops(t.ops) if reverse else t.ops,work,True)
    return cb.finish_circuit()

def verify(ds,blocked,rows,targets):
    c=build(ds,blocked,False);ic=build(ds,blocked,True);Q=c.num_qubits
    def pack(r):return ((np.array(r,dtype=np.uint16)[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(r),Q).T.astype(bool)
    A,B=pack(rows),pack(targets);q=km.array([km.q(i) for i in range(Q)])
    path=DIR/('blocked_'+'_'.join(map(str,ds))+f'_b{int(blocked)}.kmb')
    c.to_file(str(path),format='kmb');c=km.Circuit.from_file(str(path))
    for seed in (19,97):
        for circ,inp,out in ((c,A,B),(ic,B,A)):
            s=km.Simulator(batch_size=len(rows),seed=seed,debug_print=False,counting_operations=True)
            s.use_same_registers_as(circ);s.write_across_shots(q,inp);s.do(circ)
            assert np.array_equal(s.read_across_shots(q),out),(ds,blocked)
            assert not np.any(s.read_phase_flipped_across_shots())
    rec=dict(profile=ds,blocked=blocked,Q=Q,paid=int(c.operation_statistics().num_toffoli_like),ops=len(c),shots=4*len(rows),errors=0,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    if ds not in ([17,13,7,3],[17,16,12,8,4,0]):path.unlink()
    print(json.dumps(rec),flush=True);return rec

if __name__=='__main__':
    rng=random.Random(316089336);out=[]
    for ds in ([17,13,7,3],[17,16,12,8,4,0],[8,5,3],[17,16],[17,1],[17,0],[12,11,10,9,8,7,6,5,4,3,2,1],[12,10,8,6,4,2,0],[8,7,6,5,4,3,2,1,0],[5,4,1],[5,3,0],[1,0]):
        rows,targets=zip(*(S.make(rng,ds,i) for i in range(32)))
        a,b=[verify(ds,flag,rows,targets) for flag in (False,True)]
        assert b['paid']<=a['paid'];out.append(dict(old=a,new=b))
    (DIR/'blocked_residue_receipt.json').write_text(json.dumps(out,indent=2)+'\n')
