import json,mmap,sys
from pathlib import Path
from collections import Counter
folder=Path(__file__).parent
src=Path(sys.argv[1]) if len(sys.argv)>1 else folder
read=lambda f:(src/f).read_text()
d=json.loads((folder/'plan.json').read_text())
keys=list(map(int,(folder/'landmarks.txt').read_text().split()))
n=len(keys); index={k:j for j,k in enumerate(keys)}
capture=(folder/'history.bin').open('rb')
mm=mmap.mmap(capture.fileno(),0,access=mmap.ACCESS_READ)
assert len(mm)==8*n*901*64,(len(mm),8*n*901*64)
base=read('extracted2.tsv.basis').splitlines()
pairs=[(i,j) for i in range(48) for j in range(i+1,48)]
pair_idx={p:k for k,p in enumerate(pairs)}
x=json.loads(read('norm_relation_receipt.json'))['norm'][0]
def reduce(v,b):
    while v:
        pivot=v.bit_length()-1
        if pivot not in b: break
        v^=b[pivot]
    return v
def insert(v,b):
    v=reduce(v,b)
    if v: b[v.bit_length()-1]=v
def vecs(i):
    j=index[i]; st=901*64
    return [sum(int.from_bytes(mm[st*(j+n*k)+64*l:st*(j+n*k)+64*(l+1)],'little')<<(512*k) for k in range(8)) for l in range(901)]
def lin(v,x):
    out=0
    while v:
        p=v&-v;v^=p;out^=x[p.bit_length()-1]
    return out
def forms(c):
    mon=[c[i]&c[j] for i,j in pairs if i>=24]
    mon2={pair_idx[i,j]:a for (i,j),a in zip([(i,j) for i,j in pairs if i>=24],mon)}
    v=[]
    for k in range(24):
        terms=int(x['forms'][k],16)
        v.append(lin(terms,mon2)^lin(sum((a>>k&1)<<j for j,a in enumerate(x['linear'])),c[24:]))
    return v

def rankmod(rows,b):
    add=dict(b)
    for row in rows: insert(row,add)
    return len(add)-len(b)

if __name__=="__main__":
    results={}
    for k,history in d.items():
        i=int(k);curr=vecs(history[-1]);active=curr[-1]
        assert active.bit_count()>1800,(i,active.bit_count())
        curr=[v&active for v in curr]
        currbasis={}
        for v in curr: insert(v,currbasis)
        basisA=[sum(1<<int(q) for q in l.split(',') if q) for l in base[i*73+1:i*73+25]]
        basisB=[sum(1<<int(q) for q in l.split(',') if q) for l in base[i*73+25:i*73+49]]
        a=forms([0]*24+[lin(v,curr) for v in basisA])
        b=forms([0]*24+[lin(v,curr) for v in basisB])
        assert rankmod(a,{})==12 and rankmod(b,{})==12
        basepair=[rankmod(a,currbasis),rankmod(b,currbasis)]
        histbasis=dict(currbasis); out=[]
        for mark in reversed(history[:-1]):
            y=vecs(mark)
            # Even if these wires cannot all be retained without additional width,
            # using their full span is a necessary-condition screen.
            for v in y[:-1]: insert(v&active,histbasis)
            out.append((mark,rankmod(a,histbasis),rankmod(b,histbasis),len(histbasis)))
        results[k]={'active':active.bit_count(),'entry_A_B_defect':basepair,'adding_older_states':out}
        print(i,active.bit_count(),basepair,out[-1],flush=True)
    print('entry',Counter(tuple(r['entry_A_B_defect']) for r in results.values()))
    print('after combined history',Counter(tuple(r['adding_older_states'][-1][1:3]) for r in results.values()))
    (folder/'history_receipt.json').write_text(json.dumps(results,indent=2))
