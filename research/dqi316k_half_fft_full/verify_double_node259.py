from pathlib import Path
import sys
# Reuse the exact #259 native runner and official ABI; independent new inputs.
s=Path('verify_fusion.py').read_text()
s=s[:s.index('for name,S,M,F in forced():')]
exec(compile(s,'verify_fusion.py','exec'))
out=P.with_suffix('.double_node.json')
rng=np.random.default_rng(25920261128)
U=C.mul(C.G,C.G)
for typ in ('double_node','two_distinct_nodes'):
 S=[];M=[];F=[]
 for i in range(136):
  w=(5,9,17,18,30,35,35,35)[i%8]
  ix=rng.choice(4095,w,replace=False);xs=[int(table.antilog[j]) for j in ix];D=[1]
  for x in xs:D=C.mul(D,[x,1])
  dd=[D[j] if j%2 else 0 for j in range(1,len(D))]
  g=[C.ks[i%17],1,1];h=g if typ=='double_node' else [C.ks[(i+1)%17],1,1]
  N=C.mul(g,h)
  vals=[C.m(C.evalp(N,x),C.inv(C.m(C.m(x,C.evalp(U,x)),C.evalp(dd,x)))) for x in xs]
  assert all(vals)
  for mode in ('zero','onehot','dense'):
   mask=np.zeros(4095,np.int64)
   if mode=='dense':mask=rng.integers(0,4096,4095,dtype=np.int64)
   if mode=='onehot':mask[ix[0]]=1<<(i%12)
   S.append(C.moment(xs,vals));M.append(mask);F.append(bool(sum((int(mask[j])&v).bit_count() for j,v in zip(ix,vals))%2))
 run(typ,np.asarray(S,np.int64),np.asarray(M,np.int64),np.asarray(F,bool),seed=25931)
out=P.with_suffix('.double_node.json');out.write_text(json.dumps(res,indent=2))
print('DOUBLE NODE RECEIPT',json.dumps(res),flush=True)

