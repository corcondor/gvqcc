#!/usr/bin/env python3
"""Test explicitly allowed constant phase using X-Z_POW-X on clean q21.
The official target global phase is retained; this is a real circuit phase.
"""
import json,pathlib,time,math
import numpy as np
from invsqrt_structural_search import read_basis,solve,SCALE,MAX
p=pathlib.Path('invsqrt_structural_work');start=time.time();desc,bits,idx,e,tol=read_basis();B=bits[idx].T.copy();inp=np.load(p/'search_inputs.npz');active=inp['active'];basecoef=inp['basecoef'];new=np.ones(MAX,dtype=np.uint8);qidx=next(i for i,d in enumerate(desc) if d['kind']=='snapshot' and d['line']==7705 and d['qubit']==21);assert not bits[qidx].any();results=[]
for drop in [(),(16,),(16,19),(16,22)]:
 rr=solve(B,e,tol,active,dropped=[(j,-float(basecoef[j])) for j in drop],new=new,maxiter=15);n=34-len(drop);row={'drop':drop,'new_basis':'constant1','generic_rotations':n,'result':rr}
 if rr and rr['margin_scaled']>0:
  eps=np.pi*rr['margin_scaled']*SCALE/n;row['rotation_toffoli_equiv']=n*(.56*np.log2(1/eps)+5.3)/4
 print(json.dumps({'drop':drop,'margin':None if not rr else rr['margin_scaled'],'cost':row.get('rotation_toffoli_equiv')}),flush=True);results.append(row)
 (p/'constant_results.json').write_text(json.dumps({'experiments':results,'elapsed_seconds':time.time()-start},indent=2))
print('DONE',time.time()-start,flush=True)
