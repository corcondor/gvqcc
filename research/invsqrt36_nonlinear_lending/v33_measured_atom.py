"""V33 exact native 30265 measured-atom donor.
Run inside the V33 companion archive (v32_rank/affine_reset dependencies).
Preserves every original HMR outcome; an independent scratch outcome is
generated and reset. Full integration requires explicit event alignment.
"""
from v32_rank import *

def donor(scratch):
    out=[Op(80,(33,),measurement=1),
         Op(160,(6,14),condition=1),
         Op(49,(21,24,33)),
         Op(160,(28,33),condition=419)]
    out += [Op(160,(q,33),condition=837) for q in [35,31,12,7,3,34,11]]
    out += [Op(144,(33,),condition=1),Op(33,(33,28)),
            Op(80,(33,),measurement=scratch),
            Op(160,(21,24),condition=scratch),
            Op(64,(),measurement=scratch),Op(49,(6,14,33))]
    return out

def replay(B,s,c,events,gs):
    M=Machine(B,s,c);it=iter(events)
    for o in gs:M.step(o,next(it) if o.raw&127==80 else None)
    assert next(it,None) is None and not M.stack
    return M

def main():
    K=NativeKMB.read('v27_low_lazy.kmb');a=30265;c=parents()[a]
    gs=[o for _,_,_,_,g,_ in c['path'] for o in g]
    used={v for o in K.ops for v in (o.measurement,o.condition) if v is not None}
    scratch=next(i for i in range(K.header[2]) if i not in used)
    assert scratch==1018
    B=BDD(NLEGAL);Q=Machine(B,[B.leaf(mask(i,NLEGAL)) for i in range(22)]+[B.zero]*15)
    for o in K.ops[:a]:
        Q.step(o,B.variable() if o.raw&127==80 else None)
        Q.p=B.zero;Q.rot=[]
    s=[Q.s[36] if q==c['d'] else Q.s[q] for q in range(36)]
    assert Q.c.get(scratch,B.zero) is B.zero
    assert B.and_(s[6],s[14]) is s[33]
    m=B.variable();n=B.variable();new=donor(scratch)
    X=replay(B,s,Q.c,[m],gs);Y=replay(B,s,Q.c,[m,n],new)
    assert X.s==Y.s and X.p is Y.p and X.rot==Y.rot
    assert X.stack==Y.stack and X.active is Y.active
    assert all(X.c.get(k,B.zero) is Y.c.get(k,B.zero) for k in X.c.keys()|Y.c.keys())
    assert cost(gs)==(3,17) and cost(new)==(2,17)
    print("PASS",a,NLEGAL,B.nvar,scratch,cost(gs),cost(new))

if __name__=='__main__':main()
