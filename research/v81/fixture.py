from random import Random
from struct import pack
R=Random(81213); F=4096; M=4095; N=35
def mul(a,b):
    z=0
    while b:
        if b&1:z^=a
        b>>=1;a<<=1
        if a&F:a^=0x1053
    return z
def pw(a,n):
    z=1
    while n:
        if n&1:z=mul(z,a)
        a=mul(a,a);n>>=1
    return z
def polyprod(a,b):
    c=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):c[i+j]^=mul(x,y)
    return c
def ev(p,x):
    y=0
    for a in p[::-1]:y=mul(y,x)^a
    return y
def quotient_linear(p,r):
    q=[0]*(len(p)-1);q[-1]=p[-1]
    for i in range(len(q)-2,-1,-1):q[i]=p[i+1]^mul(r,q[i+1])
    assert p[0]==mul(r,q[0]);return q
exp=[1]
for _ in range(1,M):exp.append(mul(exp[-1],2))
assert len(set(exp))==M and mul(exp[-1],2)==1
q=[0]*851;c=[0]*49142;phase=0
for l in range(64):
    w=l if l<=35 else R.randrange(27,36)
    js=R.sample(range(M),w);es=[R.randrange(1,F) for _ in js];rs=[exp[j] for j in js]
    P=[1]
    for r in rs:P=polyprod(P,[r,1])
    V=[0]*N
    for r,e in zip(rs,es):
        h=quotient_linear(P,r); d=ev(h,r);assert d
        s=mul(e,pw(d,F-2))
        for i,v in enumerate(h):V[i]^=mul(s,v)
    P=[0]*(N-w)+P
    assert len(P)==N+1 and P[N]==1
    assert all(ev(P,r)==0 and ev(V,r)==e for r,e in zip(rs,es))
    for i,v in enumerate(P[:N]+V):
        for b in range(12):q[12*i+b]|=((v>>b)&1)<<l
    masks=[R.randrange(F) for _ in range(M)]
    if l==36:masks=[0]*M
    if l==37:masks=[(1<<(j%12)) for j in range(M)]
    for j,v in enumerate(masks):
        for b in range(12):c[12*j+b]|=((v>>b)&1)<<l
    expected=sum((e&masks[j]).bit_count() for j,e in zip(js,es))&1
    phase|=expected<<l
open('fixture.bin','wb').write(pack('<'+'Q'*(len(q)+len(c)+1),*(q+c+[phase])))
print('64 independent sparse-error instances; weights 0 through 35 plus high weights; zero and one-hot masks included')
