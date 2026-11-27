"""Syndrome-only reference with strict sparse certificate; not KMB."""
from field_reference import mul,div,prod,trim,add,evalp,EXP,LOG,eea_trace
M=4095;W=35;N=70
def syndromes(errors):
    out=[0]*N
    for p,e in errors.items():
        if not(0<=p<M and 0<e<=M):raise ValueError('invalid error')
        a=EXP[p];power=a
        for j in range(N):out[j]^=mul(e,power);power=mul(power,a)
    return out
def bm_locator(s):
    C,B=[1],[1];L,m,b=0,1,1
    for n,x in enumerate(s):
        delta=x
        for i in range(1,L+1):
            if i<len(C):delta^=mul(C[i],s[n-i])
        if not delta:m+=1;continue
        old=C[:];ratio=div(delta,b)
        C=add(C,[0]*m+[mul(ratio,z) for z in B])
        if 2*L<=n:L=n+1-L;B=old;b=delta;m=1
        else:m+=1
    if len(C)-1!=L or L>W or not C or C[0]!=1:raise ValueError('invalid locator')
    return C
def recover(s,lam):
    if len(s)!=N or any(not isinstance(x,int) or not 0<=x<=M for x in s):raise ValueError('invalid syndrome')
    if not lam or lam[0]!=1 or len(lam)-1>W:raise ValueError('invalid locator')
    omega=trim(prod(s,lam)[:N]);d=len(lam)-1
    if len(omega)>d:raise ValueError('key equation degree')
    derivative=trim([lam[j] if j%2 else 0 for j in range(1,len(lam))]);errors={}
    for p in range(M):
        z=EXP[(-p)%M]
        if evalp(lam,z)==0:
            den=evalp(derivative,z)
            if not den:raise ValueError('non-simple root')
            v=div(evalp(omega,z),den)
            if not v:raise ValueError('zero magnitude')
            errors[p]=v
    if len(errors)!=d or syndromes(errors)!=s:raise ValueError('sparse certificate failure')
    return errors
def decode(s):
    s=list(map(int,s))
    if len(s)!=N or any(not 0<=x<=M for x in s):raise ValueError('invalid syndrome')
    return recover(s,bm_locator(s))
def decode_eea(s):
    s=list(map(int,s));trace,t,r=eea_trace(s)
    if not t or not t[0]:raise ValueError('EEA normalization failure')
    return recover(s,[div(x,t[0]) for x in t])
def phase(errors,mbuc):
    if len(mbuc)!=M:raise ValueError('mbuc length')
    return sum((v&int(mbuc[p])).bit_count() for p,v in errors.items())%2
