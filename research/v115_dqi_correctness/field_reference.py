"""GF(4096) and independent EEA arithmetic, adapted from PR #181."""
import hashlib,json
MOD=0x1053
EXP=[]; LOG=[-1]*4096
x=1
for i in range(4095):
    assert LOG[x]==-1
    EXP.append(x); LOG[x]=i
    x<<=1
    if x&4096:x^=MOD
assert x==1 and len(set(EXP))==4095
EXP*=2
def mul(a,b):return EXP[LOG[a]+LOG[b]] if a and b else 0
def div(a,b):
    if not b:raise ZeroDivisionError('zero field divisor')
    return EXP[(LOG[a]-LOG[b])%4095] if a else 0
def trim(p):
    p=list(p)
    while p and not p[-1]:p.pop()
    return p
def add(a,b):
    r=[0]*max(len(a),len(b))
    for i,x in enumerate(a):r[i]^=x
    for i,x in enumerate(b):r[i]^=x
    return trim(r)
def prod(a,b):
    if not a or not b:return []
    r=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        if x:
            for j,y in enumerate(b):
                if y:r[i+j]^=mul(x,y)
    return trim(r)
def divrem(a,b):
    a,b=trim(a),trim(b)
    if not b:raise ZeroDivisionError('zero polynomial divisor')
    q=[0]*max(0,len(a)-len(b)+1)
    while len(a)>=len(b):
        off=len(a)-len(b); f=div(a[-1],b[-1]);q[off]^=f
        for j,v in enumerate(b):a[off+j]^=mul(f,v)
        a=trim(a)
    return trim(q),a
def evalp(a,x):
    y=0
    for c in reversed(a):y=mul(y,x)^c
    return y
def eea_trace(s):
    rprev,r=[0]*70+[1],trim(s);tprev,t=[],[1];trace=[]
    while r and len(r)-1>=35:
        q,rem=divrem(rprev,r)
        tn=add(tprev,prod(q,t))
        trace.append((len(r)-1,len(rem)-1))
        rprev,r=r,rem;tprev,t=t,tn
    return trace,trim(t),trim(r)
NODES=(3134,3169,3257,3302,3384,3431,3519,3552,3592,3633,3671,3727,3792,3854,3921,3977,4054)
