"""Bounded Newton refit to the official error/gap boundary for discrete tables."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import time,json,numpy as np
from pathlib import Path
from inverse_v2_chemistry_refit import FixedAngles
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'gvqcc_repo';base=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz'));reports=[];start=time.monotonic()
for idx in (1,5,6):
 p=OUT/f'chemistry_discrete_v3_candidate_{idx}.npz'
 if not p.exists():continue
 data=dict(base);data.update(dict(np.load(p)));m=FixedAngles(data);w=data['W'];ii=data['H2_I'];n=w.size;d=ii-w.sum(1);y=np.r_[w.ravel(),d.ravel()];C=w.shape[-1]
 def original(z):
  ww=z[:n].reshape(w.shape);dd=z[n:].reshape(d.shape);return np.r_[ww.ravel(),(dd+ww.sum(1)).ravel()]
 def ev(z):
  f,g,c,J,v=m.evaluate(original(z),C,smooth=0)
  ratio=(.01999998/.019999995)**2;c[:2]=(c[:2]+1)*ratio-1;J[:2]*=ratio;c[2]+=(3.914898005-3.91489802)/.01
  for row in J:row[:n]=(row[:n].reshape(w.shape)+row[n:].reshape(ii.shape)[:,None,:]).ravel()
  return f,c,J,v
 def valid(v):return v['error1']<=.02 and v['error2']<=.02 and v['gap']>3.914898 and v['Lambda_smooth']>49
 f,c,J,v=ev(y);best=y.copy() if valid(v) else None;bestf=f if best is not None else float('inf');trace=[];scale=np.linalg.norm(J,axis=1)
 for it in range(30):
  f,c,J,v=ev(y);Jn=J/scale[:,None];cn=c/scale
  if valid(v) and f<bestf:best=y.copy();bestf=f
  trace.append({'iteration':it,'metrics':v,'constraints':c.tolist()})
  if max(abs(c))<1e-8:break
  step=-Jn.T@np.linalg.lstsq(Jn@Jn.T,cn,rcond=1e-12)[0]
  residual=np.linalg.norm(cn)
  accepted=False
  for ls in range(16):
   yt=y+(.5**ls)*step;ft,ct,jt,vt=ev(yt)
   if np.linalg.norm(ct/scale)<residual:
    y=yt;accepted=True;break
  if not accepted:break
 yy=best if best is not None else y;xx=original(yy);data['W']=xx[:n].reshape(w.shape);data['H2_I']=xx[n:].reshape(ii.shape)
 exact=evaluate_dfthc_angle_words(data['angle_words'],data['W'],data['H2_I']-data['W'].sum(1),m.S,m.beta,m.ref,brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
 ok=bool(exact['error_1']<=.02 and exact['error_2']<=.02 and exact['E_gap']>3.914898 and exact['Lambda']>49 and exact['gap_in_domain'])
 target=OUT/f'chemistry_discrete_v3_repaired_{idx}.npz';np.savez_compressed(target,angle_words=data['angle_words'],W=data['W'],H2_I=data['H2_I'])
 row={'index':idx,'official_numerical_metrics':exact,'numerically_valid':ok,'improves_lambda_under_unchanged_loader_assumption':ok and exact['lambda_eff']<46.90658950862355,'changed_words':int(np.count_nonzero(data['angle_words']!=base['angle_words'])),'path':str(target.relative_to(ROOT)),'trace':trace,'seconds':time.monotonic()-start,'full_circuit_verified':False};reports.append(row);print(json.dumps(row),flush=True)
(OUT/'chemistry_discrete_v3_repair_results.json').write_text(json.dumps({'results':reports,'seconds':time.monotonic()-start},indent=2)+'\n')
