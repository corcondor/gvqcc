"""Cross-stage two-output rank-one tensor contraction.
Keep the original q virtual through a subsequent carry and two HMRs.
The two surviving factors are put into one persistent affine gauge; R
is used for two data updates and one measured-phase update without
rebuilding the affine gauge. Exact replay and 36-slot check separate.
"""
from v43_lazy_transport import *

def transport_mask(L,o):
 if o.raw==17 and L>>(o.wires[0]+1)&1:return L^1
 if o.raw==33 and L>>(o.wires[1]+1)&1:return L^(1<<(o.wires[0]+1))
 return L

def persistent(A,B,L,exclude):
 best=None
 for a,b in [(A,B),(B,A)]:
  for p in range(37):
   if p in exclude or not a>>(p+1)&1:continue
   bb,ll=b,L
   if bb>>(p+1)&1:bb^=a;ll^=a
   for q in range(37):
    if q in exclude or q==p or not bb>>(q+1)&1:continue
    aa=a^(bb^(1<<(q+1)))if a>>(q+1)&1 else a
    if not aa>>(p+1)&1:continue
    pre=affine_ops(bb,q)+affine_ops(aa,p)
    if any(w in exclude for o in pre for w in o.wires):continue
    for o in pre:ll=transport_mask(ll,o)
    score=(2*len(pre)+3*ll.bit_count(),len(pre))
    if best is None or score<best[0]:best=(score,p,q,pre,ll)
 return best[1:]if best else None

def scan(src,out):
 K=NativeKMB.read(src);O=K.ops;one,S,A,M,D=sample(K,2048,43531);R=Counter();C=[]
 for k in range(len(O)-6):
  g=O[k:k+7]
  if [o.raw for o in g]!=[33,33,49,80,33,33,80]:continue
  q,x=g[0].wires;d,y=g[1].wires
  if len({q,x,d,y})!=4 or g[2].wires!=(q,d,y)or g[3].wires!=(d,)or g[4].wires!=(q,y)or g[5].wires!=(x,q)or g[6].wires!=(q,):continue
  if S[k][y] or D[k]or D[k+7]:continue
  R['terminal_patterns']+=1
  a=None
  for j in range(k-1,max(-1,k-1200),-1):
   o=O[j]
   if q not in o.wires:continue
   if o.raw==49 and o.wires[-1]==q and not S[j][q] and not D[j]:a=j;break
   if o.raw in (17,33)and o.wires[-1]==q:continue
   break
  if a is None:continue
  R['generator_matches']+=1;assert O[a].raw==49
  ids=[j for j in range(37)if j not in(q,x,d,y)and S[k][j]];s=list(S[k]);f0,f1=O[a].wires[:2];aa,bb=[form(S[a][i],s,ids,one)for i in (f0,f1)]
  if aa is None or bb is None:R['factor_transport_fail']+=1;continue
  r=S[k][q]^S[k][d]^S[k][x];l=form(r^(S[a][f0]&S[a][f1]),s,ids,one)
  if l is None:R['linear_residue_fail']+=1;continue
  z=persistent(aa,bb,l,{q,x,d,y})
  if z is None:R['gauge_fail']+=1;continue
  p,t,pre,L=z;rec_d=g[3].measurement;rec_x=g[6].measurement
  def upd(target):return [Op(49,(p,t,target))]+lin_emit(L,target,0,None)
  def phase(rec):return [Op(160,(p,t),condition=rec)]+lin_emit(L,None,128,rec)
  prefix=[o for o in O[a+1:k]if q not in o.wires];body=prefix+pre+upd(x)+[Op(33,(d,y)),Op(17,(d,)),Op(49,(d,x,y)),Op(17,(d,)),Op(80,(x,),rec_x)]+phase(rec_x)+[Op(33,(d,x))]+upd(x)+[Op(80,(d,),rec_d)]+pre[::-1]
  body=compress(body);assert all(q not in o.wires for o in body)
  hs=[j for j in range(a,k)if O[j].raw&127==80]+[k+6,k+3]
  C.append(dict(a=a,b=k+7,core=a,body=list(map(pack,body)),event_order=hs,kind='crossstage_persistent_rank_one',donor='new shared affine tensor gauge',meta=dict(terminal=k,omitted=q,output=x,carrier=d,other_output=y,factor_masks=[aa,bb],linear_mask=l,pivots=[p,t],gauge_ops=len(pre),source_paid=sum(o.raw&127 in PAID for o in O[a:k+7]),body_paid=sum(o.raw&127 in PAID for o in body))))
  print('CAND',a,k+7,'omitted',q,'orig',len(O[a:k+7]),'body',len(body),'paid',C[-1]['meta']['source_paid'],C[-1]['meta']['body_paid'],flush=True)
 print('DONE',dict(R),len(C),flush=True);Path(out).write_text(json.dumps(dict(parent_sha=sha(src),stats=dict(R),candidates=C),indent=2))
if __name__=='__main__':scan(*sys.argv[1:])
