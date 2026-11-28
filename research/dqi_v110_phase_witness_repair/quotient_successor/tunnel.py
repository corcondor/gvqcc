from collections import Counter
from pathlib import Path
p=Path(__file__).parent
rows=lambda s:[list(map(int,l.split())) for l in (p/s).read_text().splitlines()]
a=rows('seam.tsv')[:100]+rows('after.tsv')[:537]
a=[r for r in a if r[0]<=41425803]
local=[3,16,19,46,68,80,104,141,258,294,340,457,631,752]
def step(d,o,a,b):
    if o==33 and (d>>a&1): return d^(1<<b)
    if o==34 and (((d>>a)^(d>>b))&1): return d^(1<<a)^(1<<b)
    return d
stats=Counter(); clean=[]; deepest=(-1,None)
for bits in range(8192):
    d=sum(((bits>>i)&1)<<q for i,q in enumerate(q for q in local if q!=340)) | (1<<340)
    d0=d
    phase=[]
    for i,o,x,y,t,z,c in a:
        if o==49 and ((d>>x|d>>y)&1):
            stats[i]+=1
            if i>deepest[0]: deepest=(i,[q for q in local if d0>>q&1])
            break
        if (o&127) in {16,32,48}:
            if any(d>>q&1 for q in ([x] if (o&127)==16 else [x,y] if (o&127)==32 else [x,y,t])): phase.append(i)
        if o==80:
            if i==41425267 and not (d>>x&1):
                stats['first_hmr_pivot_zero']+=1
                break
            if d>>x&1: phase.append(i)
            d &= ~(1<<x)
        else: d=step(d,o,x,y)
    else:
        clean.append((sum(((d0>>q)&1)<<j for j,q in enumerate(local)), d.bit_count(), phase))
print('failure histogram',dict(sorted(stats.items(),key=lambda x:str(x[0]))))
print('deepest',deepest,'candidates after second HMR',len(clean),'terminal no delta',sum(k[1]==0 for k in clean))
print('best survivors',sorted(clean,key=lambda k:(k[1],len(k[2])))[:5])

# Elimination certificate vs assuming only sample-wise failure:
# symbolic rows represent the differential in the 14 entry directions.
m = {q: 1<<j for j,q in enumerate(local)}
constraints=[]
for i,o,x,y,t,z,c in a:
    if o==33: m[y]=m.get(y,0)^m.get(x,0)
    if o==34: m[x],m[y]=m.get(y,0),m.get(x,0)
    if o==49:
        for side,q in enumerate((x,y)):
            constraints.append((m.get(q,0),(i,side,q)))
    if o==80: m[x]=0
basis={}
for orig,(r,desc) in enumerate(constraints):
    provenance=1<<orig
    while r:
        j=r.bit_length()-1
        if j not in basis:
            basis[j]=r,provenance
            break
        v,k=basis[j]
        r^=v
        provenance^=k
    r=1<<10; certificate=0
    while r and r.bit_length()-1 in basis:
        v,k=basis[r.bit_length()-1]
        r^=v; certificate^=k
    if not r:
        obligations=[(row,desc) for j,(row,desc) in enumerate(constraints) if certificate>>j&1]
        print('entry q340 delta forced zero, certificate',obligations)
        break
