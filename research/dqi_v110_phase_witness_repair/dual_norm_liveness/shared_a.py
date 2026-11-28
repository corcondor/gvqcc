from audit_history import folder,d,vecs,lin,forms,base,insert,rankmod,json
from collections import Counter
from itertools import combinations

A={}
for k,history in d.items():
    i=int(k); now=vecs(history[-1]); active=now[-1]
    assert active.bit_count()==4096
    q=now[:-1]
    cols=[sum(1<<int(v) for v in l.split(',') if v) for l in base[i*73+1:i*73+25]]
    na=forms([0]*24+[lin(v,q) for v in cols])
    basis={}
    for v in na:insert(v,basis)
    assert len(basis)==12
    A[i]=basis
stats=Counter();hits=[]
for i,j in combinations(A,2):
    shared=12-rankmod(A[i].values(),A[j])
    stats[shared]+=1
    if shared:hits.append([i,j,shared])
allrank=rankmod((v for b in A.values() for v in b.values()),{})
print('combined rank',allrank,'of',12*len(A))
print('A norm subspace pair overlap',stats)
print('overlaps',hits[:50])
(folder/'shared_a_receipt.json').write_text(json.dumps({'combined_rank':allrank,'histogram':stats,'nonzero_intersections':hits},indent=2))
