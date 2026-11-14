#!/usr/bin/env python3
"""Select new parity bases against the residual created by removing old rotations."""
import json,pathlib,time,itertools
import numpy as np
from fractions import Fraction
from invsqrt_structural_search import read_basis,solve,SCALE,MAX
p=pathlib.Path('invsqrt_structural_work');start=time.time()
desc,bits,idx,e,tol=read_basis();B=bits[idx].T.copy();inp=np.load(p/'search_inputs.npz');active=inp['active'];basecoef=inp['basecoef'];weight=1/np.maximum(tol[active],1.0)
Vs=[];cand=[];seen=set()
for line in (7705,8075,8189):
 ss=[i for i,d in enumerate(desc) if d['kind']=='snapshot' and d['line']==line];arr=bits[ss][:,active]
 for a in range(46):
  for b in range(a,46):
   v=arr[a] if a==b else arr[a]^arr[b];key=np.packbits(v,bitorder='little').tobytes()
   if key in seen or not v.any():continue
   seen.add(key);Vs.append(v);cand.append({'line':line,'qubits':[a] if a==b else [a,b],'basis_indices':[ss[a]] if a==b else [ss[a],ss[b]]})
V=np.array(Vs,dtype=float).T*weight[:,None];norm0=np.sum(V*V,axis=0);As=np.asarray(B[active],dtype=float);results=[]
small=list(map(int,np.argsort(abs(basecoef))[:4]));scenarios=[(small[0],)]+list(itertools.combinations(small,2))
for drop in scenarios:
 keep=[j for j in range(B.shape[1]) if j not in drop];Aw=As[:,keep]*weight[:,None];Q,R=np.linalg.qr(Aw,mode='reduced');y=(-e[active]+As[:,list(drop)]@basecoef[list(drop)])*weight;resid=y-Q@(Q.T@y);norm=np.maximum(norm0-np.sum((Q.T@V)**2,axis=0),1e-12);imp=(V.T@resid)**2/norm;imp[norm<1e-7]=0
 order=np.argsort(-imp);todo=[];projs=[]
 # Correlation ranking can repeat affine-equivalent bases; retain projection diversity.
 for k in order[:100]:
  v=V[:,k]-Q@(Q.T@V[:,k]);vn=np.linalg.norm(v)
  if vn<1e-7:continue
  v/=vn
  if any(abs(float(v@z))>1-1e-8 for z in projs):continue
  projs.append(v);todo.append(int(k))
  if len(todo)==5:break
 print(json.dumps({'drop':drop,'ranked':todo}),flush=True)
 for k in todo:
  c=cand[k];new=bits[c['basis_indices'][0]].copy()
  for j in c['basis_indices'][1:]:new^=bits[j]
  res=solve(B,e,tol,active,dropped=[(j,-float(basecoef[j])) for j in drop],new=new,maxiter=10)
  row={'candidate':c,'drop':drop,'result':res};nrot=34-len(drop)
  if res and res['margin_scaled']>0:
   eps=np.pi*res['margin_scaled']*SCALE/nrot;row['rotation_toffoli_equiv']=nrot*(.56*np.log2(1/eps)+5.3)/4
  results.append(row);print(json.dumps({'drop':drop,'qubits':c['qubits'],'line':c['line'],'margin':None if not res else res['margin_scaled'],'cost':row.get('rotation_toffoli_equiv')}),flush=True)
  (p/'replace_results.json').write_text(json.dumps({'experiments':results,'elapsed_seconds':time.time()-start},indent=2))
print('DONE',time.time()-start,flush=True)
