"""22Q shared translation gauges, exact same V52 plan; research only."""
import sys,json,struct,random
from pathlib import Path
from collections import defaultdict
from ancillaless import W,MOD,expand,mcx,verify,NativeKMB,Op

def gray(x):
 y=x
 while x:x>>=1;y^=x
 return y

def cover(vals,k):
 rng=random.Random(4321+k);remaining=sorted(vals);groups=[];prev=0
 candidates=set(range(1,1<<k)) if k<=9 else {1<<i for i in range(k)}|{(1<<k)-1}|{rng.randrange(1,1<<k) for _ in range(192)}
 while remaining:
  best=max(candidates,key=lambda v:(sum((s&v).bit_count()&1 for s in remaining),-(v^prev).bit_count(),-v))
  selected=[s for s in remaining if (s&best).bit_count()&1];assert selected
  groups.append((best,selected));remaining=[s for s in remaining if not ((s&best).bit_count()&1)];prev=best
 return groups

def emit(plan,src,out):
 K=NativeKMB.read(src);C,G=expand(plan);ops=[];tags=[];ang=[];glob=defaultdict(int);stats=[]
 def cx(a,b):ops.append(Op(33,(a,b)))
 def rot(p,a,tag):
  if a%MOD:ops.append(Op(19,(p,)));ang.append(a%MOD);tags.append(tag)
 def change(cur,s,p):
  delta=cur^s;assert not(delta>>p&1)
  while delta:q=(delta&-delta).bit_length()-1;cx(q,p);delta&=delta-1
 def parities(L,tag):
  by=defaultdict(list)
  for s,a in L:
   if a%MOD:by[s.bit_length()-1].append((s,a))
  for p,group in sorted(by.items()):
   cur=1<<p
   for s,a in sorted(group,key=lambda z:gray(z[0]^(1<<p))):
    change(cur,s,p);cur=s;rot(p,a,tag(s))
   change(cur,1<<p,p)
 def translation(cs,delta):
  if not delta:return
  p=(delta&-delta).bit_length()-1;bits=[q for q in range(W)if q!=p and delta>>q&1]
  for q in bits:cx(p,q)
  ops.extend(mcx(cs,p))
  for q in reversed(bits):cx(p,q)
 if C:
  rot(0,C,['C',0]);ops.append(Op(17,(0,)));rot(0,C,['C',1]);ops.append(Op(17,(0,)))
 for (d,pr),vals in sorted(G.items()):
  if not vals:continue
  cs=list(range(W-d,W));neg=[Op(17,(q,))for q in cs if not (pr>>(q-(W-d))&1)]
  for s,a in vals.items():assert s and s.bit_length()<=W-d;glob[s]-=a
  groups=cover(vals,W-d);prev=0;ops.extend(neg)
  for v,masks in groups:
   translation(cs,prev^v);prev=v
   parities([(s,vals[s]) for s in masks],lambda s:['F',d,pr,s])
  translation(cs,prev);ops.extend(neg[::-1]);stats.append([d,pr,len(vals),len(groups),len(set(s.bit_length()-1 for s in vals))])
 parities(glob.items(),lambda s:['P',s])
 h=list(K.header);h[1]=W;h[2]=0;h[10]=len(ang)
 F=NativeKMB(K.prefix16,tuple(h),[(t,b''.join(struct.pack('<QQ',0,a)for a in ang)if t==10 else z)for t,z in K.sections],ops)
 Path(out).write_bytes(F.to_bytes());Path(str(out)+'.tags.json').write_text(json.dumps(tags));Path(str(out)+'.groups.json').write_text(json.dumps(stats));print('emitted',len(ops),len(ang),sum(o.raw==49 for o in ops),'groups',sum(r[3] for r in stats),'old_groups',sum(r[4] for r in stats),flush=True)
if __name__=='__main__':
 plan=json.load(open(sys.argv[1]));src=sys.argv[2];out=sys.argv[3];emit(plan,src,out);verify(plan,out)
