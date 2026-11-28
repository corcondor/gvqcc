import bisect
from pathlib import Path
from collections import Counter
from audit_history import (folder,read,d,vecs,insert,forms,lin,rankmod,base,json,mmap)

f=(folder/'events.bin').open('rb')
m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
ids=[int(l.split()[0]) for l in (folder/'events.tsv').read_text().splitlines()]
spans=json.loads((folder/'intervals.json').read_text())
n=len(ids)
assert len(m)==8*n*64,(len(m),8*n*64)
def event_vec(j):
    return sum(int.from_bytes(m[64*(j+n*k):64*(j+n*k+1)],'little')<<(512*k) for k in range(8))
results={}
for s,ss in spans.items():
    i=int(s); now=d[s][-1]; curr=vecs(now); active=curr[-1]; curr=[z&active for z in curr]
    a=forms([0]*24+[lin(sum(1<<int(q) for q in l.split(',') if q),curr) for l in base[i*73+1:i*73+25]])
    assert rankmod(a,{})==12
    basis={}
    for z in curr: insert(z,basis)
    marks=[]
    for lo,hi in ss:
        for z in vecs(lo)[:-1]: insert(z&active,basis)
        j,k=bisect.bisect_left(ids,lo),bisect.bisect_left(ids,hi)
        for e in range(j,k): insert(event_vec(e)&active,basis)
        marks.append(dict(lo=lo,hi=hi,captured_writes=k-j))
    res=dict(A_defect=rankmod(a,basis),history_rank=len(basis),active=active.bit_count(),spans=marks)
    results[s]=res
    print(s,res,flush=True)
print('event-complete trace',Counter(r['A_defect'] for r in results.values()))
(folder/'events_receipt.json').write_text(json.dumps(results,indent=2))
