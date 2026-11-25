"""Dirty-ancilla finite common-factor synthesis; exact gates, no extra slot.
Reference core from V51 repair.py. Import Op from the PR116 native KMB engine.
"""
from native_kmb import Op
def mcx(cs,t):
    cs=list(cs);assert t not in cs and len(cs)==len(set(cs)) and all(0<=q<36 for q in cs+[t]);n=len(cs)
    if n==0:return [Op(17,(t,))]
    if n==1:return [Op(33,(cs[0],t))]
    if n==2:return [Op(49,(*cs,t))]
    spare=[q for q in range(36)if q!=t and q not in cs]
    if len(spare)>=n-2:
        a=spare[:n-2];l=[Op(49,(cs[0],cs[1],a[0]))]+[Op(49,(cs[i+1],a[i-1],a[i]))for i in range(1,n-2)];g=[Op(49,(cs[-1],a[-1],t))]
        return l+g+l[::-1]+l[1:]+g+l[1:][::-1]
    assert spare;d=spare[0];k=(n+1)//2;u=mcx(cs[:k],d);v=mcx(cs[k:]+[d],t)
    return u+v+u+v
def emit_cube(lits,t):
    neg=[Op(17,(q,))for q,b in lits if not b]
    return neg+mcx([q for q,b in lits],t)+neg[::-1]
def paid(o):return sum(p.raw==49 for p in o)
def group_emit(group,t):
    S=[set(c['literals'])for c in group];common=set.intersection(*S);used={q for s in S for q,b in s};sp=[q for q in range(36)if q!=t and q not in used]
    direct=sum((emit_cube(sorted(s),t)for s in S),[])
    if not common or not sp:return direct,False
    d=sp[0];a=emit_cube(sorted(common),d);b=sum((emit_cube(sorted(s-common)+[(d,1)],t)for s in S),[]);new=a+b+a+b
    return (new,True)if (paid(new),len(new))<(paid(direct),len(direct))else(direct,False)
