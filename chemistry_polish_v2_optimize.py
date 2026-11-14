"""Fixed-angle constrained weight refinement, with native W,d coordinates.
Preserves the official reference, shifts, angle table and circuit shape.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1')
import numpy as np,json,time,argparse
from pathlib import Path
from scipy.optimize import nnls, minimize
from inverse_v2_chemistry_refit import FixedAngles
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=600);p.add_argument('--method',default='sqp');p.add_argument('--smooth',type=float,default=1e-8);p.add_argument('--seed',type=int,default=0);args=p.parse_args()
base=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz'));m=FixedAngles(base)
w0=base['W'];i0=base['H2_I'];d0=i0-w0.sum(1);shape=w0.shape;n=w0.size;cnum=shape[2]
y0=np.r_[w0.ravel(),d0.ravel()]; y=y0.copy()
# Hold coefficients at the exact zero face to inspect smooth stationarity.
active=np.r_[np.abs(w0.ravel())>1e-8,np.ones(i0.size,dtype=bool)]
if args.method=='full':active[:]=True

def orig(yy):
 w=yy[:n].reshape(shape);d=yy[n:].reshape(i0.shape)
 return np.r_[w.ravel(),(d+w.sum(1)).ravel()]
def transform(a):
 a=a.copy();a[:n]=(a[:n].reshape(shape)+a[n:].reshape(i0.shape)[:,None,:]).ravel();return a
scale=None

def evaluate(yy):
 f,g,con,J,met=m.evaluate(orig(yy),cnum,smooth=args.smooth)
 # Keep tiny conservative margins while preserving baseline report separately.
 return f,transform(g),con,np.array([transform(t) for t in J]),met
f,g,con,J,met=evaluate(y)
scale=np.linalg.norm(J,axis=1);Jn=J/scale[:,None]
mu,res=nnls(Jn[:,active].T,-g[active]);stat=g+mu@Jn
print(json.dumps({'initial':met,'active_variables':int(active.sum()),'kkt_residual_active':res,'kkt_residual_inf_active':float(abs(stat[active]).max()),'kkt_lagrange':(mu/scale).tolist(),'objective_gradient_active_norm':float(np.linalg.norm(g[active]))}),flush=True)
# Smooth absolute value introduces a deliberate upper bound in objective only.
# Error and energy-gap constraints remain exact throughout.
start=time.monotonic();trace=[];best=None;steps=[];graddiffs=[]
bestval=float('inf');mu_previous=mu;rejects=0

def save(yy,tag='candidate'):
 data=dict(base); xx=orig(yy);data['W']=xx[:n].reshape(shape);data['H2_I']=xx[n:].reshape(i0.shape)
 path=ROOT/'gvqcc_repo'/('chemistry_polish_v2_'+args.method+'_'+tag+'.npz');np.savez_compressed(path,**data)
 return path

def feasible(met):return met['error1']<=.020 and met['error2']<=.020 and met['gap']>3.914898 and met['Lambda_smooth']>49

def record(yy,iteration,extra=None):
 global best,bestval
 ff,gg,cc,JJ,mm=evaluate(yy)
 row={'iteration':iteration,'seconds':time.monotonic()-start,'calls':m.calls,'metrics':mm,'constraints':cc.tolist()}
 if extra:row.update(extra)
 trace.append(row);print(json.dumps(row),flush=True)
 exact=m.evaluate(orig(yy),cnum,smooth=0)[-1]
 if feasible(exact) and exact['lambda_eff_smooth']<bestval:
  best=yy.copy();bestval=exact['lambda_eff_smooth'];save(best)
 return ff,gg,cc,JJ,mm
record(y,0)
if args.method=='aug':
 # Start from estimated KKT multipliers, rather than a zero-multiplier penalty.
 lag=mu/scale;latest=y.copy()
 class Budget(Exception):pass
 for out,rho in enumerate([10,100,1000,10000,100000]):
  def fun(yy):
   if time.monotonic()-start>args.seconds:raise Budget()
   f,g,c,J,_=evaluate(yy);t=np.maximum(0,lag+rho*c)
   return f+(t@t-lag@lag)/(2*rho),g+t@J
  def cb(yy):
   global latest
   latest=yy.copy()
  try:
   r=minimize(fun,y,jac=True,method='L-BFGS-B',callback=cb,options={'maxiter':120,'maxcor':12,'maxls':30,'ftol':1e-14,'gtol':1e-10});y=r.x;msg=str(r.message)
  except Budget:y=latest;msg='budget'
  f,g,con,J,met=record(y,out+1,{'rho':rho,'message':msg});lag=np.maximum(0,lag+rho*con)
  save(y,'last')
  if time.monotonic()-start>args.seconds:break
else:
 # Sequential quadratic directions on the current sparse orthant; normal
 # corrections keep all three originally active constraints on their boundary.
 trust=.002;hscale=.01
 for iteration in range(1,401):
  if time.monotonic()-start>args.seconds:break
  Jn=J/scale[:,None];cn=con/scale
  Ja=Jn[:,active];ga=g[active]
  def H(vec):
   q=vec.copy();alpha=[]
   for s,z in zip(steps[::-1],graddiffs[::-1]):
    r=1/(s@z);a=r*(s@q);alpha.append(a);q-=a*z
   q*=hscale
   for s,z,a in zip(steps,graddiffs,alpha[::-1]):
    r=1/(s@z);q+=s*(a-r*(z@q))
   return q
  hg=H(ga);hj=np.array([H(a) for a in Ja]);M=Ja@hj.T
  mu=np.linalg.lstsq(M,cn-Ja@hg,rcond=1e-12)[0];pa=-hg-mu@hj
  pn=np.linalg.norm(pa)
  if pn>trust:pa*=trust/pn
  # Preserve the sign of the active face for this local experiment.
  idx=np.flatnonzero(active);sw=np.sign(y[idx]);isw=idx<n
  crosses=isw&(pa*sw<0)
  if crosses.any() and args.method!='full':
   ratio=np.min(-.95*y[idx[crosses]]/pa[crosses]);pa*=min(1.,float(ratio))
  oldy=y.copy();oldgrad=g.copy();oldJ=J.copy();oldf=f;oldmu=mu.copy();accepted=False
  for line in range(14):
   yt=y.copy();yt[active]+=pa*(.5**line)
   # Retract to the three equalities using minimum-norm local Newton steps.
   for correction in range(5):
    ft,gt,ct,jt,mt=evaluate(yt)
    if np.max(np.abs(ct))<2e-8:break
    jtn=jt[:,active]/scale[:,None];ctn=ct/scale
    corr=-jtn.T@np.linalg.lstsq(jtn@jtn.T,ctn,rcond=1e-12)[0]
    yt[active]+=corr
   ft,gt,ct,jt,mt=evaluate(yt)
   if np.max(ct)<2e-6 and ft<oldf-1e-12:
    accepted=True;y=yt;f,g,con,J,met=ft,gt,ct,jt,mt;break
  if accepted:
   s=(y-oldy)[active];z=((g-oldgrad)+oldmu@((J-oldJ)/scale[:,None]))[active]
   curvature=s@z
   if curvature>1e-12*np.linalg.norm(s)*np.linalg.norm(z):
    steps.append(s);graddiffs.append(z)
    if len(steps)>12:steps.pop(0);graddiffs.pop(0)
    hscale=float(np.clip(curvature/(z@z),1e-7,10))
   trust=min(.05,trust*1.3);rejects=0
  else:
   trust*=.25;steps=[];graddiffs=[];rejects+=1
  if iteration%5==0 or not accepted or iteration==1:
   f,g,con,J,met=record(y,iteration,{'accepted':accepted,'line_search':line,'trust':trust,'projected_norm':pn,'hscale':hscale})
  if trust<1e-10 or rejects>=5:break
 save(y,'last')
if best is not None:
 data=dict(np.load(save(best)));met=evaluate_dfthc_angle_words(data['angle_words'],data['W'],data['H2_I']-data['W'].sum(1),m.S,m.beta,m.ref,brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
 print(json.dumps({'official_numerical_candidate':met}),flush=True)
else:met=None
report={'method':args.method,'smooth':args.smooth,'full_circuit_verified':False,'best_official_numerical_metrics':met,'trace':trace,'baseline_source':'dqi_inputs/chemistry_4033/submission_asterios_full.npz','angle_words_unchanged':True}
(ROOT/'gvqcc_repo'/('chemistry_polish_v2_'+args.method+'_result.json')).write_text(json.dumps(report,indent=2)+'\n')
