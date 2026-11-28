"""Dirty-ladder echo, no HMR, all borrowed wires restored.
For two disjoint bit groups a,b (already negated residue bits),
accumulate (AND(a) XOR AND(a+b))*v_i into each target t_i.
This detects multiplicity exactly one (not arbitrary odd multiplicity).
"""
from collections import Counter

def fused(a,b,d,v,t):
    x=list(a)+list(b); n=len(x); k=len(a)
    assert 2<=k<n and len(d)==n-1 and len(v)==len(t)
    assert len(set(x+d+v+t))==len(x+d+v+t)
    f=[('CCX',x[0],x[1],d[0])]+[('CCX',d[i-1],x[i+1],d[i]) for i in range(1,n-1)]
    combine=[('CX',d[k-2],d[-1])]
    use=[('CCX',d[-1],z,y) for z,y in zip(v,t)]
    out=[]
    for start in (0,1):
        chain=f[start:]
        out+=chain+combine+use+combine+chain[::-1]
    return out

def reference(a,b,d,v,t,flag):
    x=list(a)+list(b); assert len(d)>=len(x)-2
    def toggle(u):
        if len(u)==2:return [('CCX',*u,flag)]
        g=[('CCX',u[0],u[1],d[0])]+[('CCX',d[i-1],u[i+1],d[i]) for i in range(1,len(u)-2)]
        h=[('CCX',d[len(u)-3],u[-1],flag)]
        return g+h+g[::-1]+g[1:]+h+g[1:][::-1]
    g=toggle(a)+toggle(x);use=[('CCX',flag,z,y) for z,y in zip(v,t)]
    return use+g+use+g[::-1]

def indicator(a,b,d,t):
    x=list(a)+list(b);n=len(x);k=len(a)
    assert 2<=k<n and len(d)==n-2
    assert len(set(x+d+[t]))==n+len(d)+1
    f=[('CCX',x[0],x[1],d[0])]+[('CCX',d[i-1],x[i+1],d[i]) for i in range(1,n-2)]
    use=[('CX',d[k-2],t),('CCX',d[-1],x[-1],t)]
    return f+use+f[::-1]+f[1:]+use+f[1:][::-1]

def run(ops,q):
    q=q[:]
    for op,*a in ops:
        if op=='CCX':q[a[2]]^=q[a[0]]&q[a[1]]
        elif op=='CX':q[a[1]]^=q[a[0]]
        elif op=='SWAP':q[a[0]],q[a[1]]=q[a[1]],q[a[0]]
        else:raise ValueError(op)
    return q

def count(g):return dict(Counter(op for op,*_ in g))
