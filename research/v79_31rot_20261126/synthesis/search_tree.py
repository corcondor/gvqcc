"""Joint factor orientation / resident-space search with persistent local flags.
Every rank-two choice is GL(2,2)-equivalent; all basis frame changes are exact.
"""
import sys,os,json,time,hashlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'donor'))
from treewidth import *
from quotient_hubs import quotient_plan

class SearchTree(TreeMulti):
 def __init__(self,Q,scale,S,policy,seed,penalty,policies=6,tries=2,persistent=True,hubs=True):
  super().__init__(Q,scale,S,policy,seed,penalty);self.policies=policies;self.tries=tries;self.persistent=persistent;self.hubs=hubs
 def prepare(self,z,nfree):
  key=(id(z),nfree)
  if key in self._leaf:return self._leaf[key]
  if not z.data or not nfree:return super().prepare(z,nfree)
  opts=[];modes=[False,True] if self.policy=='auto' else [self.policy=='clean']
  if nfree==1:modes=[False]
  for clean in modes:
   cap=nfree-int(clean)
   for pol in range(self.policies):
    base,sub=groups_policy(z.data,self.scale,pol,z.p+37*pol+self.seed);keys=sorted(sub)
    if not keys:opts.append((0,0,0,clean,base,sub,[]));continue
    cost2=sum(1 if clean else 2*len(co) for Z in sub.values() for k,co in Z.items() if k is not None)
    for keep in sorted({0,min(2,cap-1),max(0,cap-2),cap//2}):
     for sd in range(self.tries):
      _,p=batches(keys,cap,self.seed+sd,keep);p=order_plan(p,self.seed+sd);cost=plan_rank_cost(p)
      weight=sum(v.bit_count() for B,_ in p for v in B)
      opts.append((cost+cost2,cost,weight,clean,base,sub,p))
    if self.hubs:
     hub=quotient_plan(keys,cap,self.seed)
     cost=plan_rank_cost(hub);weight=sum(v.bit_count() for B,_ in hub for v in B)
     opts.append((cost+cost2,cost,weight,clean,base,sub,hub))
  chosen=min(opts,key=lambda a:a[:3]);ans=(chosen[0],('basis',chosen));self._leaf[key]=ans;return ans
 def leaf_basis(self,z,f,free):
  if not z.data:return
  _,chosen=self.prepare(z,len(free))
  if chosen[0]=='expand':return super().leaf_basis(z,f,free)
  paid,first,_,clean,base,sub,plan=chosen[1];d,p=z.d,z.p
  self.local_sweep(f,base,d,p,[],[])
  if not plan:return
  pool=free[:-1] if clean else free;second=free[-1] if clean else None
  A=[];wires=[];actual=0
  for B,K in plan:
   I=intersection(A,B)
   if A:
    X=independent(I+A)
    for a,b in basis_xors(A,X):self.op(33,wires[a],wires[b])
    for v,t in zip(X[len(I):],wires[len(I):]):self.condition(f,v,-1,t,True)
    wires=wires[:len(I)]
   A=independent(I+B)
   for v in A[len(I):]:
    t=next(t for t in pool if t not in wires);self.condition(f,v,-1,t);wires.append(t);actual+=1
   remaining=[(v,h) for v,h,_ in K]
   while remaining:
    tab=pivot_basis(A)
    if self.persistent:
     v,h=min(remaining,key=lambda vh:(reduce(vh[0],tab)[1].bit_count(),vh))
    else:v,h=remaining[0]
    remaining.remove((v,h));r,c=reduce(v,tab);assert not r
    js=list(bits(c))
    if self.persistent:
     # Choose an invertible pivot whose updated resident frame best covers upcoming flags.
     def merit(pv):
      C=A[:];C[pv]=v;t=pivot_basis(C)
      return sum(reduce(w,t)[1].bit_count() for w,_ in remaining),pv
     pivot=min(js,key=merit);others=[j for j in js if j!=pivot]
    else:pivot=js[-1];others=js[:-1]
    t=wires[pivot]
    for j in others:self.op(33,wires[j],t)
    if h==1:self.op(33,f,t)
    Z=sub[v,h];self.local_sweep(t,Z.get(None,[]),d,p,[v],[h])
    for (u,j),co in sorted((s,c) for s,c in Z.items() if s is not None):
     if clean:
      self.condition(t,u,j,second);self.local_sweep(second,co,d,p,[v,u],[h,j]);self.condition(t,u,j,second,True)
     else:self.c1=t;self.second_echo(v,h,u,j,co,d,p)
    if h==1:self.op(33,f,t)
    if self.persistent:A[pivot]=v
    else:
     for j in others[::-1]:self.op(33,wires[j],t)
  for v,t in zip(A,wires):self.condition(f,v,-1,t,True)
  assert actual==first,(actual,first)
  self.stats['resident_basis_products']+=actual;self.stats['estimated_leaf_paid']+=paid
  self.stats['leaf_first_groups']+=len(sub);self.stats['leaf_cache_batches']+=len(plan)

def run(Q,stem,seed=0,policies=6,tries=2,persistent=True,hubs=True):
 start=time.time();P=json.load(open('recip.plan.json'));root=make_nodes(P,Q)
 e=SearchTree(Q,MOD//P['scale'],set(),'auto',seed,8,policies,tries,persistent,hubs)
 proxy=sum(e.split_cost(c)[0] for c in root.ch.values())
 for c in root.ch.values():e.split_tree(c)
 e.local_sweep(None,list(e.plain.items()),0,0,[],[]);best,n=cancel(e.ops)
 p=Path(stem+'.kmb');write_hmr(NativeKMB.read('reference_header.kmb'),p,best,e.angles,Q,True)
 K=NativeKMB.read(p);counts=Counter(o.raw for o in K.ops)
 r=dict(width=Q,ops=len(K.ops),ccx=counts[49],cx=counts[33],rotations=len(e.angles),generic=sum(a%(1<<125)!=0 for a in e.angles),hmr=counts[80],proxy=proxy,seed=seed,policies=policies,tries=tries,persistent=persistent,hubs=hubs,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),seconds=time.time()-start,**e.stats)
 Path(stem+'.json').write_text(json.dumps(dict(stats=r,tags=e.tags,angles=[str(x) for x in e.angles]),separators=(',',':')));print(r,flush=True)
if __name__=='__main__':run(int(sys.argv[1]),sys.argv[2],*map(int,sys.argv[3:]))
