"""Restricted quadratic common-coordinate test for carry exchanges.
Run beside the V35 companion archive's affine_reset.py and v29_delta.py.
Sampled inconsistency proves no degree <= 2 expression in these coordinates;
it is not a lower bound for arbitrary adaptive circuits."""
from affine_reset import *
from v29_delta import sample
from collections import Counter

def scan(K,n=2048):
    one,S,G,M,D=sample(K,n,3531)
    res=[]
    def rank(xs):
        B={}
        for v in xs:
            r,_=reduce(B,v)
            if r:B[r.bit_length()-1]=(r,0)
        return len(B)
    for i in range(len(K.ops)-3):
        o,x,y,h=K.ops[i:i+4]
        if [g.raw for g in (o,x,y,h)] != [49,33,33,80] or D[i]:continue
        a,b,d=o.wires;c=h.wires[0]
        if len({a,b,c,d})!=4 or x.wires!=(c,d) or y.wires!=(c,a) or S[i][d]:continue
        s=list(S[i]);s[a]^=s[c]
        ids=[k for k in range(37) if k not in (c,d)]
        target=s[b]&s[c]
        cols=[one]+[s[k] for k in ids]
        cols += [s[j]&s[k] for j,k in itertools.combinations(ids,2)]
        before=[one]+[S[i][k] for k in range(37) if k!=d]
        after=[one]+[S[i+4][k] for k in range(37) if k!=c]
        common=[one]+[s[k] for k in ids]
        rec=dict(i=i,a=a,b=b,c=c,d=d,ranks=[rank(before),rank(after),rank(common),rank(before+after)],quadratic_fit=fit(target,cols),quadratic_rank=rank(cols),quadratic_augmented_rank=rank(cols+[target]),samples=n)
        res.append(rec)
    return res

if __name__=='__main__':
    K=NativeKMB.read(sys.argv[1])
    r=scan(K)
    Path(sys.argv[2]).write_text(json.dumps(r,indent=2))
    print(len(r),sum(x['quadratic_fit'] is None for x in r),Counter(tuple(x['ranks']) for x in r))
