#!/usr/bin/env python3
"""Drop one C mode per r from R9 B127 C46 while PRESERVING angle_words and 15 actual public KMB.
One-body and gap are exact when dropped unit vector v is orthogonal to d=H2_I-sum(W,axis=1).
Metric is exact FeMoCo 2-body error; no change to KMB. No official final score asserted.
"""
import numpy as np,scipy.linalg as la,json,time
from pathlib import Path
from scipy.optimize import minimize
from scipy.linalg import null_space
from sys import path
path.insert(0,'/mnt/data/gvqcc_33144_exp')
from longtrain.physical_verify import Physical,decode
root=Path('/mnt/data/gvqcc_actual_branch');p=Physical('/mnt/data/gvqcc_33144_bundle_v2/chem_gpu_inputs.npz')
z=np.load(root/'v8/dfthcsos/submission.npz');d={k:z[k].copy() for k in z.files}
w=d['W'];H=d['H2_I'];R,B,C=w.shape;assert (R,B,C)==(9,127,46)
print('BASE',p.evaluate(d),flush=True)
# packed features from angle_word arrays
U=decode(d['angle_words'],d['tree_edges'],int(d.get('brot',7)))[76:].reshape(R,B,76)
Packed=((U[:,:,p.ii]*U[:,:,p.jj])*p.sc).reshape(R,B,-1)
Xs=[np.einsum('bc,bn->cn',w[r],Packed[r],optimize=True) for r in range(R)]
All=np.concatenate(Xs,axis=0)
Residual=All.T@All-p.T
print('BASE e2 direct',np.linalg.norm(Residual),flush=True)

# per-r candidate vectors via SVD in W, X, no d and constrained d⊥
models=['delete_small_weight','delete_small_packed','svd_W_orth_d','svd_X_orth_d','residual_sphere']
results=[]
for model in models:
 t0=time.time();Ws=[];Hs=[];Rnow=Residual.copy();dropped=[];rv=[]
 for r in range(R):
  X=Xs[r];D=(H[r]-w[r].sum(axis=0));normD=np.linalg.norm(D)
  Bd=null_space(D[None,:]) # C x (C-1) normalized, v must be orthogonal to D
  G=X@X.T
  # candidates rotate or directly delete
  if model=='delete_small_weight':
   i=np.argmin(np.linalg.norm(w[r],axis=0));v=np.eye(C)[:,i] # not orthogonal to D; quantify
  elif model=='delete_small_packed':
   i=np.argmin(np.diag(G));v=np.eye(C)[:,i]
  else:
   GG=(w[r].T@w[r]) if model=='svd_W_orth_d' else G
   gproj=Bd.T@GG@Bd
   val,vec=la.eigh(gproj);v=Bd@vec[:,0]
   if model=='residual_sphere':
    # objective equals exact delta in squared error if we remove rank-1 x x^T.
    Hr=X@Rnow@X.T;B= Bd
    Gp=B.T@G@B;Hp=B.T@Hr@B
    def fun(u):
     v=u/np.linalg.norm(u);gg=v@Gp@v;hh=v@Hp@v
     return gg*gg-2*hh
    def jac(u):
     nv=np.linalg.norm(u);v=u/nv;gg=v@Gp@v
     g=(4*gg*Gp@v-4*Hp@v);return (g-v*(g@v))/nv
    best=(fun(Bd.T@v),v)
    rng=np.random.default_rng(3300+r)
    for t in range(8):
     start=vec[:,0] if t==0 else rng.normal(size=C-1)
     opt=minimize(fun,start,jac=jac,method='BFGS',options={'maxiter':130,'gtol':1e-12})
     sol=opt.x/np.linalg.norm(opt.x)
     if fun(sol)<best[0]:best=(fun(sol),Bd@sol)
    v=best[1]
  v=v/np.linalg.norm(v)
  # basis of orthogonal complement
  M=null_space(v[None,:]);assert np.allclose(M.T@M,np.eye(C-1),atol=1e-8)
  wr=w[r]@M;hr=H[r]@M
  Ws.append(wr);Hs.append(hr)
  vX=v@X;Rnow-=np.outer(vX,vX)
  rv.append(dict(r=r,norm_d_dot_v=float(D@v),norm_x=float(np.linalg.norm(vX)),delta_e2_sq=float(np.sum(Rnow**2)-np.sum((Rnow+np.outer(vX,vX))**2)),metric_val=float(np.linalg.norm(Rnow))))
  dropped.append(v)
 trial=dict(d,W=np.stack(Ws),H2_I=np.stack(Hs))
 # U no change and angle_words remain exact
 ps=p.evaluate(trial,full=True)
 fname=f'c45_V8_sameKMB_{model}.npz';np.savez_compressed(root/fname,**trial)
 print('MODEL',model,'seconds',round(time.time()-t0,2),'e1',ps['error_1'],'e2',ps['error_2'],'lambda',ps['lambda_eff'],'pass',ps['admissible'],'Ddotv max',max(abs(x['norm_d_dot_v']) for x in rv),flush=True)
 results.append(dict(model=model,physics=ps,rv=rv,source=str(fname),same_angle_words=bool(np.array_equal(trial['angle_words'],d['angle_words'])),all_original_15_KMB_byteidentical=True))
Path(root/'c45_sameKMB_results.json').write_text(json.dumps(results,indent=2)+'\n')