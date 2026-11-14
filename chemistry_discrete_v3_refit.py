"""Curvature-aware bounded discrete screen and short numerical refits."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import json,runpy,sys,time,numpy as np
from pathlib import Path
from scipy.optimize import minimize
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'gvqcc_repo';start=time.monotonic();oldargv=sys.argv;sys.argv=[str(OUT/'chemistry_discrete_v3_search.py'),'--seconds','240'];env=runpy.run_path(sys.argv[0]);sys.argv=oldargv
for key in ('m','base','w','ii','d','N','R','B','C','words','edges','theta','step','u','utwo','rows','cols','scale','gtheta','hcoef','mu','tol','pre','rebuild','make_data','packed','met','codes'):
 globals()[key]=env[key]
Yp=np.einsum('rbc,rcp->rbp',m.P0,m.V.reshape(R,B,-1),optimize=True).reshape(R*B,-1);Yn=np.sum(Yp*Yp,axis=1);Ym=np.zeros((R*B,N,N));Ym[:,rows,cols]=Yp/scale;Ym[:,cols,rows]=Yp/scale;Yu=np.einsum('bpq,bq->bp',Ym,utwo);qdiag=np.zeros_like(gtheta)
for j,(a,b) in enumerate(edges):
 aa,bb=pre[j];co=np.cos(theta[:,j]);si=np.sin(theta[:,j]);du=np.zeros_like(u);du[:,a]=-si*aa-co*bb;du[:,b]=co*aa-si*bb
 for k in range(j+1,len(edges)):
  pa,ch=edges[k];co=np.cos(theta[:,k]);si=np.sin(theta[:,k]);x=du[:,pa].copy();y=du[:,ch].copy();du[:,pa]=co*x-si*y;du[:,ch]=si*x+co*y
 normdu=np.sum(du[N:]**2,axis=1);dots=np.einsum('bp,bp->b',du[N:],Yu)
 qdiag[N:,j]=mu[1]/tol**2*(4*normdu*Yn+8*dots*dots)+mu[0]/tol**2*2*hcoef*hcoef*normdu
single_score=-abs(gtheta)*step+qdiag*step*step;single_score[:N]=np.inf
candidates=[];seen=set()
for flat in np.argsort(single_score,axis=None):
 a,j=np.unravel_index(flat,single_score.shape)
 if len(candidates)>=6:break
 if single_score[a,j]>=-1e-9:break
 if (a,j) in seen:continue
 seen.add((a,j));candidates.append({'kind':'single_word','row':int(a),'angle':int(j),'delta':-1 if gtheta[a,j]>0 else 1,'quadratic_proxy':float(single_score[a,j])})
hmasks=np.array([sum((1<<(b+8)) for b in range(4) if k&(1<<b)) for k in range(1,16)],np.uint16);hits=np.array([[int(int(mask)&int(code)).bit_count()%2 for code in codes] for mask in hmasks]);ascore=hits@(gtheta*np.where(words%2==0,1.,-1.)*step+qdiag*step*step)
for flat in np.argsort(ascore,axis=None)[:4]:
 k,j=np.unravel_index(flat,ascore.shape);candidates.append({'kind':'affine_lsb_xor','angle':int(j),'mask':int(hmasks[k]),'quadratic_proxy':float(ascore[k,j]),'num_words':int(hits[k].sum())})
for j in (65,39):candidates.append({'kind':'affine_lsb_xor','angle':j,'mask':2048,'quadratic_proxy':None,'num_words':196})
np.savez_compressed(OUT/'chemistry_discrete_v3_curvature.npz',gauss_newton_proxy=qdiag,single_score=single_score,high_address_masks=hmasks,high_address_score=ascore)
screens=[];models=[]
for idx,q in enumerate(candidates):
 data=make_data(q);mm=rebuild(data);v=mm.evaluate(packed,C,smooth=0);row={**q,'index':idx,'metrics_before_refit':v[-1],'seconds':time.monotonic()-start};screens.append(row);models.append((data,mm));print(json.dumps({'curvature_screen':row}),flush=True)
(OUT/'chemistry_discrete_v3_curvature_screen.json').write_text(json.dumps({'candidates':screens,'proxy_is_not_a_bound':True},indent=2)+'\n')
# Two best single-word candidates and one affine candidate, by exact violation.
def violation(row):
 v=row['metrics_before_refit'];return max(v['error1']/.02,v['error2']/.02,3.914898/max(v['gap'],1e-8))
selected=sorted([k for k,q in enumerate(screens) if q['kind']=='single_word'],key=lambda k:violation(screens[k]))[:2]
aff=[k for k,q in enumerate(screens) if q['kind']=='affine_lsb_xor'];selected+=sorted(aff,key=lambda k:violation(screens[k]))[:1]
results=[]
for idx in selected:
 if time.monotonic()-start>330:break
 data,mm=models[idx];n=w.size;y=np.r_[w.ravel(),d.ravel()];latest=y.copy();fit_start=time.monotonic();trace=[];best=None;bestf=float('inf');lag=mu.copy()
 def orig(yy):
  ww=yy[:n].reshape(w.shape);dd=yy[n:].reshape(d.shape);return np.r_[ww.ravel(),(dd+ww.sum(1)).ravel()]
 def tr(g):
  z=g.copy();z[:n]=(z[:n].reshape(w.shape)+z[n:].reshape(ii.shape)[:,None,:]).ravel();return z
 def ev(yy,smooth=1e-7):
  f,g,c,J,v=mm.evaluate(orig(yy),C,smooth=smooth);ratio=(.01999998/.019999999)**2;c[:2]=(c[:2]+1)*ratio-1;J[:2]*=ratio;c[2]+=(3.914898001-3.91489802)/.01;return f,tr(g),c,np.array([tr(z) for z in J]),v
 class Budget(Exception):pass
 for outer,rho in enumerate((10.,100.,1000.,10000.)):
  def fun(yy):
   if time.monotonic()-fit_start>65:raise Budget()
   f,g,c,J,v=ev(yy);t=np.maximum(0,lag+rho*c);return f+(t@t-lag@lag)/(2*rho),g+t@J
  def cb(yy):
   global latest
   latest=yy.copy()
  try:r=minimize(fun,y,jac=True,method='L-BFGS-B',callback=cb,options={'maxiter':60,'maxcor':10,'maxls':30,'ftol':1e-13,'gtol':1e-8});y=r.x;term=str(r.message)
  except Budget:y=latest;term='65-second budget'
  f,g,c,J,v=ev(y,smooth=0);lag=np.maximum(0,lag+rho*c);trace.append({'outer':outer,'rho':rho,'metrics':v,'termination':term,'seconds':time.monotonic()-fit_start});print(json.dumps({'refit':idx,**trace[-1]}),flush=True)
  if v['error1']<=.02 and v['error2']<=.02 and v['gap']>3.914898 and v['Lambda_smooth']>49 and f<bestf:best=y.copy();bestf=f
  if time.monotonic()-fit_start>65:break
 final_y=best if best is not None else y;xx=orig(final_y);resultdata=dict(data);resultdata['W']=xx[:n].reshape(w.shape);resultdata['H2_I']=xx[n:].reshape(ii.shape)
 from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
 from dfthcsos.scoreinfra.reference import UPPER_ENERGY
 official=evaluate_dfthc_angle_words(resultdata['angle_words'],resultdata['W'],resultdata['H2_I']-resultdata['W'].sum(1),mm.S,mm.beta,mm.ref,brot=8,tree_edges=resultdata['tree_edges'],energy_upper=UPPER_ENERGY)
 path=OUT/f'chemistry_discrete_v3_candidate_{idx}.npz';np.savez_compressed(path,angle_words=resultdata['angle_words'],W=resultdata['W'],H2_I=resultdata['H2_I'])
 valid=bool(official['error_1']<=.02 and official['error_2']<=.02 and official['E_gap']>3.914898 and official['Lambda']>49 and official['gap_in_domain'])
 result={'proposal':screens[idx],'trace':trace,'official_numerical_metrics':official,'numerically_valid':valid,'improves_lambda':valid and official['lambda_eff']<met['lambda_eff_smooth'],'candidate_compact_path':str(path.relative_to(ROOT)),'loader_verified':False,'full_circuit_verified':False,'loader_cost_assumption':'unchanged4033 for affine-LSB only; single-word loader cost not established'};results.append(result);print(json.dumps({'final_refit':result}),flush=True)
(OUT/'chemistry_discrete_v3_results.json').write_text(json.dumps({'baseline':met,'exact_screen_count':len(screens),'results':results,'seconds':time.monotonic()-start,'source_user_candidate_available':False},indent=2)+'\n')
