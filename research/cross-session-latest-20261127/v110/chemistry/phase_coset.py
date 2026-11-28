"""Reachable quadratic phase coset synthesis with one or two literal products.
Reduces phase functions modulo the affine span of ALL live wires, then performs
an exact two-sum search on pair-product syndromes.  Every emitted phase remains
exact over both legal endpoint domains; affine transport is validated separately.
"""
from affine_care_general import *

AFF={17,33,34};DIAG={0,16,32,128,144,160};ALLOW=AFF|DIAG

def projector(rows,one):
 p,_=pivot(rows,one)
 return sorted(p.items(),reverse=True)

def reduce_with(p,v):
 e=0
 for h,(a,c)in p:
  if v>>h&1:v^=a;e^=c
 return v,e

def linear_ops(coeff,n,cond):
 flag=128 if cond is not None else 0;out=[]
 if coeff>>n&1:out.append(Op(flag,(),condition=cond))
 for q in range(n):
  if coeff>>q&1:out.append(Op(flag|16,(q,),condition=cond))
 return out

def phase_search(rows,one,phases,cap):
 n=len(rows);p=projector(rows,one);answers={};remaining={}
 for cond,val in phases.items():
  r,c=reduce_with(p,val)
  if not r:answers[cond]=(c.bit_count(),c,[])
  remaining[cond]=(r,c)
 # Keep all distinct product values; among equal syndrome columns, distinct
 # linear residues can yield quite different correction weights.
 products=[];lookup={};live=[q for q,v in enumerate(rows)if v]
 for ii,i in enumerate(live):
  for j in live[ii+1:]:
   r,c=reduce_with(p,rows[i]&rows[j])
   if not r:continue
   ent=(c,i,j);products.append((r,c,i,j));lookup.setdefault(r,[]).append(ent)
 for cond,(rhs,lc)in remaining.items():
  best=answers.get(cond,(cap,0,[]))
  for c,i,j in lookup.get(rhs,[]):
   lin=lc^c;cost=1+lin.bit_count()
   if cost<best[0]:best=(cost,lin,[(i,j)])
  # No approximate hashing: syndrome equality is exact over all addresses.
  for r,c,i,j in products:
   other=rhs^r
   if other<r:continue
   for cc,a,b in lookup.get(other,[]):
    lin=lc^c^cc;cost=2+lin.bit_count()
    if cost<best[0]:best=(cost,lin,[(i,j),(a,b)])
  if best[0]<cap:answers[cond]=best
 if len(answers)!=len(phases):return None
 out=[]
 for cond,(cost,lin,pairs)in answers.items():
  out.extend(linear_ops(lin,n,cond));flag=128 if cond is not None else 0
  for i,j in pairs:out.append(Op(flag|32,(i,j),condition=cond))
 return out

def signature_actual(gs,start,one):
 rows=start[:];phases={}
 for o in gs:
  if o.raw in AFF:rows=runaff([o],rows,one)
  else:
   f=one
   for q in o.wires:f&=rows[q]
   phases[o.condition]=phases.get(o.condition,0)^f
 return rows,{k:v for k,v in phases.items()if v}

def run(family,out,k):
 start=time.monotonic();p=family/f'angle_k_{k}.kmb';c=V.parse(p);native=NativeKMB.read(p)
 with np.load(family/'submission.npz')as d:targets=V.targets(d['angle_words'])
 n=1219;one=(1<<(2*n))-1;pair=[V.initial(c,targets[k+d],n)for d in(0,1)];rows=[a|(b<<n)for a,b in zip(*pair)]
 ops=[];buf=[];records=[];rng=random.Random(442423+k);blocks=0
 def flush():
  nonlocal rows,blocks
  if not buf:return
  after,phases=signature_actual(buf,rows,one);best=buf[:];method=None
  if phases and len(buf)>=8:
   aff=[o for o in buf if o.raw in AFF];aa=aff[:]
   for rev in(False,True):
    a=build(after if rev else rows,rows if rev else after,one,len(aa),rng,0)
    if a is not None and len(a)<len(aa):aa=list(reversed(a))if rev else a
   if len(aa)+1<len(best):
    for rev in(False,True):
     phase=phase_search(after if rev else rows,one,phases,len(best)-len(aa))
     if phase is not None:
      cand=aa+phase if rev else phase+aa
      if len(cand)<len(best):best=cand;method='end'if rev else'start'
   assert signature_actual(best,rows,one)==(after,phases)
  if len(best)<len(buf):
   rec=dict(block=blocks,index=len(ops),before=len(buf),after=len(best),phase_functions=len(phases),method=method);records.append(rec)
   print('change',k,rec,flush=True)
  blocks+=1;ops.extend(best);rows=after;buf.clear()
 for i,o in enumerate(native.ops):
  if o.raw in ALLOW:buf.append(o);continue
  flush();b=o.raw&127;q=o.wires
  if b==49:rows[q[2]]^=rows[q[0]]&rows[q[1]]
  elif b==80:rows[q[0]]=0
  ops.append(o)
 flush();new=copy.deepcopy(native);new.ops=ops;out.mkdir(parents=True,exist_ok=True);q=out/p.name;q.write_bytes(new.to_bytes())
 parsed=V.parse(q);checks=[V.endpoint(parsed,targets[a],targets[b],n)for a,b in[(k,k+1),(k+1,k)]];assert all(x['pass_all']for x in checks),checks
 r=dict(status='PASS_EXACT_REACHABLE_PHASE_COSET',bank=k,input_sha256=V.sha(p),output_sha256=V.sha(q),before=len(native.ops),after=len(ops),records=records,checks=checks,seconds=time.monotonic()-start)
 (out/f'bank_{k}.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({x:r[x]for x in('bank','before','after','seconds')}),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('family',type=Path);ap.add_argument('out',type=Path);ap.add_argument('--bank',type=int);a=ap.parse_args()
 for k in([a.bank]if a.bank is not None else range(15)):run(a.family,a.out,k)