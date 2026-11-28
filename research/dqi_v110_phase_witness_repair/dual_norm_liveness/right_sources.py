from audit_history import folder,d,vecs,lin,forms,base,insert,reduce,rankmod,json
from collections import Counter
import bisect
report={}
def build(xs):
    z={}
    for x in xs: insert(x,z)
    return z
for k,ph in d.items():
    i=int(k);v=vecs(ph[-1]);act=v[-1];v=[z&act for z in v]
    bb=[sum(1<<int(q) for q in l.split(',') if q) for l in base[i*73+25:i*73+49]]
    cb=[lin(f,v) for f in bb]
    nb=forms([0]*24+cb)
    nb_b={}
    for z in nb:insert(z,nb_b)
    assert len(nb_b)==12
    af=dict(nb_b)
    for z in cb+[act]:insert(z,af)
    # The norm is allowed an affine change of B coordinates.
    qd=[i for i,z in enumerate(v[:-1]) if z and not reduce(z,nb_b)]
    qa=[i for i,z in enumerate(v[:-1]) if z and not reduce(z,af)]
    l={}
    for z in cb+[act]+[v[j] for j in qa]:insert(z,l)
    ra=12-rankmod(nb,l)
    direct=12-rankmod(nb,build(v[j] for j in qd))
    report[k]=dict(direct_norm_only_rank=direct,single_wire_mod_affine_rank=ra,raw_wires=qd,affine_wires=qa)
print('direct B norm ranks',Counter(r['direct_norm_only_rank'] for r in report.values()))
print('single physical B norm wires mod B-affine',Counter(r['single_wire_mod_affine_rank'] for r in report.values()))
(folder/'right_sources.json').write_text(json.dumps(report,indent=2))
