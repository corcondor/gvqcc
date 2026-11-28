"""Gap obstruction for the #263/#266 monic degree-35 padding chart.

A 32-point affine F2-subspace has square-free locator L=H^2+s^2 X.
For D=X(X^2+X+k)L, compute exact half-degree Euclidean remainders.
No simulator and no claim of native correctness.
"""
import json
from pathlib import Path
from random import Random
MOD=0x1053
EXP=[1]
for _ in range(4094):
    x=EXP[-1]<<1
    EXP.append(x^MOD if x&4096 else x)
assert len(set(EXP))==4095
LOG={x:i for i,x in enumerate(EXP)}
EXP*=2
def mul(a,b): return EXP[LOG[a]+LOG[b]] if a and b else 0
def inv(a): return EXP[4095-LOG[a]]
def sqrt(a): return EXP[(2048*LOG[a])%4095] if a else 0
def trace(a):
    t=0
    for _ in range(12):
        t^=a
        a=mul(a,a)
    assert t in (0,1)
    return t
def trim(p):
    while p and not p[-1]: p.pop()
    return p
def add(a,b):
    p=[0]*max(len(a),len(b))
    for i,v in enumerate(a):p[i]^=v
    for i,v in enumerate(b):p[i]^=v
    return trim(p)
def scale(a,c): return trim([mul(x,c) for x in a])
def prod(a,b):
    if not a or not b:return []
    p=[0]*(len(a)+len(b)-1)
    for i,u in enumerate(a):
        for j,v in enumerate(b):p[i+j]^=mul(u,v)
    return trim(p)
def div(a,b):
    a=trim(a[:]); b=trim(b[:]); assert b
    q=[0]*max(0,len(a)-len(b)+1); bi=inv(b[-1])
    while len(a)>=len(b):
        j=len(a)-len(b); u=mul(a[-1],bi);q[j]=u
        for i,v in enumerate(b):a[i+j]^=mul(u,v)
        trim(a)
    return trim(q),a
def check(L,k):
    assert len(L)==33 and all(not L[j] for j in range(3,33,2)) and L[1]
    H=[sqrt(x) for x in L[::2]]
    s=sqrt(L[1]); r=sqrt(k); assert r
    D=prod([0,k,1,1],L)
    A=trim([sqrt(x) for x in D[::2]])
    B=trim([sqrt(x) for x in D[1::2]])
    # Predicted A, B and the first two polynomial divisions.
    assert A==add([0]+H,scale([0,r,1],s))
    assert B==add(prod([r,1],H),[0,s])
    q1,R=div(A,B)
    assert q1==[1] and len(R)==17
    q2,W=div(B,R)
    assert q2==[1,inv(r)]
    assert W==scale([0,k,1,1],mul(s,inv(r)))
    assert len(W)==4
    # This next quotient has degree 13, not <=2.
    q3,_=div(R,W)
    assert len(q3)==14
    return (17,17,16,3),len(q3)-1
def main():
    rng=Random(26620261128); ks=[k for k in range(4096) if trace(k)==1]
    assert len(ks)==2048
    count=0; examples=[]
    for i in range(4):
        offset=(rng.randrange(64,4096)&~63)
        multiplier=rng.randrange(1,4096)
        xs=[mul(multiplier,offset^j) for j in range(32)]
        assert len(set(xs))==32 and all(xs)
        L=[1]
        for x in xs:L=prod(L,[x,1])
        for k in ks:
            seq,gap=check(L,k);count+=1
        examples.append(dict(offset=offset,multiplier=multiplier,locator=L,degree_sequence=seq,next_quotient_degree=gap))
    out=dict(scope="exact algebra on legal affine-subspace locators; not a native circuit replay",
             supports=4,root_free_quadratics=len(ks),cases=count,failures=0,
             next_quotient_degree=13,allowed_gap=2,examples=examples)
    Path("gap32_receipt.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="examples"}))
if __name__=="__main__": main()
