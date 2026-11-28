"""Fixed physical-coordinate scaling: x->alpha*x, S_i->alpha^(i+1) S_i.
No syndrome-dependent or verifier-dependent routing.
"""
import sys,kickmix as km,hashlib
from pathlib import Path
from rank42 import linmat
from packed_shared import m,E
parent=Path(sys.argv[1]);out=Path(sys.argv[2]);c=km.Circuit.from_file(str(parent));ops=[]
for j in range(70):
    wires=[int(q.id) for q in c.register_data[f'S{j}']];a=E[j+1];cols=tuple(m(a,1<<i) for i in range(12));tape=linmat(cols)
    rows=[1<<i for i in range(12)]
    for op,x,y in tape:
        if op==0:rows[y]^=rows[x]
        else:rows[x],rows[y]=rows[y],rows[x]
    assert rows==[sum(((v>>i)&1)<<k for k,v in enumerate(cols)) for i in range(12)]
    for op,x,y in tape:ops.append((33 if op==0 else 34,wires[x],wires[y]))
assert all([int(b.id) for b in c.register_data[f'E{i}']]==list(range(12*i,12*i+12)) for i in range(4095))
out.write_text('\n'.join(' '.join(map(str,g)) for g in ops)+'\n');print('frame ops',len(ops),'parent',hashlib.file_digest(parent.open('rb'),'sha256').hexdigest())
