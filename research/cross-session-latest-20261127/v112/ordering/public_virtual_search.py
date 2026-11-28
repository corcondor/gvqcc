"""V112 extension: include clean epochs of public quantum inputs. Independent exhaustive
value/phase checking over local dirty inputs and both private HMR results.
No claim of full width or official PASS. Use only unconditional clean lifetimes.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'vendor'))
from schedule import *
from virtual_base import compile_epoch,cost
import itertools,bisect

def exhaustive(old,new,z,m):
 if sum(o.raw&127==80 for o in old)!=1 or any(o.raw&127 in (1,18,19,64,65,66) for o in old+new):raise ValueError('other instruments')
 if any(o.condition is not None and o.condition!=m for o in old+new):raise ValueError('external guard')
 if any(o.measurement is not None and o.measurement!=m for o in old+new):raise ValueError('external measurement')
 ws=sorted({q for o in old+new for q in o.wires}-{z});k=len(ws)
 if k>16:raise ValueError('too many local inputs')
 N=1<<k;allbits=(1<<N)-1
 def bits(i):
  a=(1<<(1<<i))-1;step=1<<(i+1);return ((allbits//((1<<step)-1))*a)<<(1<<i)
 ini={q:bits(j) for j,q in enumerate(ws)};ini[z]=0
 def run(ops,b):
  q=ini.copy();ph=0
  for o in ops:
   if o.condition is not None and b==0:continue
   t=o.raw&127;w=o.wires
   if t==17:q[w[0]]^=allbits
   elif t==33:q[w[1]]^=q[w[0]]
   elif t==49:q[w[2]]^=q[w[0]]&q[w[1]]
   elif t==34:q[w[0]],q[w[1]]=q[w[1]],q[w[0]]
   elif t==50:d=q[w[0]]&(q[w[1]]^q[w[2]]);q[w[1]]^=d;q[w[2]]^=d
   elif t==80:ph^=q[w[0]] if b else 0;q[w[0]]=0
   elif t in (0,16,32,48):
    f=allbits
    for j in w:f&=q[j]
    ph^=f
   else:raise ValueError('unsupported op')
  return q,ph
 for b in (0,1):
  if run(old,b)!=run(new,b):raise ValueError('counterexample')
 return 2*N

def run(p,out):
 c=NativeKMB.read(p);orig=c.ops;oldQ=c.header[1];pins=pub(c);d=0;dep=[]
 for g in orig:dep.append(d);d+=(g.raw==129)-(g.raw==1)
 # Full-width operation markers (conservative HMR interval model).
 data=lifetimes(c);_,E,ends,uses=data;live=set();pressure_mask=[]
 for i,u in enumerate(uses):
  live.update(e for e in u if e>=0);pressure_mask.append(int(len(live)+len(pins)==oldQ))
  for e in u:
   if e>=0 and ends[e]==i:live.remove(e)
 prefix=list(itertools.accumulate([0]+pressure_mask));candidates=[];fail=collections.Counter()
 for z in range(oldQ):
  known=z not in pins;start=0
  for end,o in enumerate(orig):
   if o.raw&127!=80 or o.wires!=(z,):continue
   if o.raw!=80 or dep[end]:known=False;start=end+1;continue
   if not known:known=True;start=end+1;continue
   s=next((i for i in range(start,end) if z in orig[i].wires),end);start=end+1
   if dep[s] or end-s>100:fail['scope/length']+=1;continue
   try:
    stop,rep,rec,f=compile_epoch(orig,s,end,oldQ,z)
    if not all(dep[i]==0 for i in range(s,stop)):raise ValueError('scope')
    delta=cost(rep)-cost(orig[s:stop]);cover=prefix[end+1]-prefix[s];cases=exhaustive(orig[s:stop],rep,z,o.measurement)
    if cover>0:candidates.append(dict(z=z,start=s,end=end,stop=stop,delta=delta,cover=cover,cases=cases,old_ops=stop-s,new_ops=len(rep),rep=rep,method='virtual_anf'))
   except ValueError as e:fail[str(e)]+=1
 # Incorporate V109 borrowed-factor identity, rebind to exact V110 bytes.
 for s in range(len(orig)-17):
  z=36;x=Op(17,(z,));cx=lambda u,v:Op(33,(u,v));cc=lambda u,v,w:Op(49,(u,v,w))
  if orig[s:s+10]!=[x,cx(10,z),cx(24,z),cx(11,10),cx(11,21),cc(10,21,z),cx(11,21),cx(11,10),cx(21,1),cc(24,z,1)]:continue
  h=orig[s+10];m=h.measurement;stop=s+18
  expected=[h,Op(128,(),condition=m),Op(144,(10,),condition=m),Op(144,(24,),condition=m),Op(144,(11,),condition=m),Op(160,(10,21),condition=m),Op(160,(10,11),condition=m),Op(160,(21,11),condition=m)]
  assert h.raw==80 and h.wires==(36,) and orig[s+10:stop]==expected
  prev=next(o for o in orig[:s][::-1] if z in o.wires);assert prev.raw==80 and prev.wires==(z,);pi=max(i for i,o in enumerate(orig[:s]) if z in o.wires);assert dep[pi]==0 and all(dep[i]==0 for i in range(s,stop));
  for o in orig[stop:]:
   assert o.condition!=m
   if o.measurement==m:assert o.raw in (80,64,65);break
  rep=[cx(21,1),cx(11,10),cx(11,21),cc(10,21,11),cx(10,11),cc(24,11,1),cx(10,11),cc(10,21,11),cx(11,21),cx(11,10)]
  cases=exhaustive(orig[s:stop],rep,z,m);candidates.append(dict(z=z,start=s,end=s+10,stop=stop,delta=1,cover=prefix[s+11]-prefix[s],cases=cases,old_ops=18,new_ops=10,rep=rep,method='borrowed_factor'))
 print('candidate count',len(candidates),'failures',fail,flush=True)
 # Resource-bounded weighted interval selection. Conservative peak points covered
 # are an optimistic ranking; recompute full candidate pressure afterwards.
 candidates.sort(key=lambda a:a['stop']);stops=[a['stop'] for a in candidates];budget=40;DP=[[(0,0,[]) for _ in range(budget+1)]]
 for j,a in enumerate(candidates):
  last=bisect.bisect_right(stops,a['start'],0,j);row=[];delta=max(0,a['delta']);
  for b in range(budget+1):
   best=DP[-1][b]
   if b>=delta:
    u=DP[last][b-delta];q=(u[0]+a['cover'],u[1]+a['old_ops']-a['new_ops'],u[2]+[j])
    if q[:2]>best[:2]:best=q
   row.append(best)
  DP.append(row)
 rows=[]
 for budget0 in (0,5,10,20,40):
  ids=DP[-1][budget0][2];sel=[candidates[j] for j in ids];new=[];last=0
  for a in sel:new+=orig[last:a['start']]+a['rep'];last=a['stop']
  new+=orig[last:];c.ops=new;f=out.with_name(f'{out.stem}_B{budget0}.kmb');f.write_bytes(c.to_bytes());d=lifetimes(c);pmax,hist=pressure(range(len(new)),d)
  r=dict(budget=budget0,peak=pmax,full_width_ops=hist[oldQ],old_full_width_ops=prefix[-1],ops=len(new),paid=cost(new),paid_delta=cost(new)-cost(orig),selected=[{k:v for k,v in a.items() if k!='rep'} for a in sel],sha256=hashlib.sha256(f.read_bytes()).hexdigest());rows.append(r);print({k:v for k,v in r.items()if k!='selected'},flush=True)
 r=dict(source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_ops=len(orig),source_paid=cost(orig),certified_candidates=[{k:v for k,v in a.items()if k!='rep'}for a in candidates],failure_reasons=fail,variants=rows,scope='local exact value and phase; removed private HMR results unread until overwrite; full circuit width unchanged unless actual allocator proves otherwise; no official verifier');out.with_suffix('.json').write_text(json.dumps(r,indent=2))
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))