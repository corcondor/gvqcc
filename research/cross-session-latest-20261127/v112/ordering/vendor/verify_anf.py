from pathlib import Path
from collections import Counter
import json,sys,hashlib
Z=frozenset(); O=frozenset([0])
def add(a,b):return a^b
def mul(a,b):
    if not a or not b:return Z
    if a==O:return b
    if b==O:return a
    if a==b:return a
    out=set()
    for x in a:
        for y in b:
            z=x|y
            if z in out:out.remove(z)
            else:out.add(z)
    if len(out)>200000:raise ValueError('ANF cap')
    return frozenset(out)
def blocks(path):
    ls=Path(path).read_text().splitlines();i=0
    while i<len(ls):
        h=ls[i].split(); assert h[0]=='PATCH'; i+=1;a=[];b=[]
        while ls[i]!='AFTER':a.append(tuple(map(int,ls[i].split())));i+=1
        i+=1
        while ls[i]!='END':b.append(tuple(map(int,ls[i].split())));i+=1
        i+=1;yield h,a,b

def check(a,b,depth):
    qs=sorted({q for g in a+b for q in g[2:5] if q>=0});bs=sorted({q for g in a+b for q in g[5:] if q>=0});
    v=0;vars={}
    def fresh():
        nonlocal v
        v+=1;return frozenset([1<<v])
    q0={q:fresh() for q in qs};b0={k:fresh() for k in bs};sc=[O]
    for _ in range(depth):sc.append(mul(sc[-1],fresh()))
    hmrs=sum((g[1]&127)==80 for g in a);assert hmrs==sum((g[1]&127)==80 for g in b);outcomes=[fresh() for _ in range(hmrs)]
    def run(ops):
        q=q0.copy();bits=b0.copy();scope=sc.copy();phi=Z;h=0;paid=Counter()
        for i,raw,x,y,z,m,k in ops:
            t=raw&127
            e=mul(scope[-1],bits[k] if k>=0 else O)
            if t==1:
                if k>=0:scope.append(e)
                else:assert len(scope)>1;scope.pop()
            elif t==0:phi^=e
            elif t==17:q[x]^=e
            elif t==33:q[y]^=mul(e,q[x])
            elif t==49:q[z]^=mul(e,mul(q[x],q[y]));paid[e]+=1
            elif t in (16,32,48):
                p=e
                for w in (x,y,z):
                    if w>=0:p=mul(p,q[w])
                phi^=p
                if t==48:paid[e]+=1
            elif t in (34,50):
                if t==50:e=mul(e,q[x]);x,y=y,z;paid[mul(scope[-1],bits[k] if k>=0 else O)]+=1
                d=mul(e,q[x]^q[y]);q[x]^=d;q[y]^=d
            elif t in (64,65,66):
                if t==64:bits[m]^=mul(e,bits[m])
                elif t==65:bits[m]^=mul(e,bits[m]^O)
                else:bits[m]^=e
            elif t==80:
                phi^=mul(e,mul(q[x],outcomes[h]));q[x]^=mul(e,q[x]);bits[m]^=mul(e,bits[m]^outcomes[h]);h+=1
            else:raise ValueError(('unknown',t))
        return q,bits,scope,phi,h,paid
    x=run(a);y=run(b);assert x[:5]==y[:5],('ANF mismatch',a,b)
    assert all(n<=x[5][p] for p,n in y[5].items()),'paid branch increased'
    return {'variables':v,'before_paid':sum(x[5].values()),'after_paid':sum(y[5].values()),'removed_guards':[(len(p),n) for p,n in (x[5]-y[5]).items()]}
if __name__=='__main__':
    res=[]
    for path in sys.argv[1:]:
        r=[]
        for h,a,b in blocks(path):
            depth=int(h[-1]) if Path(path).name=='donor.txt' else 0
            q=check(a,b,depth);r.append(q)
        res.append(dict(path=path,blocks=len(r),before_paid=sum(x['before_paid'] for x in r),after_paid=sum(x['after_paid'] for x in r),max_variables=max([x['variables'] for x in r],default=0),details=r if Path(path).name=='donor.txt' else None))
    print(json.dumps(res,indent=2))