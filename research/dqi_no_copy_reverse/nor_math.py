"""Independent algebra test of no-copy reverse chart; not native verifier."""
import random,json
F=4096;K=2048
EXP=[1]
for _ in range(1,F-1):
    x=EXP[-1]<<1;EXP.append(x^0x1053 if x&F else x)
assert len(set(EXP))==4095
LOG=[-1]*F
for i,x in enumerate(EXP):LOG[x]=i
EXP*=2
def m(a,b):return EXP[LOG[a]+LOG[b]] if a and b else 0
def inv(a):assert a;return EXP[4095-LOG[a]]
def mul(a,b):
    a0,a1=a&4095,a>>12;b0,b1=b&4095,b>>12
    t=m(a1,b1)
    return (m(a0,b0)^m(K,t))|((m(a0,b1)^m(a1,b0)^t)<<12)
def inverse(a):
    x,y=a&4095,a>>12;n=m(x,x)^m(x,y)^m(K,m(y,y));n=inv(n)
    return m(x^y,n)|(m(y,n)<<12)
def div(a,b):return mul(a,inverse(b))
def sq(a):return mul(a,a)
def fwd(n,d,l,head,q,c):
    h=(head>>12);t=mul(c,head)^h
    return mul(q,d),n^mul(head,d),mul(q,l^mul(t,sq(d)))
def rev(n,d,l,head,q,c):
    x=div(n,q);t=mul(c,head)^(head>>12)
    return d^mul(head,x),x,div(l,q)^mul(t,sq(x))
def scalar(n,d,heads,qs,back=False):
    for h,q in (reversed(list(zip(heads,qs))) if back else zip(heads,qs)):
        if back:x=div(n,q);n,d=d^mul(h,x),x
        else:n,d=mul(q,d),n^mul(h,d)
    return n,d
def parity(mask,x):return (mask&x).bit_count()&1
rng=random.Random(20261128);count={k:0 for k in ['regular','pole_D','zero_N']};checks=0
for gi in range(8,17):
    for case in count:
        for j in range(32):
            while True:
                qs=[rng.randrange(1,F) for _ in range(gi)]
                qs=[q for q in qs for _ in (0,1)]
                heads=[rng.randrange(1<<24) for _ in qs];cs=[];c=0
                for q in qs:cs.append(c);c^=inv(q)
                assert c==0
                if case=='regular':n0=rng.randrange(1<<24);break
                n,d=scalar(int(case=='pole_D'),int(case=='zero_N'),heads,qs,True)
                if d:n0=div(n,d);break
            l0=rng.randrange(1<<24);n,d,l=n0,1,l0
            for h,q,c in zip(heads,qs,cs):n,d,l=fwd(n,d,l,h,q,c)
            assert n or d
            if case=='pole_D':assert d==0 and n
            if case=='zero_N':assert n==0 and d
            pole=not d;C=n if pole else d
            n,d=(d,n) if pole else (n,d)
            n,d,l=div(n,C),1,div(l,sq(C))
            if pole:n,d=d,n
            for h,q,c in reversed(list(zip(heads,qs,cs))[1:]):n,d,l=rev(n,d,l,h,q,c)
            q=qs[0];n,d,l=d,div(n,q),div(l,q)
            assert d==inverse(C)
            n,l=div(n,d)^heads[0],div(l,sq(d))^(heads[0]>>12)
            assert (n,l)==(n0,l0)
            r,s=scalar(n,1,heads,qs);assert (r if pole else s)==C and (not s)==pole
            for _ in range(3):
                mask=rng.randrange(1<<24);pm=rng.randrange(2)
                assert parity(mask,C)^parity(mask,r if pole else s)^(pm*int(pole))^(pm*int(not s))==0
                checks+=1
            assert scalar(r,s,heads,qs,True)==(n0,1)
            count[case]+=1
result=dict(field='GF(2^24) over GF(4096), K=2048',cases=count,checks=checks,all_pass=True,scope='independent algebra only, not native KMB')
print(json.dumps(result,indent=2));open('nor_math.json','w').write(json.dumps(result,indent=2)+'\n')
