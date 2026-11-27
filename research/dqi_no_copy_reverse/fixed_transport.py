"""Standalone reproduction of the selected 59 CCX tape (GF(2^12), 0x1053).
Tensor from symmetry_dqi_mixed42_20261115_inputs.json, record 0.
Uses only Python stdlib; emits expanded and pooled gates, not a KMB.
"""
import json,collections,pathlib
N=12; F=1<<N
T=[(a,a,b) for a,b in [(1,1075),(3136,265),(3137,1338),(1087,3647),(3008,1580),(4095,2067),(3821,3916),(3958,3289),(411,917),(859,239),(2806,2391),(2477,2488),(1568,2150),(2048,530),(3616,2676),(2065,1774),(2092,2794),(61,3076),(30,1960),(1032,3553),(1046,2633),(2063,3239),(3108,3394),(1067,485),(1397,2096),(3250,1589),(2503,3589),(2454,1044),(1544,2075),(3998,3087),(3299,1087),(2746,545),(1625,1566),(4017,826),(3850,1992),(187,1266),(210,278),(286,696),(460,942),(3939,148),(3604,1758),(375,1610)]]
P=lambda x:x.bit_count()&1
X=list(range(12));S=list(range(12,24));INV=list(range(24,36));A=list(range(36,47));Y=[X[0]]+A;D=47

def mul(x,y):
    z=0
    while y:
        if y&1:z^=x
        y>>=1;x<<=1
        if x&F:x^=0x1053
    return z

def lin(cols,x):
    z=0
    for i,c in enumerate(cols):
        if x>>i&1:z^=c
    return z

def columns_inv(cols):
    n=len(cols);r=[sum(((c>>i)&1)<<j for j,c in enumerate(cols))|(1<<(n+i)) for i in range(n)]
    for j in range(n):
        k=next(k for k in range(j,n) if r[k]>>j&1);r[j],r[k]=r[k],r[j]
        for k in range(n):
            if k!=j and r[k]>>j&1:r[k]^=r[j]
    return [sum(((r[i]>>(n+j))&1)<<i for i in range(n)) for j in range(n)]

def basis(e,u):
    assert P(e&u)==1
    pivot=(u&-u).bit_length()-1
    return [e]+[(1<<i)^((1<<pivot) if u>>i&1 else 0) for i in range(N) if i!=pivot]

def dual(cols,mask):return sum(P(c&mask)<<j for j,c in enumerate(cols))

def linear_gates(g,qs,cols):
    n=len(qs);rows=[sum(((c>>i)&1)<<j for j,c in enumerate(cols)) for i in range(n)];steps=[]
    for j in range(n):
        k=next(k for k in range(j,n) if rows[k]>>j&1)
        if k!=j:rows[k],rows[j]=rows[j],rows[k];steps.append(('SWAP',qs[j],qs[k]))
        for k in range(n):
            if k!=j and rows[k]>>j&1:rows[k]^=rows[j];steps.append(('CX',qs[j],qs[k]))
    assert rows==[1<<j for j in range(n)];g.extend(reversed(steps))

def parity_gates(qs,mask):
    support=[q for j,q in enumerate(qs) if mask>>j&1];assert support
    return support[0],[('CX',q,support[0]) for q in support[1:]]

def product(g,qs,rs,ys,u,v,w):
    a,ga=parity_gates(qs,u);b,gb=parity_gates(rs,v);c,gc=parity_gates(ys,w)
    gc=[('CX',op[2],op[1]) for op in gc]
    assert len({a,b,c})==3
    assert not ({q for j,q in enumerate(qs) if u>>j&1}&{q for j,q in enumerate(ys) if w>>j&1})
    g.extend(ga+gb+gc+[('CCX',a,b,c)]+gc[::-1]+gb[::-1]+ga[::-1])

def row_factor(rows):
    piv={}
    for r in rows:
        for j,p in sorted(piv.items(),reverse=True):
            if r>>j&1:r^=p
        if r:piv[r.bit_length()-1]=r
    base=list(sorted(piv.items(),reverse=True));masks=[0]*len(base)
    for i,r in enumerate(rows):
        for j,(pos,p) in enumerate(base):
            if r>>pos&1:r^=p;masks[j]|=1<<i
        assert r==0
    return [(a,p) for a,(_,p) in zip(masks,base) if a]

def ccx(g,a,b,c):assert len({a,b,c})==3;g.append(('CCX',a,b,c))

def make(k=0,e=665,ell=3105):
    u,v,w=T[k];ib=basis(e,u);ob=basis(w,ell);ii=columns_inv(ib);oi=columns_inv(ob)
    cm=sum(P(u&mul(1<<j,w))<<j for j in range(N));assert cm
    sb=basis(v&-v,v);si=columns_inv(sb);tb=basis(cm&-cm,cm);ti=columns_inv(tb)
    ts=[(dual(ib,a),dual(sb,b),lin(oi,c)) for a,b,c in T]
    assert ts[k]==(1,1,1) and all(not(a&c&1) for j,(a,b,c) in enumerate(ts) if j!=k)
    g=[];linear_gates(g,X,ii);linear_gates(g,S,si);linear_gates(g,INV,ti)
    for j,(a,b,c) in enumerate(ts):
        if j!=k and a&1:product(g,X,S,Y,a,b,c)
    d=D;z=X[0];vbar=S[0];c=INV[0]
    g.append(('X',vbar));ccx(g,c,d,z);ccx(g,vbar,z,d);g.append(('X',vbar))
    for j,(a,b,c0) in enumerate(ts):
        if j!=k and not a&1:product(g,X,S,Y,a,b,c0)
    g.append(('X',vbar));ccx(g,vbar,z,d);ccx(g,c,d,z)
    gr=[sum(P(u&mul(a,b))<<j for j,b in enumerate(tb)) for a in ob[1:]]
    gg=row_factor(gr);q=X[1];ccx(g,vbar,q,z)
    for a,b in gg:product(g,Y[1:],INV,[q],a,b,1)
    ccx(g,vbar,q,z);ccx(g,vbar,z,d);g.append(('X',vbar))
    for j in range(1,N):g.append(('HMR',X[j],j-1))
    g.append(('CZ_IF',c,z,0));linear_gates(g,S,sb);linear_gates(g,INV,tb);linear_gates(g,Y,ob)
    for a,b,c0 in T:
        q,ga=parity_gates(INV,a);r,gb=parity_gates(Y,b);val=lin(ii,c0);mask=(val>>1)^(val&1)
        if mask:g.extend(ga+gb+[('CZ_MASK',q,r,mask)]+gb[::-1]+ga[::-1])
    for j in range(1,N):g.append(('SWAP',A[j-1],X[j]))
    h=[]
    for o in g:
        if h and h[-1]==o and o[0] in ('X','CX','CCX','SWAP'):h.pop()
        else:h.append(o)
    return h

def expand(g):
    out=[]
    for op,*a in g:
        if op=='CZ_MASK':q,r,m=a;out.extend(('CZ_IF',q,r,j) for j in range(11) if m>>j&1)
        else:out.append((op,*a))
    return out

if __name__=='__main__':
    g=make();h=expand(g);assert sum(o[0]=='CCX' for o in g)==59 and len(g)==2030 and len(h)==2218
    p=pathlib.Path(__file__).with_name('fixed_transport_tape.json');p.write_text(json.dumps({'gates':h,'pooled_gates':g},separators=(',',':'))+'\n')
    print(collections.Counter(o[0] for o in g))
