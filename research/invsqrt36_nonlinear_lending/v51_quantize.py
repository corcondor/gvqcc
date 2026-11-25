"""Finite integer spectral repair; no asymptotic Fourier transfer.
Run in the PR116 archive environment with PYTHONPATH set to it.
python v51_quantize.py v49_joint_spectral_plan.json output_plan.json 80
"""
import json,sys,math,time
from pathlib import Path
import numpy as np
from v49_spectral import fw,N,SCALE
P=json.load(open(sys.argv[1]));Q=Path(sys.argv[2]);t=time.time();A=SCALE
E=(A>>24)*int(sys.argv[3])//100 if len(sys.argv)>3 else A>>24
L=(A-E)**2;H=(A+E)**2
assert all(b['start']>=1 for b in P['blocks']);covered=np.zeros(N+1,np.uint8)
lo=np.zeros(N+1,np.int64);hi=np.zeros(N+1,np.int64)
for x in range(1,N+1):lo[x]=math.isqrt((L-1)//x)+1;hi[x]=math.isqrt(H//x)
result=[];hist=[]
for b in P['blocks']:
 st=b['start'];m=1<<b['k'];end=min(st+m,N+1);n=end-st;covered[st:end]+=1
 ids=np.array(b['indices'],np.int64);cs=np.array(b['coeff'],np.int64);ix=np.argsort(-np.abs(cs));ids=ids[ix];cs=cs[ix];ls=lo[st:end];hs=hi[st:end];cache={};best=None
 def test(r,p):
  global best
  key=(r,p)
  if key in cache:return cache[key]
  step=1<<p;v=((cs[:r]+step//2)//step)*step if p else cs[:r];w=np.zeros(m,np.int64);w[ids[:r]]=v;y=fw(w)[:n];ok=bool(np.all((y>=ls)&(y<=hs)));nnz=int(np.count_nonzero(v));rec=(ok,nnz)
  cache[key]=rec
  if ok:
   if best is None or (nnz,-p,r)<best[0]:best=((nnz,-p,r),ids[:r][v!=0].tolist(),v[v!=0].tolist(),float(np.max(np.abs(y.astype(np.float64)*np.sqrt(np.arange(st,end))/A-1)*2**24)))
  return rec
 for p in [0,16,19,21,23,25]:
  probes=sorted(set([max(1,int(len(ids)*q))for q in [.25,.4,.55,.7,.85,.95,1.0]]));good=[]
  for r in probes:
   if test(r,p)[0]:good.append(r)
  if not good:continue
  u=min(good);l=max([r for r in probes if r<u and not test(r,p)[0]]+[0])
  while u-l>1:
   mid=(u+l)//2
   if test(mid,p)[0]:u=mid
   else:l=mid
  for r in range(max(1,u-3),min(len(ids),u+3)+1):test(r,p)
 assert best
 score,ii,cc,worst=best;z=dict(start=st,k=b['k'],indices=ii,coeff=cc,role='adaptive_integer_spectral');result.append(z);hist.append(dict(start=st,k=b['k'],before=len(ids),after=len(ii),step_power=-score[1],max_relative_ratio=worst,probes=len(cache)));print(st,len(ids),'->',len(ii),'step',-score[1],'max',worst,flush=True)
assert np.all(covered[1:]==1)
Q.write_text(json.dumps(dict(legal=N,scale=SCALE,blocks=result,scope='analytic target; exact integer intervals on all legal x',history=hist,terms=sum(len(b['indices'])for b in result),seconds=time.time()-t)));print('total',sum(len(b['indices'])for b in P['blocks']),sum(len(b['indices'])for b in result),'seconds',time.time()-t,flush=True)
