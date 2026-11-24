"""Merge PR41 exact multi-HMR charts with PR40 nested union; reject overlaps."""
from verify_portfolio import *
base=pickle.load(open(P/'portfolio_v7nested_path_unmapped.pkl','rb'))
new=pickle.load(open(P/'v7_exact_edges.pkl','rb'));sel={};blocked=[]
for a,e in sorted(new.items()):
 z=e[2];hits=[x for x in base if x[1]<z and x[2]>a]
 if not hits or any(x[0]!='fallback'for x in hits):blocked.append([a,z,[(x[0],x[1],x[2])for x in hits]]);continue
 sel[a]=e
out=[];skip=-1
for e in base:
 a,z=e[1:3]
 if z<=skip:continue
 if e[0]!='fallback':assert a>=skip;out.append(e);continue
 k=max(a,skip)
 while k<z:
  if k in sel:v=sel[k];out.append(v);skip=v[2];k=skip;continue
  j=min([z]+[u for u in sel if k<u<z]);out.append(('fallback',k,j,None,None,None,None,OPS[k:j],{}));k=j
assert all(e[2]==g[1]for e,g in zip(out,out[1:]))and out[0][1]==0 and out[-1][2]==N
rec={'accepted':[(e[1],e[2],e[8]['paid_delta'])for e in sel.values()],'overlap_excluded':blocked,'covered':sum(e[2]-e[1]for e in out if e[0]!='fallback')}
print(rec,flush=True);pickle.dump(out,open(P/'portfolio_v7unionquotient_path_unmapped.pkl','wb'));(P/'v7_unionquotient_plan.json').write_text(json.dumps(rec,indent=2))
