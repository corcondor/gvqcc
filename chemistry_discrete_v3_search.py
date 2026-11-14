"""Bounded exact-angle word search with official fixed reference and cached pairs."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import argparse,copy,json,time,numpy as np
from pathlib import Path
from scipy.optimize import linear_sum_assignment,minimize
from inverse_v2_chemistry_refit import FixedAngles
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors,evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'gvqcc_repo';start=time.monotonic()
p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=360);args=p.parse_args()
base=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz'));m=FixedAngles(base)
w=base['W'];ii=base['H2_I'];d=ii-w.sum(1);N=m.N;R=m.R;B=m.B;C=w.shape[-1];words=base['angle_words'];edges=base['tree_edges'];theta=np.pi*words/128;step=np.pi/128
u=reconstruct_u_vectors(words/128,edges);u/=np.linalg.norm(u,axis=1)[:,None];utwo=u[N:];one=u[:N]
X=np.einsum('rbc,rbpq->rcpq',w,m.outer.reshape(R,B,N,N),optimize=True);hp=m.hbase-np.einsum('rc,rcpq->pq',d,X)
eig,vec=np.linalg.eigh(hp);rr,cc=linear_sum_assignment(-abs(one@vec));match=np.empty(N,int);match[rr]=cc
qrec=np.einsum('j,jp,jq->pq',eig[match],one,one,optimize=True);E=qrec-hp;evweights=np.empty(N);evweights[match]=np.einsum('jp,pq,jq->j',one,E,one,optimize=True)
ae1=2*((vec*evweights)@vec.T-E);sgn=(vec*np.sign(eig))@vec.T
packed=np.r_[w.ravel(),ii.ravel()];f,_,con,_,met=m.evaluate(packed,C,smooth=0);gap=met['gap'];lam=met['Lambda_smooth'];mu=np.array([.00020490204278176348,4.157669356168666,.05637299652286543]);tol=.02
A=(gap/f)*sgn+((lam-gap)/f)*(sgn-np.eye(N))+mu[0]/tol**2*ae1-mu[2]/.01*(sgn-np.eye(N))
hcoef=np.einsum('rbc,rc->rb',w,d).ravel();grad=np.zeros_like(u);grad[N:]=-2*hcoef[:,None]*(utwo@A.T);grad[:N]=4*eig[match,None]*(one@E.T)*mu[0]/tol**2
# The symmetric pair target is constant across every discrete candidate.
rows,cols=m.rows,m.cols;scale=m.scale
T=m.ref['tei'][rows[:,None],cols[:,None],rows[None,:],cols[None,:]].copy();sl=m.S[rows,cols];ident=(rows==cols).astype(float);T+=.5*(np.outer(sl,ident)+np.outer(ident,sl));T*=scale[:,None]*scale[None,:]
xpair=np.einsum('rbc,rbp->rcp',w,m.V.reshape(R,B,-1),optimize=True).reshape(-1,len(rows));residual=xpair.T@xpair-T;proj=m.V@residual
K=np.einsum('rbc,rcp->rbp',m.P0,proj.reshape(R,B,-1),optimize=True).reshape(R*B,-1)
Kfull=np.zeros((R*B,N,N));Kfull[:,rows,cols]=K/scale;Kfull[:,cols,rows]=K/scale
grad[N:]+=8*np.einsum('bpq,bq->bp',Kfull,utwo)*mu[1]/tol**2
# Reverse differentiation of the exact ordered Givens tree.
state=np.zeros_like(u);state[:,0]=1;pre=[]
for j,(a,b) in enumerate(edges):
 aa=state[:,a].copy();bb=state[:,b].copy();pre.append((aa,bb));co=np.cos(theta[:,j]);si=np.sin(theta[:,j]);state[:,a]=co*aa-si*bb;state[:,b]=si*aa+co*bb
gtheta=np.zeros_like(theta);adj=grad.copy()
for j in range(len(edges)-1,-1,-1):
 a,b=edges[j];aa,bb=pre[j];co=np.cos(theta[:,j]);si=np.sin(theta[:,j]);ga=adj[:,a].copy();gb=adj[:,b].copy();gtheta[:,j]=ga*(-si*aa-co*bb)+gb*(co*aa-si*bb);adj[:,a]=co*ga+si*gb;adj[:,b]=-si*ga+co*gb
masks=[1]
for b in range(11):masks.extend([1<<(b+1),1^(1<<(b+1))])
for a in range(11):
 for b in range(a+1,11):masks.extend([(1<<(a+1))^(1<<(b+1)),1^(1<<(a+1))^(1<<(b+1))])
masks=np.array(masks,dtype=np.uint16);codes=1|(np.arange(len(words),dtype=np.uint16)<<1)
flip=np.bitwise_and(masks[:,None],codes[None,:]);flip=((flip[:,:,None]>>np.arange(12))&1).sum(axis=2)%2
score=flip@(gtheta*np.where(words%2==0,1.,-1.)*step)
affine=[]
for flat in np.argsort(score,axis=None)[:12]:
 k,j=np.unravel_index(flat,score.shape);affine.append({'kind':'affine_lsb_xor','angle':int(j),'mask':int(masks[k]),'num_words':int(flip[k].sum()),'predicted_lagrangian_change':float(score[k,j])})
singles=[]
for flat in np.argsort(-abs(gtheta),axis=None)[:12]:
 a,j=np.unravel_index(flat,gtheta.shape);delta=-1 if gtheta[a,j]>0 else 1;singles.append({'kind':'single_word','row':int(a),'angle':int(j),'delta':delta,'predicted_lagrangian_change':-float(abs(gtheta[a,j])*step)})
np.savez_compressed(OUT/'chemistry_discrete_v3_gradient.npz',angle_gradient_radians=gtheta,affine_masks=masks,affine_score=score)
ranking={'baseline':met,'mu':mu.tolist(),'affine_candidates':affine,'single_candidates':singles,'seconds':time.monotonic()-start,'ranking_is_first_order_heuristic':True,'affine_template_count':int(score.size)}
(OUT/'chemistry_discrete_v3_ranking.json').write_text(json.dumps(ranking,indent=2)+'\n');print(json.dumps({'ranking':ranking}),flush=True)

def rebuild(data):
 mm=copy.copy(m);mm.base=data;uu=reconstruct_u_vectors(data['angle_words']/128,edges);uu/=np.linalg.norm(uu,axis=1)[:,None];mm.one=uu[:N];mm.outer=np.einsum('ip,iq->ipq',uu[N:],uu[N:]);mm.V=mm.outer[:,rows,cols]*scale;mm.G=mm.V@mm.V.T;mm.G4=mm.G.reshape(R,B,R,B).transpose(0,2,1,3);mm.P0=data['W']@data['W'].transpose(0,2,1);xp=np.einsum('rbc,rbp->rcp',data['W'],mm.V.reshape(R,B,-1),optimize=True).reshape(-1,len(rows));res=xp.T@xp-T;mm.e20=float(np.sum(res*res));pj=mm.V@res;mm.A=np.array([pj[r*B:(r+1)*B]@mm.V[r*B:(r+1)*B].T for r in range(R)]);mm.calls=0;return mm

def make_data(proposal):
 data=dict(base);ww=words.copy()
 if proposal['kind']=='affine_lsb_xor':
  hit=np.array([int(int(proposal['mask'])&int(code)).bit_count()%2 for code in codes],dtype=bool);ww[hit,proposal['angle']]^=1
 else:ww[proposal['row'],proposal['angle']]=(int(ww[proposal['row'],proposal['angle']])+proposal['delta'])%256
 data['angle_words']=ww;return data
screens=[]
# A few independent positions are enough for this bounded first screen.
chosen=[];positions=set()
for q in affine:
 if q['angle'] not in positions:chosen.append(q);positions.add(q['angle'])
 if len(chosen)>=4:break
positions=set()
for q in singles:
 key=(q['row'],q['angle'])
 if key not in positions:chosen.append(q);positions.add(key)
 if len(positions)>=6:break
for idx,q in enumerate(chosen):
 if time.monotonic()-start>args.seconds*.60:break
 data=make_data(q);mm=rebuild(data);vv=mm.evaluate(packed,C,smooth=0);row={**q,'index':idx,'metrics_before_refit':vv[-1],'seconds':time.monotonic()-start};screens.append(row);print(json.dumps({'screen':row}),flush=True)
 # Keep exact updated vector/cache initializers for the best few candidates.
 np.savez_compressed(OUT/f'chemistry_discrete_v3_screen_{idx}.npz',**data)
(OUT/'chemistry_discrete_v3_screen.json').write_text(json.dumps({'candidates':screens,'baseline':met,'seconds':time.monotonic()-start},indent=2)+'\n')
