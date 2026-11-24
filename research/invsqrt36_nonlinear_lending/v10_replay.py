"""Exact replay of PR45 -> PR50 and PR44 -> PR50 wide. No new search.
Identical instructions executed once by determinism; changed slices replayed independently.
Copy this file to central/global_chart/ in the original PR50 reproduction archive.
"""
from verify_chart import *
from fractions import Fraction
from functools import lru_cache
D=Path(__file__).resolve().parents[2]/'results'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def des(g):return [Op(x[0],tuple(x[1]),x[2],x[3])for x in g]
def depth(ops,paid=False):
 q=[0]*37;c={};st=[];d=0
 for o in ops:
  g=o.raw&127
  guard=st[-1] if st else 0
  if o.raw==129:
   k=max(guard,c.get(o.condition,0));c[o.condition]=k;st.append(k);continue
  if o.raw==1:st.pop();continue
  deps=[guard]+[q[i]for i in o.wires]
  for v in (o.condition,o.measurement):
   if v is not None:deps.append(c.get(v,0))
  k=max(deps)+(int(g in(48,49,50)) if paid else 1)
  for i in o.wires:q[i]=k
  for v in (o.condition,o.measurement):
   if v is not None:c[v]=k
  d=max(d,k)
 assert not st
 return d

def main():
 wide='--wide' in sys.argv
 f=D/('base44.kmb' if wide else 'base45.kmb');g=D/('v9_universal_44_NOT_SUBMIT.kmb' if wide else 'v9_cost_integrated_NOT_SUBMIT.kmb');p=NativeKMB.read(f);n=NativeKMB.read(g)
 assert sha(f)==('88932661d90e2f253a7845d550f657b2c26a062adfa54b05438c64ae8adea0be' if wide else 'f7abc033dbed5477d5685225d9bf5fe262ceb888189ebcc3266ce23f9d15fd6d')
 assert sha(g)==('c1d706a1f0f1533bc02565f9f95e1220f79ab0208577f48c2152089bfe5d5d26' if wide else '67ba0273bc086f25ab91cbb1b287cff7d16aaec2addaa4d59a63a08c6a61fd79')
 assert byte_emit(p,p.ops,37)==f.read_bytes() and byte_emit(n,n.ops,37)==g.read_bytes()
 assert [(k,v)for k,v in p.sections if k==0 or k>9]==[(k,v)for k,v in n.sections if k==0 or k>9]
 O,Nn=p.ops,n.ops;rec=json.loads((D/('v9_universal_44.json' if wide else 'v9_cost_integrated.json')).read_text())
 donors={5867:((16,33,3),[11,12,24,33]),6026:((24,16,3),[10,12,16,33]),7851:((19,7,3),[-1,7,10,13,19,33]),8105:((25,6,34),[3,6,20,33]),8174:((31,20,8),[3,20,33,34]),8233:((9,34,15),[3,8,33,34]),9664:((26,27,30),[33]),13598:((4,0,29),[3,4,19,27])}
 edits={}
 for i,(w,ls) in ({} if wide else donors).items():
  assert O[i]==Op(49,w);t=w[-1];edits[i]=(i+1,[Op(17,(t,))if q<0 else Op(33,(q,t))for q in ls])
 for s in rec['selected']:
  a,z=s['range' if wide else 'base_range'];assert O[a:z]==des(s['old_gates']);edits[a]=(z,des(s['new_gates']))
 print('depth proxy',depth(O),depth(Nn),'paid depth proxy',depth(O,True),depth(Nn,True),flush=True)
 b=BDD(NLEGAL);s=[b.leaf(mask(i,NLEGAL))for i in range(22)]+[b.zero]*15;M=Machine(b,s)
 @lru_cache(None)
 def prob(t):
  if t.var<0:return Fraction(t.value.bit_count(),NLEGAL)
  return (prob(t.low)+prob(t.high))/2
 def cost(A,o):
  if o.raw&127 not in(48,49,50):return 0
  a=b.and_(A.active,A.c.get(o.condition,b.zero))if o.raw&128 else A.active
  r=prob(a);prob.cache_clear();return r
 def fork(A):
  B=Machine(b,A.s,A.c);B.active=A.active;B.stack=A.stack.copy();return B
 def equal(A,B):return A.s==B.s and A.c==B.c and A.stack==B.stack and A.active is B.active and A.p is B.p and A.rot==B.rot
 i=j=shared=0;costs=[Fraction(0),Fraction(0)];t0=time.time();trace=[]
 while i<len(O):
  M.p=b.zero;M.rot=[]
  if i not in edits:
   o=O[i];assert o==Nn[j],(i,j);v=b.variable() if o.raw&127==80 else None;r=cost(M,o);costs[0]+=r;costs[1]+=r;M.step(o,v);i+=1;j+=1;shared+=1
  else:
   z,gates=edits[i];assert Nn[j:j+len(gates)]==gates;A=fork(M);B=fork(M);ev=[]
   for o in O[i:z]:
    v=b.variable()if o.raw&127==80 else None
    if v is not None:ev.append(v)
    costs[0]+=cost(A,o);A.step(o,v)
   it=iter(ev)
   for o in gates:costs[1]+=cost(B,o);B.step(o,next(it)if o.raw&127==80 else None)
   assert next(it,None)is None and equal(A,B),(i,z,j)
   trace.append({'range':[i,z],'new_range':[j,j+len(gates)],'hmr_variables_so_far':b.nvar,'equal':True});print('exact splice',i,z,'seconds',round(time.time()-t0,1),flush=True);M=A;i=z;j+=len(gates)
  if shared and shared%10000==0:print('shared prefix',shared,'seconds',round(time.time()-t0,1),flush=True)
 assert j==len(Nn) and M.s==s and not M.stack
 charts=rec['charts'];assert all(q<36 for a,z,l,h in charts for o in Nn[l:h]for q in o.wires)
 result={'parent_sha256':sha(f),'candidate_sha256':sha(g),'verification':'PASS','legal_inputs':NLEGAL,'hmr_variables':b.nvar,'shared_ops_exactly_identical':shared,'independent_splice_checks':len(trace),'splices':trace,'expected_paid_before':float(costs[0]),'expected_paid_after':float(costs[1]),'expected_paid_before_fraction':str(costs[0]),'expected_paid_after_fraction':str(costs[1]),'static_paid_before':sum(o.raw&127 in(48,49,50)for o in O),'static_paid_after':sum(o.raw&127 in(48,49,50)for o in Nn),'ops_before':len(O),'ops_after':len(Nn),'source_coverage':sum(z-a for a,z,*_ in charts),'peak_used_q':max(q for o in Nn for q in o.wires)+1,'depth_proxy_before':depth(O),'depth_proxy_after':depth(Nn),'paid_depth_proxy_before':depth(O,True),'paid_depth_proxy_after':depth(Nn,True),'seconds':time.time()-t0,'official_verifier':False,'new_search':False}
 (D/('v10_wide_replay.json' if wide else 'v10_full_replay.json')).write_text(json.dumps(result,indent=2));print(result,flush=True)
if __name__=='__main__':main()
