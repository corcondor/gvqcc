import hashlib,json,sys
from pathlib import Path
P=0x1053
def mul(a,b):
    z=0
    while b:
        if b&1:z^=a
        b>>=1;a<<=1
        if a&4096:a^=P
    return z
def inv(a):
    assert a
    q=1;b=a;n=4094
    while n:
        if n&1:q=mul(q,b)
        n>>=1;b=mul(b,b)
    assert mul(q,a)==1
    return q
def val(a,x):
    v=0
    for u in a[::-1]:v=mul(v,x)^u
    return v
def solve(m):
    k=len(m)
    m=[r.copy() for r in m]
    for i in range(k):
        j=next((j for j in range(i,k) if m[j][i]),None)
        if j is None:return None
        m[j],m[i]=m[i],m[j]
        q=inv(m[i][i]);m[i][i:]=[mul(q,t) for t in m[i][i:]]
        for row in range(k):
            if row!=i and (v:=m[row][i]):m[row][i:]=[a^mul(v,b) for a,b in zip(m[row][i:],m[i][i:])]
    return [z[-1] for z in m]
def locator(s,k=35):
    assert len(s)>=2*k
    coeff=solve([s[i:i+k+1] for i in range(k)])
    if coeff is None:return None,None
    c=coeff+[1]
    for i in range(k):
        v=0
        for j,x in enumerate(c):v^=mul(x,s[i+j])
        assert v==0
    return c,[x for x in range(4096) if val(c,x)==0]
def all_moments(support,amp,k):
    a=amp.copy();z=[]
    for _ in range(k):
        agg=0
        for v in a:agg^=v
        z.append(agg)
        a=[mul(x,v) for x,v in zip(support,a)]
    return z

def field_pow(a,k):
    z=1
    while k:
        if k&1:z=mul(z,a)
        a=mul(a,a);k>>=1
    return z

f=json.loads(Path(sys.argv[1]).read_text())
expected=dict(zip((field_pow(2,j) for j in f['error_indices']),f['error_values']))
p=[2890,0,1,0,1]
assert all(val(p,x) for x in range(4096))
for row in f['native_rows']:
    y=row['output']
    c,roots=locator(y)
    assert c is not None and len(roots)<35
    z=[y[i+4]^y[i+2]^mul(2890,y[i]) for i in range(66)]
    _,support=locator(z,33)
    assert set(support)==set(expected)
    # The recovered unknown is x*e(x)*p(x), since DQI starts with exponent 1.
    cols=[all_moments([x],[1],33) for x in support]
    v=solve([list(a)+[b] for a,b in zip(zip(*cols),z)])
    e=[mul(a,inv(mul(x,val(p,x)))) for x,a in zip(support,v)]
    assert dict(zip(support,e))==expected
    assert all_moments(support,[mul(x,a) for x,a in zip(support,e)],70)==row['input']
    print(json.dumps(dict(circuit=row['circuit'],raw_rank=35,raw_roots=roots,raw_locator=c,filtered_rank=33,
                          filtered_roots=len(support),recovered_all_70=True,recovered_all_33=True)))
