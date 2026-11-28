"""Exact arithmetic reference; data-dependent degree/pivot control is NOT a native circuit.
Use the same one-pass extended-Euclid comparator for all methods.
"""
import json
from pathlib import Path
from packed_return import mul as M,inv as I,EXP,LOG
def S(x):return M(x,x)
def R(x):return EXP[(LOG[x]*2048)%4095] if x else 0
def trim(a):
    a=list(a)
    while a and not a[-1]:a.pop()
    return a
def add(a,b):return trim([(a[i] if i<len(a) else 0)^(b[i] if i<len(b) else 0) for i in range(max(len(a),len(b)))])
def mul(a,b,c=None):
    if not a or not b:return []
    z=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            z[i+j]^=M(x,y)
            if c is not None:c['mul']+=1
    return trim(z)
def scale(a,k,c=None):
    if k==1:return a[:]
    if c is not None:c['mul']+=len(a)
    return trim(M(v,k) for v in a)
def div(a,b,c=None):
    assert b
    a=list(a);d=len(a)-len(b);z=[0]*max(0,d+1)
    bi=1 if b[-1]==1 else I(b[-1])
    if c is not None and d>=0 and bi!=1 and id(b) not in c['cache']:
        c['inv']+=1;c['cache'][id(b)]=b
    for j in range(d,-1,-1):
        k=M(a[j+len(b)-1],bi);z[j]=k
        if c is not None and bi!=1:c['mul']+=1
        for i in range(len(b)-1):
            a[j+i]^=M(k,b[i])
            if c is not None:c['mul']+=1
        a[j+len(b)-1]=0
    return trim(z),trim(a)
def rem(a,b,c=None):return div(a,b,c)[1]
def exact(a,b,c=None):
    z,r=div(a,b,c);assert not r;return z
def egcd(a,b,c=None,two=True):
    u,v=[1],[];s,t=[],[1]
    while b:
        k,r=div(a,b,c);a,b=b,r
        if two:u,v=v,add(u,mul(k,v,c))
        s,t=t,add(s,mul(k,t,c))
    h=a[-1]
    if h!=1:
        if c is not None and id(a) not in c['cache']:c['inv']+=1
        z=I(h);a=scale(a,z,c);s=scale(s,z,c)
        if two:u=scale(u,z,c)
    return a,u,s
def square(a):return trim([z for v in a for z in (S(v),0)])
def derivative(a):return trim([a[i+1] if i%2==0 else 0 for i in range(len(a)-1)])
def split(a):return trim(R(x) for x in a[::2]),trim(R(x) for x in a[1::2])
def join(a,b):
    z=[0]*max(0,2*len(a)-1,2*len(b))
    for i,x in enumerate(a):z[2*i]=S(x)
    for i,x in enumerate(b):z[2*i+1]=S(x)
    return trim(z)
def counter():return dict(mul=0,inv=0,cache={})
def direct(P,N):
    c=counter()
    if len(P)==1:return [],P,c,0
    h,_,u=egcd(P,derivative(P),c,two=False)
    Q,n=exact(P,h,c),exact(N,h,c);pre=c['mul']
    return rem(mul(n,u,c),Q,c),Q,c,pre
def half(P,N):
    c=counter()
    if len(P)==1:return [],P,c,0
    A,B=split(P);H,u,v=egcd(A,B,c);h=square(H)
    Q,n=exact(P,h,c),exact(N,h,c);pre=c['mul']
    return rem(mul(n,join(v,u),c),Q,c),Q,c,pre
def shared(P,N):
    c=counter()
    if len(P)==1:return [],P,c,0
    A,B=split(P);H,_,u=egcd(B,A,c,two=False);h=square(H)
    Q,n=exact(P,h,c),exact(N,h,c)
    A,B=exact(A,H,c),exact(B,H,c);C,D=split(n);pre=c['mul']
    if len(Q)==1:return [],Q,c,pre
    G=rem(mul(rem(C,B,c),u,c),B,c)
    J=rem(mul(rem(D,B,c),u,c),B,c)
    E=add(exact(add(C,mul(A,G,c)),B,c),[0]+J)
    F=add(exact(add(D,mul(A,J,c)),B,c),G)
    return join(E,F),Q,c,pre
def ev(a,x):
    y=0
    for v in a[::-1]:y=M(y,x)^v
    return y
def trace(x):
    z=0
    for _ in range(12):z^=x;x=S(x)
    assert z in (0,1);return z
class RNG:
    def __init__(self):self.s=23972611
    def rand(self,n):
        x=self.s;x^=(x<<13)&0xffffffff;x^=x>>17;x^=(x<<5)&0xffffffff;self.s=x;return x%n
def syndrome(xs,es):
    ss=[0]*70
    for x,e in zip(xs,es):
        z=M(x,e)
        for k in range(70):ss[k]^=z;z=M(z,x)
    return ss
def recurrence(P,ss):
    for i in range(len(ss)-len(P)+1):
        z=0
        for j,v in enumerate(P):z^=M(v,ss[i+j])
        if z:return False
    return True
def main():
    rng=RNG();ghosts=[x for x in range(1,4096) if trace(x)==1]
    stats={};checks=miss=repeat=phase=0
    for w in range(36):
        for t in range(30):
            mode=t%3;xs=[]
            while len(xs)<w:
                x=rng.rand(4095)+1
                if x not in xs:xs.append(x)
            es=[rng.rand(4095)+1 for x in xs]
            P=[1]
            for x in xs:P=mul(P,[x,1])
            extra=0 if mode==0 else (35-w)//2;used=[]
            while extra:
                k=ghosts[rng.rand(len(ghosts))]
                if k in used:continue
                used.append(k);m=2 if mode==2 and extra>=2 else 1
                for _ in range(m):P=mul(P,[k,1,1])
                extra-=m
            N=[]
            for x,e in zip(xs,es):N=add(N,scale(exact(P,[x,1]),e))
            a,b,d=[fn(P,N) for fn in (direct,half,shared)]
            assert a[:2]==b[:2]==d[:2]
            ss=syndrome(xs,es);assert recurrence(P,ss)
            for x,e in zip(xs,es):assert ev(d[0],x)==e;checks+=1
            # Deterministic independent public mask. This does not affect synthesis.
            mask=[(x*109+17*t+19*w)&4095 for x in xs]
            assert trace(sumxor(M(e,m) for e,m in zip(es,mask)))==trace(sumxor(M(ev(d[0],x),m) for x,m in zip(xs,mask)))
            phase+=1
            if w:
                assert not recurrence(exact(P,[xs[0],1]),ss);miss+=1
                pp=mul(P,[xs[0],1]);nn=mul(N,[xs[0],1]);A,B=split(pp)
                H,_,_=egcd(A,B);assert rem(nn,square(H));repeat+=1
            z=stats.setdefault(mode,dict(n=0,direct=[0,0,0],half=[0,0,0],shared=[0,0,0],max=[0,0,0]));z['n']+=1
            for i,(key,v) in enumerate(zip(('direct','half','shared'),(a,b,d))):
                for j,x in enumerate((v[2]['mul'],v[2]['inv'],v[3])):z[key][j]+=x
                z['max'][i]=max(z['max'][i],v[2]['mul'])
    for z in stats.values():
        for key in ('direct','half','shared'):z[key]=[x/z['n'] for x in z[key]]
    out=dict(cases=1080,amplitude_checks=checks,phase_cases=phase,missing_root_rejected=miss,repeated_physical_rejected=repeat,stats=stats,scope='Synthetic GF4096 reference; not a paid gate count')
    print(json.dumps(out,indent=2));Path(__file__).with_name('reference_receipt.json').write_text(json.dumps(out,indent=2)+'\n')
def sumxor(xs):
    z=0
    for x in xs:z^=x
    return z
if __name__=='__main__':main()
