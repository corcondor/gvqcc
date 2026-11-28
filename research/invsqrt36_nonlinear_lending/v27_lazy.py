"""Lazy permutation synthesis on recovered V26 low KMB.
Place beside affine_reset.py and engine from the companion archive.
All unconditional SWAPs outside conditional scopes enter the virtual frame.
Every source operation is compared against the mapped target trajectory.
"""
from affine_reset import *
from dataclasses import replace
from collections import Counter

def main(src,out):
    K=NativeKMB.read(src)
    B=BDD(NLEGAL)
    inp=[B.leaf(mask(i,NLEGAL)) for i in range(22)]+[B.zero]*15
    S=Machine(B,inp); D=Machine(B,inp)
    mp=list(range(37)); new=[]; R=Counter(); E=Fraction(0); p0=p1=0
    t=time.time()
    @lru_cache(None)
    def prob(v):
        return Fraction(v.value.bit_count(),NLEGAL) if v.var<0 else (prob(v.low)+prob(v.high))/2
    def nz(M): return int(not any(v is B.zero for v in M.s))
    for i,o in enumerate(K.ops):
        g=o.raw&127
        S.p=D.p=B.zero; S.rot=[]; D.rot=[]
        if g in (48,49,50):
            E+=prob(active(S,o)); prob.cache_clear()
        m=B.variable() if g==80 else None
        if o.raw==34 and not S.stack:
            a,b=o.wires; mp[a],mp[b]=mp[b],mp[a]
            R['virtual_swaps']+=1
        else:
            x=replace(o,wires=tuple(mp[q] for q in o.wires))
            new.append(x); D.step(x,m); p1+=nz(D)
        S.step(o,m); p0+=nz(S)
        assert all(S.s[q] is D.s[mp[q]] for q in range(37))
        assert S.p is D.p and S.rot==D.rot and S.active is D.active and S.stack==D.stack and S.c==D.c,i
    for q in range(22):
        if D.s[q] is inp[q]: continue
        r=next(r for r in range(37) if D.s[r] is inp[q])
        o=Op(34,(q,r)); new.append(o); D.step(o); p1+=nz(D); R['terminal_swaps']+=1
    assert S.s==D.s==inp and not S.stack
    out=Path(out); out.write_bytes(byte_emit(K,new,37))
    T=NativeKMB.read(out); assert T.ops==new
    assert [(k,v) for k,v in K.sections if k not in range(1,10)]==[(k,v) for k,v in T.sections if k not in range(1,10)]
    rec=dict(status='PASS',parent_sha=hashlib.sha256(Path(src).read_bytes()).hexdigest(),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),legal=NLEGAL,hmr=B.nvar,old_ops=len(K.ops),ops=len(new),expected_paid=str(E),old_pressure=p0,new_pressure=p1,stats=dict(R),seconds=time.time()-t)
    out.with_suffix('.json').write_text(json.dumps(rec,indent=2)); print(rec,flush=True)

if __name__=='__main__': main(*sys.argv[1:])
