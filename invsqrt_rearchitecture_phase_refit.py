#!/usr/bin/env python3
import pathlib,json,time,sys
from fractions import Fraction
import numpy as np
from scipy.optimize import linprog
MAX=3133452; SCALE=1e-11

def load(p):
 meta=json.loads((p/'basis.json').read_text());ds=meta['basis'];nw=(MAX+63)//64
 pp=np.memmap(p/'basis.u64',mode='r',dtype='<u8',shape=(len(ds),nw))
 inds=[i for i,d in enumerate(ds) if d['kind'] in ('rotation','phase_parity')]
 bits=np.unpackbits(np.asarray(pp[inds]).view('u1'),axis=1,bitorder='little')[:,:MAX]
 dd=[ds[i] for i in inds]
 phase=np.zeros(MAX,dtype=np.longdouble)
 for b,d in zip(bits,dd):
  if d['kind']=='rotation':
   f=Fraction(d['half_turns'])/2;a=np.longdouble(f.numerator)/f.denominator
  else:a=np.longdouble(.5)
  phase+=a*b
 x=np.arange(1,MAX+1,dtype=np.longdouble);target=1/np.sqrt(x);tol=target/2**24;phase-=target;phase-=np.rint(phase)
 ix=[i for i,d in enumerate(dd) if d['kind']=='rotation' and d['class']=='rotation']
 B=bits[ix].T.copy();e=np.array(phase/SCALE,dtype=float);t=np.array(tol/SCALE,dtype=float)
 return B,e,t

def dot(B,coeff):
 out=np.empty(len(B))
 for i in range(0,len(B),32768):out[i:i+32768]=B[i:i+32768]@coeff
 return out

def solve(B,e,t):
 margin=t-abs(e);active=np.unique(np.r_[np.arange(2048),np.linspace(0,MAX-1,2048,dtype=int),np.argpartition(margin,1024)[:1024]])
 objective=np.zeros(B.shape[1]+1);objective[-1]=-1
 for it in range(30):
  b=np.asarray(B[active],dtype=float);A=np.column_stack((np.vstack((b,-b)),np.ones(2*len(active))))
  res=linprog(objective,A_ub=A,b_ub=np.r_[t[active]-e[active],t[active]+e[active]],bounds=[(-1e6,1e6)]*B.shape[1]+[(None,None)],method='highs',options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
  if not res.success:return {'success':False,'message':res.message}
  err=e+dot(B,res.x[:-1]);m=t-abs(err);worst=np.argpartition(m,128)[:128]
  mn=float(m.min());gap=float(res.x[-1]-mn)
  row=dict(success=True,lp_margin_turns=float(res.x[-1]*SCALE),actual_min_margin_turns=mn*SCALE,max_error_ratio=float(np.max(abs(err)/t)),worst_x=int(np.argmax(abs(err)/t))+1,gap_turns=gap*SCALE,iterations=it+1,coeff_adjustment_scaled=res.x[:-1].tolist())
  print(json.dumps({k:v for k,v in row.items() if k!='coeff_adjustment_scaled'}),flush=True)
  if gap<1e-7: return row
  active=np.unique(np.r_[active,worst])
 return row

if __name__ == '__main__':
 start=time.monotonic();out=[]
 names=sys.argv[1:] or ['drop1','drop2','drop3']
 for name in names:
  p=pathlib.Path('invsqrt_rearchitecture_phase_work')/name
  B,e,t=load(p)
  row={'intervention':name,'baseline_angles_margin_turns':float(np.min(t-abs(e))*SCALE),'rotations':B.shape[1]}
  print(json.dumps(row),flush=True);row['refit']=solve(B,e,t)
  out.append(row)
  pathlib.Path('gvqcc_repo/invsqrt_rearchitecture_'+('_'.join(names))+'_results.json').write_text(json.dumps({'scope':'numerical feasibility only; not implementable circuit; HMR/deferred cleanup invalid after intervention','elapsed_seconds':time.monotonic()-start,'records':out},indent=2))
  del B,e,t
