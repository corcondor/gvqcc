"""Exact-L1, fixed-angle proximal SQP for GVQCC chemistry.

The nonsmooth derivative of sum_b |W| is handled by soft thresholding, while
three active official constraints are solved in a three-dimensional dual.
No angle table or official verifier is modified. Numerical acceptance is
independently checked by the official numerical evaluator after optimization.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1')
import numpy as np,json,time,argparse
from pathlib import Path
from scipy.optimize import nnls
from chem_next_fixed_angles import FastFixedAngles as FixedAngles
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=600);p.add_argument('--start',type=Path);p.add_argument('--label',default='prox');p.add_argument('--debug',action='store_true');p.add_argument('--tight',action='store_true');p.add_argument('--schur',action='store_true');p.add_argument('--metric',action='store_true');p.add_argument('--overlap-graph',action='store_true');args=p.parse_args()
if args.overlap_graph and not args.metric:p.error('--overlap-graph requires --metric')
if not args.start:raise ValueError('--start required for exact public4030 source')
base=dict(np.load(args.start,allow_pickle=False));data=base
assert base['W'].shape==(8,143,44)
assert __import__('hashlib').sha256(base['angle_words'].astype(np.uint8).tobytes()).hexdigest()=='8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea'
m=FixedAngles(base);shape=base['W'].shape;ishape=base['H2_I'].shape;n=base['W'].size;C=shape[2]
y=np.r_[data['W'].ravel(),(data['H2_I']-data['W'].sum(1)).ravel()]

def orig(yy):
 w=yy[:n].reshape(shape);d=yy[n:].reshape(ishape)
 return np.r_[w.ravel(),(d+w.sum(1)).ravel()]
def transform(a):
 a=a.copy();a[:n]=(a[:n].reshape(shape)+a[n:].reshape(ishape)[:,None,:]).ravel();return a
# A fixed 3D Schur complement preserves the inertia around near-zero hprime
# eigenvalues, avoiding |eigenvalue| kinks while leaving the other directions free.
if args.schur:
 w=base['W'];d=base['H2_I']-w.sum(1)
 X=np.einsum('rbc,rbpq->rcpq',w,m.outer.reshape(m.R,m.B,m.N,m.N),optimize=True)
 hp=m.hbase-np.einsum('rc,rcpq->pq',d,X)
 evals,evec=np.linalg.eigh(hp);small=np.argsort(abs(evals))[:3];large=np.array([k for k in range(m.N) if k not in small]);V0=evec[:,small];V1=evec[:,large]
 schur_target=V0.T@hp@V0;sr,sc2=np.tril_indices(3);sweights=np.where(sr==sc2,1.,np.sqrt(2.))

def ev(yy):
 f,g,c,J,met=m.evaluate(orig(yy),C,smooth=0)
 if args.tight:
  ratio=(.01999998/.0199999999)**2;c[:2]=(c[:2]+1)*ratio-1;J[:2]*=ratio;c[2]+=(3.9148980001-3.91489802)/.01
 Jn=np.array([transform(v) for v in J])
 if args.schur:
  ww=yy[:n].reshape(shape);dd=yy[n:].reshape(ishape)
  X=np.einsum('rbc,rbpq->rcpq',ww,m.outer.reshape(m.R,m.B,m.N,m.N),optimize=True)
  hp=m.hbase-np.einsum('rc,rcpq->pq',dd,X)
  A=V0.T@hp@V0;B=V0.T@hp@V1;D=V1.T@hp@V1;solve=np.linalg.solve(D,B.T)
  block=A-B@solve-schur_target;Veff=V0-V1@solve
  c=np.r_[c,block[sr,sc2]*sweights]
  extra=[]
  for i,j,weight in zip(sr,sc2,sweights):
   aa=.5*(np.outer(Veff[:,i],Veff[:,j])+np.outer(Veff[:,j],Veff[:,i]))*weight
   av=np.einsum('pq,rbpq->rb',aa,m.outer.reshape(m.R,m.B,m.N,m.N));ax=np.einsum('rb,rbc->rc',av,ww)
   extra.append(np.r_[(-av[:,:,None]*dd[:,None,:]).ravel(),(-ax).ravel()])
  Jn=np.r_[Jn,np.array(extra)]
 return f,transform(g),c,Jn,met

def feasible(mm):return mm['error1']<=.020 and mm['error2']<=.020 and mm['gap']>3.914898 and mm['Lambda_smooth']>49
prefix=Path(__file__).resolve().parent/('chem_next_public4030_'+args.label)

def save(yy,tag):
 xx=orig(yy);d=dict(base);d['W']=xx[:n].reshape(shape);d['H2_I']=xx[n:].reshape(ishape)
 out=prefix.with_name(prefix.name+'_'+tag+'.npz');np.savez_compressed(out,**d);return out
f,g,c,J,met=ev(y);sc=np.linalg.norm(J,axis=1);support=np.r_[abs(y[:n])>1e-7,np.ones(y.size-n,dtype=bool)]
mu=np.linalg.lstsq((J/sc[:,None])[:,support].T,-g[support],rcond=1e-12)[0];start=time.monotonic();trace=[];best=y.copy() if feasible(met) else None;bestf=f if best is not None else float('inf');h=.00002
print(json.dumps({'initial':met,'initial_dual':mu.tolist(),'active_w_count':int(np.count_nonzero(y[:n])),'constraint_gram_eigenvalues':np.linalg.eigvalsh((J/sc[:,None])@(J/sc[:,None]).T).tolist(),'tight':args.tight}),flush=True)

metric=np.ones_like(y)
if args.metric:
 # Diagonal of the unnormalized squared H2 residual Hessian, with
 # positive curvature surrogates for H1 and the identity coefficients.
 features=m.V.reshape(m.R,m.B,-1)
 w=base['W']; d=base['H2_I']-w.sum(1)
 terms=np.einsum('rbc,rbd->rcd',w,features,optimize=True)
 norms2=np.einsum('rcd,rcd->rc',terms,terms)
 products=np.einsum('rbd,rcd->rbc',features,terms,optimize=True)
 feature_norm2=np.einsum('rbd,rbd->rb',features,features)
 h2_diag=4*(np.diagonal(m.A,axis1=1,axis2=2)[:,:,None]+products*products
             + feature_norm2[:,:,None]*norms2[:,None,:])
 h1_diag=2*d[:,None,:]*d[:,None,:]*feature_norm2[:,:,None]
 alpha=np.abs(mu/sc)
 curvature=alpha[1]/(.02**2)*np.abs(h2_diag)+alpha[0]/(.02**2)*h1_diag
 if args.overlap_graph:
  # A high-degree feature shares curvature with many other basis directions.
  # Scale its step by the degree relative to the typical row within its group.
  overlap=features@features.swapaxes(1,2)
  norms=np.sqrt(feature_norm2)
  overlap/=norms[:,:,None]*norms[:,None,:]
  degree=np.square(overlap).sum(axis=2)
  normalized=degree/np.median(degree,axis=1)[:,None]
  curvature*=normalized[:,:,None]
  print(json.dumps({'overlap_degree_min':degree.min(),'overlap_degree_max':degree.max()}),flush=True)
 d_curvature=2*alpha[0]/(.02**2)*norms2+alpha[2]/.01
 diagonal=np.r_[curvature.ravel(),d_curvature.ravel()]
 typical=np.median(diagonal)
 metric=np.clip(typical/np.maximum(diagonal,typical*.03),.1,20.)
 print(json.dumps({'metric_min':metric.min(),'metric_median':np.median(metric),'metric_max':metric.max()}),flush=True)

def soft_qp(yy,g,J,c,h,mu,met):
 # Smooth first-order portion, excluding the W L1 terms (H2_I stays nonzero).
 xx=orig(yy);w=xx[:n].reshape(shape);ii=xx[n:].reshape(ishape)
 l1=np.sum(abs(w),axis=1)+abs(ii)
 tau=np.broadcast_to((met['gap']/met['lambda_eff_smooth']*.5*l1)[:,None,:],shape).ravel()
 gs=g.copy();gs[:n]-=tau*np.sign(yy[:n]);Jn=J/sc[:,None];cn=c/sc
 rates=h*metric
 def calc(uu):
  z=yy-rates*(gs+uu@Jn)
  threshold=rates[:n]*tau
  nxt=z.copy();nxt[:n]=np.sign(z[:n])*np.maximum(abs(z[:n])-threshold,0)
  pp=nxt-yy
  val=gs@pp+.5*((pp/rates)@pp)+tau@(abs(nxt[:n])-abs(yy[:n]))+uu@(cn+Jn@pp)
  mask=np.r_[abs(z[:n])>threshold,np.ones(yy.size-n,dtype=bool)]
  return pp,cn+Jn@pp,val,mask
 for k in range(50):
  pp,r,v,mask=calc(mu)
  if np.max(abs(r))<1e-12:break
  HH=(Jn[:,mask]*rates[mask])@Jn[:,mask].T
  step=np.linalg.lstsq(HH,r,rcond=1e-12)[0]
  for ls in range(20):
   mun=mu+step*(.5**ls);pn,rn,vn,maskn=calc(mun)
   if vn>=v-1e-14:break
  mu=mun
 return calc(mu)[0],mu,k,float(np.max(abs(calc(mu)[1])))

for it in range(1,1001):
 if time.monotonic()-start>args.seconds:break
 pp,mu,dual_iters,dual_res=soft_qp(y,g,J,c,h,mu,met)
 oldf=f;accepted=False
 for line in range(12):
  # Line interpolation to a prox point preserves exact zeros at full step.
  yt=y+pp*(.5**line)
  for corr in range(12):
   ft,gt,ct,jt,mt=ev(yt)
   if max(abs(ct[:3]))<1e-8 and (not args.schur or max(abs(ct[3:]))<1e-12):break
   face=np.r_[abs(yt[:n])>1e-7,np.ones(yt.size-n,dtype=bool)]
   jtface=jt[:,face]/sc[:,None]
   weighted=jtface*metric[face]
   correction=-weighted.T@np.linalg.lstsq(weighted@jtface.T,ct/sc,rcond=1e-12)[0]
   
   # Safeguarded normal restoration: reduce normalized constraint residual.
   residual0=np.linalg.norm(ct/sc)
   for normal_ls in range(12):
    yn=yt.copy();yn[face]+=correction*(.5**normal_ls)
    fn,gn,cn,jn,mn=ev(yn)
    if np.linalg.norm(cn/sc)<residual0:break
   else:break
   yt=yn
  ft,gt,ct,jt,mt=ev(yt)
  if args.debug and it<=2:print(json.dumps({'trial':line,'h':h,'df':ft-oldf,'c':ct.tolist(),'step_norm_after_retract':float(np.linalg.norm(yt-y))}),flush=True)
  if max(ct[:3])<2e-8 and (not args.schur or max(abs(ct[3:]))<1e-10) and (ft<oldf-1e-11 or (max(c)>2e-8 and np.linalg.norm(ct/sc)<.1*np.linalg.norm(c/sc))):
   accepted=True;break
 if accepted:
  step=yt-y; oldlag=g+mu@(J/sc[:,None]);newlag=gt+mu@(jt/sc[:,None])
  y=yt;f,g,c,J,met=ft,gt,ct,jt,mt
  # BB scaling on the fixed active support avoids artificial L1 secants.
  mask=(abs(y[:n])>1e-7)&(abs((y-step)[:n])>1e-7)&(y[:n]*(y-step)[:n]>0)
  mask=np.r_[mask,np.ones(y.size-n,dtype=bool)]
  ss=step[mask];zz=(newlag-oldlag)[mask];den=ss@zz
  hbb=((ss/metric[mask])@ss)/den if den>1e-16 else h*1.3
  h=float(np.clip(hbb,h*.5,min(h*1.6,.05)))
  if feasible(met) and f<bestf:
   best=y.copy();bestf=f;save(best,'candidate')
 else:h*=.2
 if it%5==0 or it==1 or not accepted:
  row={'iteration':it,'seconds':time.monotonic()-start,'calls':m.calls,'metrics':met,'accepted':accepted,'h':h,'line_search':line,'dual_iterations':dual_iters,'dual_residual':dual_res,'step_norm':float(np.linalg.norm(pp)),'active_w_count':int(np.count_nonzero(y[:n]))}
  trace.append(row);print(json.dumps(row),flush=True)
 if h<1e-10:break
save(y,'last');official=None
if best is not None:
 path=save(best,'candidate');data=dict(np.load(path))
 official=evaluate_dfthc_angle_words(data['angle_words'],data['W'],data['H2_I']-data['W'].sum(1),m.S,m.beta,m.ref,brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
 print(json.dumps({'official_numerical_candidate':official}),flush=True)
report={'method':'exact L1 proximal SQP','diagonal_curvature_metric':args.metric,'overlap_graph':args.overlap_graph,'official_numerical_metrics':official,'full_circuit_verified':False,'trace':trace,'baseline_source':str(args.start),'baseline_sha256':__import__('hashlib').sha256(args.start.read_bytes()).hexdigest(),'reference_loader_toffoli_perpass':4030,'reference_task_toffoli':14722,'reference_task_qubits':427,'angle_words_unchanged':True,'exact_objective':True,'seconds':time.monotonic()-start}
prefix.with_name(prefix.name+'_result.json').write_text(json.dumps(report,indent=2)+'\n')
