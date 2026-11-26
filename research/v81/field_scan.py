"""Exact GF(2^12) additive subspace scan basis generator."""
from collections import Counter
from pathlib import Path
import json
MOD=0x1053; F=4096; ORDER=F-1; N=35
EXP=[]; LOG=[0]*F; x=1
for i in range(ORDER):
    assert x not in EXP
    EXP.append(x); LOG[x]=i; x<<=1
    if x&F: x^=MOD
assert x==1; EXP*=2

def mul(a,b): return EXP[LOG[a]+LOG[b]] if a and b else 0
def power(a,k): return EXP[(LOG[a]*k)%ORDER] if a else int(k==0)
def inv(a): assert a; return EXP[ORDER-LOG[a]]
def xorall(v):
    out=0
    for a in v:out^=a
    return out

def addmul(A,B,c):
    A=A[:]+[0]*max(0,len(B)-len(A))
    for j,b in enumerate(B):A[j]^=mul(c,b)
    while len(A)>1 and not A[-1]:A.pop()
    return A

def prod(a,b):
    c=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):c[i+j]^=mul(x,y)
    return c

def evalpoly(a,x):
    y=0
    for c in reversed(a):y=mul(y,x)^c
    return y

def trace(a):
    return xorall(power(a,1<<j) for j in range(12))

def coords(basis):
    c=[0]*F; seen={0}
    for i,b in enumerate(basis):
        assert b not in seen
        for x in list(seen):c[x^b]=c[x]^(1<<i)
        seen|={x^b for x in seen}
    assert len(seen)==F
    return c

def independent_prefix(basis):
    span={0}; out=[]
    for x in basis:
        if x not in span:out.append(x);span|={a^x for a in span}
        if len(out)==12:return out
    return out

def towers():
    divisors=[1,2,3,4,6,12]
    def rec(d):
        if d==12:return [[12]]
        return [[d]+s for e in divisors if e>d and e%d==0 for s in rec(e)]
    out=[]
    for chain in rec(1):
        basis=[1]
        for d,e in zip(chain,chain[1:]):
            g=EXP[ORDER//((1<<e)-1)]
            basis=[mul(b,power(g,k)) for k in range(e//d) for b in basis]
        assert len(independent_prefix(basis))==12
        out.append(("tower_"+"_".join(map(str,chain)),basis))
    return out

def subspace(beta):
    T=[0,1]; S=[]; tab=[]
    for b in beta:
        t=evalpoly(T,b);assert t
        s=[mul(c,inv(t)) for c in T]; S.append(s)
        cols=[evalpoly(s,1<<i) for i in range(12)]; row=[0]*F
        for i in range(1,F):k=(i&-i).bit_length()-1;row[i]=row[i^(1<<k)]^cols[k]
        tab.append(row)
        tt=[0]*(2*len(T)-1)
        for i,c in enumerate(T):tt[2*i]=mul(c,c)
        T=addmul(tt,T,t)
    span=[0]
    for j,b in enumerate(beta):
        assert all(tab[j][x]==0 and tab[j][x^b]==1 for x in span)
        span += [x^b for x in span]
    B=[[1]]
    for i in range(1,N+1):
        j=(i&-i).bit_length()-1;B.append(prod(B[i^(1<<j)],S[j]));assert len(B[i])==i+1 and B[i][-1]
    return B,tab

def linear_columns(s,basis,coordinate):return [coordinate[mul(s,b)] for b in basis]

def plan():
    polynomial=[1<<i for i in range(12)]
    normal=[]
    for a in range(1,F):
        b=[power(a,1<<i) for i in range(12)]
        if len(independent_prefix(b))==12:normal=b;break
    candidates=[('polynomial',polynomial),('normal',normal)]+towers()
    fields={d:[a for a in range(F) if power(a,1<<d)==a] for d in [1,2,3,4,6,12]}
    assert all(len(a)==1<<d for d,a in fields.items())
    dual=[0]*F; seen=set()
    for a in range(F):
        t=sum(trace(mul(a,1<<j))<<j for j in range(12));assert t not in seen;seen.add(t);dual[t]=a
    matcost={}; coordinate={}
    for name,b in candidates:
        c=coords(b);coordinate[name]=c
        matcost[name]=[sum(v.bit_count() for v in linear_columns(s,b,c)) for s in range(F)]
    rows=[]; best=None
    for tree,beta in candidates:
        B,tab=subspace(beta);counts=Counter();constants=Counter()
        def dfs(k,a):
            if k==0:return
            h=1<<(k-1);highP=max(0,min(h,N+1-h));highV=max(0,min(h,N-h));nvar=highP+highV-int(h<=N<h*2)
            for s in (tab[k-1][a],1,tab[k-1][a]^1):
                if s:counts[s]+=nvar
                if h<=N<h*2 and s:constants[mul(s,inv(B[N][-1]))]+=1
            dfs(k-1,a);dfs(k-1,a^beta[k-1])
        dfs(12,0)
        for physical,basis in candidates:
            score=sum(matcost[physical][s]*n for s,n in counts.items())+sum(coordinate[physical][s].bit_count()*n for s,n in constants.items())
            score+=(F-1)*sum(v.bit_count() for v in basis) if physical!='polynomial' else 0
            rows.append(dict(tree=tree,physical=physical,estimated_linear_ops=score))
            if best is None or score<best[0]:best=(score,tree,physical,beta,basis,B,tab)
    score,tree,physical,beta,basis,B,tab=best
    print('candidates',len(candidates),'pairings',len(rows),'winner',tree,physical,score)
    print('subfields',[(d,len(v)) for d,v in fields.items()]);print('beta',beta,'basis',basis)
    out={'modulus':MOD,'subfield_cardinalities':{d:len(v) for d,v in fields.items()},'chains':[n for n,b in towers()], 'tree_basis_name':tree,'physical_basis_name':physical,'beta':beta,'basis':basis,'B':B,'subspace_values':tab,'scores':sorted(rows,key=lambda x:x['estimated_linear_ops']),'trace_dual':dual}
    Path('plan.json').write_text(json.dumps(out,separators=(',',':')))
    with open('plan.txt','w') as f:
        f.write(' '.join(map(str,beta))+'\n');f.write(' '.join(map(str,basis))+'\n')
        for row in B:f.write(' '.join(map(str,row))+'\n')
        for row in tab:f.write(' '.join(map(str,row))+'\n')
    return out
if __name__=='__main__':plan()
