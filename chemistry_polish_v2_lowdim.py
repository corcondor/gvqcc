"""Reduced exact-objective constrained search: per-column scales and native d."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import time,json,argparse,numpy as np
from pathlib import Path
from scipy.optimize import minimize
from inverse_v2_chemistry_refit import FixedAngles
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=240);args=p.parse_args()
b=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz'));m=FixedAngles(b)
w0=b['W'];d0=b['H2_I']-w0.sum(1);n=w0.size;nsmall=d0.size;shape=w0.shape
cachez=None;cacheval=None;start=time.monotonic();best=None;bestf=float('inf');trace=[]
class Budget(Exception):pass

def ev(z):
 global cachez,cacheval,best,bestf
 if cachez is not None and np.array_equal(z,cachez):return cacheval
 if time.monotonic()-start>args.seconds:raise Budget()
 w=w0*(1+z[:nsmall].reshape(d0.shape)[:,None,:]);d=d0+z[nsmall:].reshape(d0.shape);ii=d+w.sum(1)
 f,g,c,J,met=m.evaluate(np.r_[w.ravel(),ii.ravel()],shape[2],smooth=0)
 ratio=(.01999998/.019999999)**2;c[:2]=(c[:2]+1)*ratio-1;J[:2]*=ratio;c[2]+=(3.914898001-3.91489802)/.01
 def tr(gg):
  gw=gg[:n].reshape(shape);gi=gg[n:].reshape(d0.shape)
  return np.r_[np.sum((gw+gi[:,None,:])*w0,axis=1).ravel(),gi.ravel()]
 gr=tr(g);jr=np.array([tr(v) for v in J]);cachez=z.copy();cacheval=(f,gr,c,jr,met,w,ii)
 if met['error1']<=.020 and met['error2']<=.020 and met['gap']>3.914898 and met['Lambda_smooth']>49 and f<bestf:
  best=(w.copy(),ii.copy());bestf=f;bb=dict(b);bb['W']=w;bb['H2_I']=ii;np.savez_compressed(ROOT/'gvqcc_repo/chemistry_polish_v2_lowdim_candidate.npz',**bb)
 return cacheval
z=np.zeros(2*nsmall)
print(json.dumps({'initial':ev(z)[4],'variables':len(z)}),flush=True)
calls=0

def callback(z):
 global calls
 calls+=1
 row={'iteration':calls,'seconds':time.monotonic()-start,'metrics':ev(z)[4],'constraints':ev(z)[2].tolist()}
 trace.append(row)
 if calls%5==0:print(json.dumps(row),flush=True)
try:
 result=minimize(lambda z:ev(z)[:2],z,method='SLSQP',jac=True,constraints={'type':'ineq','fun':lambda z:-ev(z)[2],'jac':lambda z:-ev(z)[3]},bounds=[(-.03,.03)]*nsmall+[(-.03,.03)]*nsmall,callback=callback,options={'maxiter':150,'ftol':1e-11,'disp':False})
 status=str(result.message);z=result.x
except Budget:status='time budget'
print(json.dumps({'termination':status,'best_exact_lambda':bestf}),flush=True)
met=None
if best is not None:
 w,ii=best
 met=evaluate_dfthc_angle_words(b['angle_words'],w,ii-w.sum(1),m.S,m.beta,m.ref,brot=8,tree_edges=b['tree_edges'],energy_upper=UPPER_ENERGY)
 print(json.dumps({'official_numerical_candidate':met}),flush=True)
(ROOT/'gvqcc_repo/chemistry_polish_v2_lowdim_result.json').write_text(json.dumps({'termination':status,'official_numerical_metrics':met,'full_circuit_verified':False,'trace':trace},indent=2)+'\n')
