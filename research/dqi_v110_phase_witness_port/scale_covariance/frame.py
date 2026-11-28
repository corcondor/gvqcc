"""Verified F2 row elimination for the physical #291 scale wrapper."""
import sys
import kickmix as km
import paired_mask as P

c=km.Circuit.from_file(sys.argv[1])
ops=[]
for j in range(70):
    w=[int(q.id) for q in c.register_data[f'S{j}']]
    col=[P.mul(int(P.EXP[j+1]),1<<k) for k in range(12)]
    M=[sum(((v>>i)&1)<<k for k,v in enumerate(col)) for i in range(12)]
    a=M[:];t=[]
    for k in range(12):
        l=next(i for i in range(k,12) if a[i]>>k&1)
        if l!=k:
            a[k],a[l]=a[l],a[k]
            t.append((34,w[k],w[l]))
        for i in range(12):
            if i!=k and a[i]>>k&1:a[i]^=a[k];t.append((33,w[k],w[i]))
    assert a==[1<<i for i in range(12)]
    ops.extend(t[::-1])
for j in range(4095):
    assert [int(q.id) for q in c.register_data[f'E{j}']]==list(range(12*j,12*j+12))
open(sys.argv[2],'w').write(''.join('%d %d %d\n'%t for t in ops))
print('frame',len(ops))
