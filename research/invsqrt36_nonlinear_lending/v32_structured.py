"""V32 exact donor from the pinned V27 source and V31 bridge portfolio.
The companion ZIP supplies v32_rank, affine_reset and the original chart data.
"""
from v32_rank import *

def main():
    K=NativeKMB.read('v27_low_lazy.kmb')
    c=parents()[30265]
    gs=[o for _,_,_,_,g,_ in c['path'] for o in g]
    assert gs[0]==Op(49,(6,14,33))
    new=[Op(160,(28,33),condition=419)]+gs[1:]+[Op(33,(33,28))]
    new += [Op(160,(q,33),condition=837) for q in [35,31,12,7,3,34,11]]
    new += [Op(144,(33,),condition=1)]
    new=optimize(new)
    # Independent exact audit of the reachable premise.
    B=BDD(NLEGAL)
    Q=Machine(B,[B.leaf(mask(i,NLEGAL)) for i in range(22)]+[B.zero]*15)
    for o in K.ops[:c['a']]:
        Q.step(o,B.variable() if o.raw&127==80 else None)
        Q.p=B.zero; Q.rot=[]
    s=[Q.s[36] if q==c['d'] else Q.s[q] for q in range(36)]
    assert B.and_(s[6],s[14]) is s[33]
    print('exact nonlinear entry premise PASS',NLEGAL,Q.B.nvar if hasattr(Q,'B') else B.nvar)
    del B,Q,s
    out=[dict(c,body=new,v32_removed=[0],v32_rank=[0,0])]
    good,bad=verify(K,out)
    assert len(good)==1 and not bad and Fraction(good[0]['E1'])==2
    pickle.dump((good,bad),open('v32_structured_verified.pkl','wb'))

if __name__=='__main__':
    main()
