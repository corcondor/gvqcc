from audit_history import folder,d,vecs,lin,forms,base,insert,rankmod,json,mmap
from collections import Counter

f=(folder/'future.bin').open('rb')
m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
p=json.loads((folder/'futureplan.json').read_text())
keys=list(map(int,(folder/'future_landmarks.txt').read_text().split()))
n=len(keys); assert len(m)==8*n*901*64; ids={a:b for b,a in enumerate(keys)}
def fut(i):
    j=ids[i]; st=901*64
    return [sum(int.from_bytes(m[st*(j+n*k)+64*l:st*(j+n*k)+64*(l+1)],'little')<<(512*k) for k in range(8)) for l in range(900)]
results={}
for s,ss in p.items():
    i=int(s); now=d[s][-1]; curr=vecs(now); active=curr[-1]; curr=[z&active for z in curr]
    a=forms([0]*24+[lin(sum(1<<int(q) for q in l.split(',') if q),curr) for l in base[i*73+1:i*73+25]])
    b={}
    for x in curr:insert(x,b)
    hist=[]
    for j in ss:
        for z in fut(j):insert(z&active,b)
        hist.append((j,rankmod(a,b),len(b)))
    results[s]=hist
    print(i,hist,flush=True)
print('next sampled sites',Counter(v[-1][1] for v in results.values()))
(folder/'future_receipt.json').write_text(json.dumps(results,indent=2))
