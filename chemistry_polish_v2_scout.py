import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1')
import numpy as np,json,time
from scipy.optimize import nnls
from inverse_v2_chemistry_refit import FixedAngles
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
b=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz'))
m=FixedAngles(b); w=b['W'];ii=b['H2_I'];d=ii-w.sum(1);n=w.size
x=np.r_[w.ravel(),ii.ravel()]; f,g,c,j,met=m.evaluate(x,44,smooth=0)

def transform(a):
 a=a.copy();a[:n]= (a[:n].reshape(w.shape)+a[n:].reshape(ii.shape)[:,None,:]).ravel();return a
q=transform(g);J=np.array([transform(t) for t in j]);
# Gradients normalized in each constraint for stationarity diagnostics.
Jn=J/np.linalg.norm(J,axis=1)[:,None]
mu,res=nnls(Jn.T,-q)
zeros=np.abs(w)<1e-10
print(json.dumps({'metrics':met,'constraint':c.tolist(),'W_abs_quantiles':np.quantile(np.abs(w),[0,.01,.1,.5,.9,.99,1]).tolist(),'num_zeros':int(zeros.sum()),'D_abs_quantiles':np.quantile(np.abs(d),[0,.1,.5,.9,1]).tolist(),'original_gradient_norm':float(np.linalg.norm(g)),'natural_gradient_norm':float(np.linalg.norm(q)),'constraint_gradient_norms':np.linalg.norm(J,axis=1).tolist(),'kkt_multipliers_normalized':mu.tolist(),'kkt_residual':res,'kkt_relative_residual':res/np.linalg.norm(q),'minabs_eigen_noinfo':None}),flush=True)
# Check all grad entries via random directional derivatives in natural coordinates.
rng=np.random.default_rng(71); y=np.r_[w.ravel(),d.ravel()]
for direction in ('dense','support','d_only'):
 z=rng.normal(size=y.shape)
 if direction=='support':z[:n][zeros.ravel()]=0
 if direction=='d_only':z[:n]=0
 z/=np.linalg.norm(z)
 def orig(yy):
  ww=yy[:n].reshape(w.shape);dd=yy[n:].reshape(d.shape)
  return np.r_[ww.ravel(),(dd+ww.sum(1)).ravel()]
 h=1e-7
 p=m.evaluate(orig(y+h*z),44,smooth=1e-7); mm=m.evaluate(orig(y-h*z),44,smooth=1e-7);v=m.evaluate(x,44,smooth=1e-7)
 fd=np.r_[(p[0]-mm[0])/(2*h),(p[2]-mm[2])/(2*h)];an=np.r_[transform(v[1])@z,np.array([transform(t) for t in v[3]])@z]
 print(json.dumps({'gradient_direction':direction,'fd':fd.tolist(),'an':an.tolist(),'relative_max_error':float(np.max(np.abs(fd-an)/np.maximum(1,np.abs(fd))))}),flush=True)
