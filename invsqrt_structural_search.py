#!/usr/bin/env python3
"""Structural phase-basis search for e46 invsqrt, distinct from fixed-basis LP.
The current arithmetic is unchanged. A new Boolean parity is computed using
CX, phase-rotated, and uncomputed. A cutting-plane LP refits existing rotations
plus new bases. Complete-domain deterministic checks precede native validation.
"""
import json,pathlib,time,hashlib,argparse
from fractions import Fraction
import numpy as np
from scipy.optimize import linprog

MAX=3133452; SCALE=1e-11

def read_basis():
 p=pathlib.Path('invsqrt_structural_work');meta=json.loads((p/'basis.json').read_text());desc=meta['basis'];nw=(MAX+63)//64
 packed=np.memmap(p/'basis.u64',mode='r',dtype='<u8',shape=(len(desc),nw))
 bits=np.unpackbits(packed.view('u1'),axis=1,bitorder='little')[:,:MAX]
 base=np.zeros(MAX,dtype=np.longdouble)
 for i,d in enumerate(desc):
  if d['kind']=='rotation':
   f=Fraction(d['half_turns'])/2;c=np.longdouble(f.numerator)/np.longdouble(f.denominator);base+=bits[i]*c
  elif d['kind']=='phase_parity':base+=bits[i]*np.longdouble(.5)
 xs=np.arange(1,MAX+1,dtype=np.longdouble);target=1/np.sqrt(xs);tol=target/2**24
 err=base-target;err-=np.rint(err)
 idx=[i for i,d in enumerate(desc) if d['kind']=='rotation' and d['class']=='rotation']
 print(json.dumps({'baseline_margin':float(np.min(tol-abs(err))),'max_ratio':float(np.max(abs(err)/tol)),'worst_x':int(np.argmax(abs(err)/tol))+1,'rotations':len(idx),'min_tolerance':float(tol[-1])}),flush=True)
 return desc,bits,idx,np.array(err/SCALE,dtype=float),np.array(tol/SCALE,dtype=float)

def solve(B,e,tol,active,dropped=(),new=None,maxiter=12):
 # B is n-by-r uint8, adjustments in units SCALE. min margin / SCALE maximized.
 r=B.shape[1];nnew=0 if new is None else (1 if new.ndim==1 else new.shape[1]);bb=B if new is None else np.column_stack((B,new))
 bounds=[(-1e6,1e6)]*(r+nnew)+[(None,None)]
 for j,value in dropped:bounds[j]=(value,value)
 active=np.unique(active)
 result=None
 for it in range(maxiter):
  A=np.asarray(bb[active],dtype=float);A=np.column_stack((np.vstack((A,-A)),np.ones(2*len(active))));rhs=np.r_[tol[active]-e[active],tol[active]+e[active]]
  objective=np.zeros(r+nnew+1);objective[-1]=-1
  res=linprog(objective,A_ub=A,b_ub=rhs,bounds=bounds,method='highs',options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
  if not res.success:return None
  coeff=res.x[:-1]
  error=e+bb@coeff
  margin=tol-np.abs(error);worst=np.argpartition(margin,min(63,len(margin)-1))[:64]
  real=float(margin.min()); gap=float(res.x[-1]-real)
  result={'lp_margin_scaled':float(res.x[-1]),'margin_scaled':real,'iterations':it+1,'active_count':len(active),'coeff_scaled':coeff.tolist(),'max_error_ratio':float(np.max(abs(error)/tol)),'worst_x':int(np.argmax(abs(error)/tol))+1,'gap_scaled':gap}
  if gap<1e-7:return result
  active=np.unique(np.r_[active,worst])
 return result

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--mode',default='initial');args=parser.parse_args();start=time.time()
 desc,bits,idx,e,tol=read_basis();B=bits[idx].T.copy();basecoef=np.array([float(Fraction(desc[i]['half_turns'])/2)/SCALE for i in idx]);margin=tol-abs(e)
 # Fixed deterministic coarse design + exact-domain tight points, independent of verification seed/hash.
 active=np.unique(np.r_[np.arange(1,2048),np.linspace(0,MAX-1,2048,dtype=int),np.argpartition(margin,2048)[:2048],np.argpartition(margin[:100000],256)[:256]])
 baseline={'source':'e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6','margin_turns':float(margin.min()*SCALE),'rotations':len(idx),'max_ratio':float(np.max(abs(e)/tol)),'active_size':len(active)}
 path=pathlib.Path('invsqrt_structural_work');np.savez(path/'search_inputs.npz',idx=idx,e=e,tol=tol,active=active,basecoef=basecoef)
 # Search an actual new parity at one of three legal insertion snapshots.
 # Cheap screening uses least-squares projection on the active points. Refitting
 # is done later with the actual minimax objective and full-domain separator.
 candidates=[];seen=set();As=np.asarray(B[active],dtype=float);y=-e[active]
 # Tight points weighted; constant is only provided if an existing qubit is 1.
 weight=1/np.maximum(tol[active],1.0); Aw=As*weight[:,None];yw=y*weight
 coef=np.linalg.lstsq(Aw,yw,rcond=None)[0];resid=yw-Aw@coef
 for line in (7705,8075,8189):
  ss=[i for i,d in enumerate(desc) if d['kind']=='snapshot' and d['line']==line]
  arr=bits[ss][:,active];Q,R=np.linalg.qr(Aw,mode='reduced')
  for a in range(46):
   for b in range(a,46):
    v=arr[a] if a==b else arr[a]^arr[b]
    key=np.packbits(v,bitorder='little').tobytes()
    if key in seen or not v.any():continue
    seen.add(key);vw=v*weight;vp=vw-Q@(Q.T@vw);norm=vp@vp
    if norm<1e-10:continue
    corr=float((vp@resid)**2/norm)
    candidates.append({'line':line,'qubits':[a] if a==b else [a,b],'basis_indices':[ss[a]] if a==b else [ss[a],ss[b]],'ls_improvement':corr})
 candidates.sort(key=lambda c:-c['ls_improvement']);(path/'screen_candidates.json').write_text(json.dumps(candidates[:100],indent=2));print(json.dumps({'unique_candidate_count':len(candidates),'top':candidates[:5],'elapsed':time.time()-start}),flush=True)
 output={'baseline':baseline,'screening_candidate_count':len(candidates),'experiments':[]}
 # One new parity with unrestricted refit, then one/two smallest rotations removed.
 # Reuse constraints from full-domain extrema of existing solution for all candidates.
 for ci,c in enumerate(candidates[:10]):
  new=bits[c['basis_indices'][0]].copy()
  for j in c['basis_indices'][1:]:new^=bits[j]
  result=solve(B,e,tol,active,new=new)
  row={'candidate':c,'kind':'add_one','result':result};output['experiments'].append(row)
  print(json.dumps({'candidate':ci,'kind':'add_one','margin':None if result is None else result['margin_scaled'],'iterations':None if result is None else result['iterations']}),flush=True)
  if result:
   coeff=result['coeff_scaled'];nrot=len(idx)+1
   eps=np.pi*max(result['margin_scaled']*SCALE,1e-300)/nrot
   row['predicted_rotation_toffoli_eq']=nrot*(.56*np.log2(1/eps)+5.3)/4
  # Only low-angle deletes are numerically plausible without wholesale datapath rewrite.
  if ci<4:
   for drop in (tuple(np.argsort(abs(basecoef))[:1]),tuple(np.argsort(abs(basecoef))[:2])):
    dropped=[(int(j),-float(basecoef[j])) for j in drop]; rr=solve(B,e,tol,active,dropped=dropped,new=new)
    rrrow={'candidate':c,'kind':'replace_'+str(len(drop)),'drop_rotation_indices':list(map(int,drop)),'result':rr};output['experiments'].append(rrrow)
    print(json.dumps({'candidate':ci,'kind':rrrow['kind'],'margin':None if rr is None else rr['margin_scaled']}),flush=True)
  (path/'results.json').write_text(json.dumps(output,indent=2))
 print(json.dumps({'elapsed_seconds':time.time()-start,'output':str(path/'results.json')}),flush=True)
if __name__=='__main__':main()
