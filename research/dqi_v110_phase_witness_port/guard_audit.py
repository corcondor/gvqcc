"""Counterexample / archive screen; no synthetic example is a native failure."""
import collections, hashlib, json, sys, zipfile
from pathlib import Path

def mul(x,y):
    out=0
    while y:
        if y&1: out^=x
        y>>=1
        x<<=1
        if x&4096: x^=0x1053
    return out
def pow_(x,n):
    r=1
    for _ in range(n): r=mul(r,x)
    return r
def xor_(xs):
    r=0
    for x in xs:r^=x
    return r
def product(a,b):
    c=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):c[i+j]^=mul(x,y)
    return c

def make():
    exps=list(range(1,409,37))
    mag=[777,156,2137,3654,376,821,1349,387,320,1903,2531,1704]
    p=[1]
    for k in [3134,3169,3257,3302,3384,3431]:
        p=product(p,[mul(k,k),0,1,0,1])
    xs=[pow_(2,i) for i in exps]
    assert len(xs)==len(mag)==12 and len(set(xs))==12
    d=len(p)-1
    assert d==24 and p[-1]==1 and all(xor_(mul(c,pow_(x,i)) for i,c in enumerate(p)) for x in xs)
    s=[xor_(mul(a,pow_(x,j)) for a,x in zip(mag,xs)) for j in range(1,71)]
    r=s[:d]
    while len(r)<70:
        r.append(xor_(mul(a,b) for a,b in zip(p,r[-d:])))
    y=[a^b for a,b in zip(s,r)]
    assert y[:35]==[0]*35 and y[35:40]==[1,1466,399,1393,1477]
    return dict(w=12,d=24,exponents=exps,magnitudes=mag,annihilator=p,input=s,residual=r,returned=y)

def audit(path):
    with zipfile.ZipFile(path) as z:
        rows=[y for line in z.read('native_pairs.jsonl').splitlines() for y in json.loads(line)['actual']]
    positions=collections.Counter(next((i+1 for i,x in enumerate(y) if x),71) for y in rows)
    return dict(sha256=hashlib.file_digest(open(path,'rb'),'sha256').hexdigest(),samples=len(rows),
                first_nonzero_word=dict(positions),zero_first35=sum(not any(y[:35]) for y in rows))
if __name__=='__main__':
    result=dict(sharp_synthetic=make())
    if len(sys.argv)>1: result['archived_native']=audit(sys.argv[1])
    print(json.dumps(result,indent=2))
