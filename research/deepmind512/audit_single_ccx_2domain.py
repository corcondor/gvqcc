#!/usr/bin/env python3
"""Exact legal-state, per-gate affine witness screening for paid CCX, across all V8 banks.
Does not alter any circuit or claim global optimality. All 2438 input samples per bank
(two physical boundary states); HMR resets and conditional CZ are tracked separately.
"""
import io,zipfile,sys,json,hashlib,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent/'GVQCC_JOINT_RANK_20261123'))
from native_kmb import NativeKMB,Op
from verify_joint import pack,basis_of,echelon_reduce
SRC=Path(__file__).parent/'public_3357.zip'

def scan():
 with zipfile.ZipFile(SRC) as z:
  with np.load(io.BytesIO(z.read('dfthcsos/submission.npz'))) as a:w=a['angle_words'].astype(np.uint8)
  n=len(w); nn=2*n; ones=(1<<nn)-1
  addr=np.tile(np.arange(n,dtype=np.uint16),2)
  selectors=[pack((addr>>i)&1) for i in range(11)]
  res=[]
  for k in range(15):
   circ=NativeKMB.parse(z.read(f'dfthcsos/angle_k_{k}.kmb'))
   prev=w[:,5*(k-1):5*k] if k else np.zeros((n,5),dtype=np.uint8)
   now=w[:,5*k:5*k+5]
   a=np.concatenate([prev,now]);st=selectors+[0]*117
   for j in range(5):
    for b in range(7):st[11+7*j+b]=pack((a[:,j]>>b)&1)
   counts={'all_ccx':0,'scratch_ccx':0,'word_ccx':0,'affine_replacable':0,'scratch_affine':0,'word_affine':0,'null_product':0,'per_epoch_affine':0}
   witnesses=[];first_hmr=None;times=[]
   limit=next(i for i,op in enumerate(circ.ops) if (op.raw & 127)==80)
   for ix,op in enumerate(circ.ops[:limit]):
    typ=op.raw&127;q=op.wires
    if typ==49:
     counts['all_ccx']+=1
     if q[-1]>=46:counts['scratch_ccx']+=1
     else:counts['word_ccx']+=1
     p=st[q[0]]&st[q[1]]
     if not p:
      counts['null_product']+=1
      witnesses.append({'index':ix,'wires':list(q),'kind':'null'})
     elif len(witnesses)<200:
      b=basis_of([st[i] for i in range(128) if i!=q[-1]]+[ones]);rem,mask=echelon_reduce(b,p)
      if rem==0:
       counts['affine_replacable']+=1
       if q[-1]>=46:counts['scratch_affine']+=1
       else:counts['word_affine']+=1
       wires=[i for i in range(128) if i!=q[-1]]
       chosen=[int(v) for j,v in enumerate(wires) if mask>>j&1]
       witnesses.append({'index':ix,'wires':list(q),'kind':'affine','cx_sources':chosen,'xor1':bool(mask>>len(wires)&1)})
     st[q[-1]] ^= p
    elif typ==33:st[q[-1]]^=st[q[0]]
    elif typ==17:st[q[0]]^=ones
    elif typ==160:pass
    else:raise ValueError((k,ix,op))
   first_hmr=limit
   print('BANK',k,counts,'first_hmr',first_hmr,flush=True)
   res.append({'k':k,'counts':counts,'first_hmr':first_hmr,'witnesses':witnesses})
  out={'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'method':'GF2 reachability affine witnesses all 2438 domain states, current all available wires (excluding target), premeasurement and postmeasurement per gate','results':res}
  (SRC.parent/'ccx_all2438_affine_scan.json').write_text(json.dumps(out,indent=2))
  return res
if __name__=='__main__':scan()
