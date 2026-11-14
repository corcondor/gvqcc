#!/usr/bin/env python3
"""Cost-targeted small search: drop three old rotations, add two independent parities."""
import json,pathlib,time,itertools,math
import numpy as np
from invsqrt_structural_search import read_basis,solve,SCALE,MAX
p=pathlib.Path('invsqrt_structural_work');start=time.time();desc,bits,idx,e,tol=read_basis();B=bits[idx].T.copy();inp=np.load(p/'search_inputs.npz');active=inp['active'];basecoef=inp['basecoef'];weight=1/np.maximum(tol[active],1.0);As=np.asarray(B[active],float);Awfull=As*weight[:,None];Qfull=np.linalg.qr(Awfull,mode='reduced')[0]
Vs=[];cand=[];seen=set()
for line in (7705,8075,8189):
 ss=[i for i,d in enumerate(desc) if d['kind']=='snapshot' and d['line']==line];arr=bits[ss][:,active]
 for a in range(46):
  for b in range(a,46):
   v=arr[a] if a==b else arr[a]^arr[b];key=np.packbits(v,bitorder='little').tobytes()
   if key in seen or not v.any():continue
   seen.add(key);vv=v*weight;vp=vv-Qfull@(Qfull.T@vv)
   if vp@vp<1e-8:continue # genuinely outside the old Boolean linear span
   Vs.append(v);cand.append({'line':line,'qubits':[a] if a==b else [a,b],'basis_indices':[ss[a]] if a==b else [ss[a],ss[b]]})
V=np.asarray(Vs,float).T*weight[:,None];norm0=np.sum(V*V,axis=0);small=list(map(int,np.argsort(abs(basecoef))[:4]));scenarios=[(small[0],)]+list(itertools.combinations(small,3));results=[]
print(json.dumps({'new_candidates':len(cand),'scenarios':scenarios}),flush=True)
for drop in scenarios:
 keep=[j for j in range(B.shape[1]) if j not in drop];Aw=As[:,keep]*weight[:,None];Q=np.linalg.qr(Aw,mode='reduced')[0];y=(-e[active]+As[:,list(drop)]@basecoef[list(drop)])*weight;res=y-Q@(Q.T@y);pv=V-Q@(Q.T@V);norm=np.maximum(np.sum(pv*pv,axis=0),1e-10);improve=(V.T@res)**2/norm
 first=[]
 for k in np.argsort(-improve)[:80]:
  if any(abs(float(pv[:,k]@pv[:,j]))>math.sqrt(norm[k]*norm[j])*(1-1e-8) for j in first):continue
  first.append(int(k))
  if len(first)==4:break
 pairs=[]
 if len(drop)==1:pairs=[(k,) for k in first]
 else:
  for k in first[:2]:
   q1=pv[:,k]/math.sqrt(norm[k]);r2=res-q1*(q1@res);v2=pv-q1[:,None]*(q1@pv)[None,:];n2=np.maximum(np.sum(v2*v2,axis=0),1e-10);gain=(V.T@r2)**2/n2;gain[n2<1e-7]=0;chosen=[]
   for j in np.argsort(-gain)[:80]:
    if j==k or any(abs(float(v2[:,j]@v2[:,z]))>math.sqrt(n2[j]*n2[z])*(1-1e-8) for z in chosen):continue
    chosen.append(int(j));pairs.append((k,int(j)))
    if len(chosen)==2:break
 print(json.dumps({'drop':drop,'candidate_pairs':pairs}),flush=True)
 for pair in pairs:
  news=[]
  for k in pair:
   c=cand[k];v=bits[c['basis_indices'][0]].copy()
   for j in c['basis_indices'][1:]:v^=bits[j]
   news.append(v)
  new=np.array(news,dtype=np.uint8).T;rr=solve(B,e,tol,active,dropped=[(j,-float(basecoef[j])) for j in drop],new=new,maxiter=10);nrot=33-len(drop)+len(pair);row={'drop':drop,'candidates':[cand[k] for k in pair],'result':rr,'generic_rotations':nrot}
  if rr and rr['margin_scaled']>0:
   eps=np.pi*rr['margin_scaled']*SCALE/nrot;row['rotation_toffoli_equiv']=nrot*(.56*np.log2(1/eps)+5.3)/4
  results.append(row);print(json.dumps({'drop':drop,'pair':pair,'margin':None if not rr else rr['margin_scaled'],'cost':row.get('rotation_toffoli_equiv')}),flush=True);(p/'pair_results.json').write_text(json.dumps({'experiments':results,'elapsed_seconds':time.time()-start},indent=2))
print('DONE',time.time()-start,flush=True)
