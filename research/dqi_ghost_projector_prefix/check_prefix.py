from ghost_prefix import *
import random,json
from pathlib import Path

def test(k,l,m,n,exhaustive=False):
    a=list(range(k)); b=list(range(k,k+l));d=list(range(k+l,2*(k+l)-1));v=list(range(d[-1]+1,d[-1]+1+m));t=list(range(v[-1]+1,v[-1]+1+m));flag=t[-1]+1;Q=flag+1
    rng=random.Random(20261128+k+l)
    if exhaustive:
        n=1<<Q;rows=[sum(((i>>j)&1)<<i for i in range(n)) for j in range(Q)]
    else:
        rows=[rng.getrandbits(n) for i in range(Q)]
        for j in range(n):
            aa=(j%4)&1;bb=(j%4)>>1
            for s,good in ((a,aa),(b,bb)):
                for i in s:rows[i]|=1<<j
                if not good:rows[rng.choice(s)]^=1<<j
    mask=(1<<n)-1
    def prod(ss):
        z=mask
        for i in ss:z&=rows[i]
        return z
    p=prod(a)^prod(a+b);want=rows[:]
    for x,y in zip(v,t):want[y]^=p&rows[x]
    old=reference(a,b,d,v,t,flag);new=fused(a,b,d,v,t)
    assert run(old,rows)==run(new,rows)==want
    assert run(new[::-1],want)==rows
    z=indicator(a,b,d[:-1],flag);w=rows[:];w[flag]^=p;assert run(z,rows)==w and run(z[::-1],w)==rows
    return dict(a=k,b=l,payload=m,shots=n,qubits=Q,old=count(old),new=count(new),indicator=count(z),failures=0,reverse_failures=0,dirty_restored=True)
r=[test(2,1,1,0,True),test(2,2,1,0,True),test(24,24,24,8192)]
Path(__file__).with_name('prefix_receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
