"""Exact mixed GF4 plane expansion, Frobenius-square repayment, whole-tape export."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'dqi_rank96_f4'))
import certify as C
rows,_=C.check()
orig=C.originals()
allrows=[('original',i,[(a,b<<24,c) for a,b,c in t],[0]*48) for i,t in enumerate(orig)]
for r,new,_ in rows:
    allrows.append((r['source'],r['type'],[(a,b<<24,c) for a,b,c in new],[0]*48))
seeds=json.loads((HERE.parent/'dqi_rank96_f4/f4_seeds.json').read_text())
mixed=json.loads((HERE/'mixed_f4_results.json').read_text())
def form(a,coord):
    return C.dot(a&0xffffff,coord&0xffffff)^C.dot(a>>24,coord>>24)
def scale(x,k):return C.scale(x,k)
for row in mixed:
    typ=row['type'];seed=seeds[typ]
    cols=seed['inCols']+[x<<24 for x in seed['inCols']]
    terms=[]
    for aa,bb,w in row['terms']:
        a,b=int(aa,16),int(bb,16)
        x,y,z,h=[sum(((form(v,col)>>k)&1)<<i for i,col in enumerate(cols)) for v in (a,b) for k in (0,1)]
        for l,r,c in ((x,z,3),(y,h,1),(x^y,z^h,2)):
            assert l and r and l!=r
            terms.append((l,r,C.transform(seed['outCols'],scale(w,c))))
    fix=[]
    for col in cols:
        v=0
        for i,w in enumerate(row['squareCorrection']):
            t=col>>(2*i)&3;v^=scale(w,C.mul4(t,t))
        fix.append(C.transform(seed['outCols'],v))
    # Check 48 linear and 1128 degree-two coefficients with independent basis evaluation.
    def evaluate(t,x):
        z=0
        for a,b,c in t:
            if C.par(a&x) and C.par(b&x):z^=c
        return z
    for i in range(48):
        assert evaluate(terms,1<<i)^fix[i]==0
        for j in range(i+1,48):
            x=(1<<i)|(1<<j)
            want=C.eval_terms(orig[typ],x&0xffffff,x>>24)
            assert evaluate(terms,x)^fix[i]^fix[j]==want,(typ,i,j)
    allrows.append(('mixed'+str(row['seed']),typ,terms,fix))
    print('MIXED_BINARY_CERT',typ,row['seed'],len(terms),sum(bool(x) for x in fix),1176,flush=True)
with open(sys.argv[1],'w') as f:
    print(len(allrows),file=f)
    for name,i,ts,fix in allrows:
        print(name,i,len(ts),file=f)
        for t in ts:print(*t,file=f)
        print(*fix,file=f)
