import runpy,sys,json
p=sys.argv[1]
sys.argv=['identify_seam.py',p]
d=runpy.run_path('identify_seam.py')
q=d['q']; m=d['m']; U=d['U']; mat=d['mat']; divide=d['divide']
z=next(c|4096 for c in range(4096) if m(c,c)^c^2048==3169)
u=divide(U,z); v=divide(u,z)
P={}
for i,r in enumerate(q):
    h=1<<i
    while r:
        k=r.bit_length()-1
        if k not in P:
            P[k]=(r,h); break
        t,b=P[k]; r^=t; h^=b
assert len(P)==840
rows=[]
for r0 in mat(u)+mat(v):
    r=r0; h=0
    while r:
        t,b=P[r.bit_length()-1]; r^=t; h^=b
    w=0
    for i in range(900):
        if h>>i&1: w^=q[i]
    assert w==r0
    rows.append(hex(h))
o=dict(kappa=3169,extension_root=z,first_op=d['at'],rank=840,verified_rows=48,rows=rows,weights=[int(h,16).bit_count() for h in rows])
json.dump(o,open('first_node_map.json','w'),indent=2)
print('verified',len(rows),'weights',min(o['weights']),max(o['weights']))
