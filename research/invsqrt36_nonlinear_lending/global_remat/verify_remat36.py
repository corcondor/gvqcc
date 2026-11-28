#!/usr/bin/env python3
"""Independent bitpacked all-2^22 validation of global delayed materialization.
Four deterministic full-size measurement transcript families; structural theorem
is needed for arbitrarily many independent transcript assignments.
"""
from pathlib import Path
import sys,json,time,hashlib
sys.path.insert(0,str(Path(__file__).parent))
from remat36 import REFERENCE,START,STOP,OUT,construct,generate
from native_kmb import NativeKMB
N=1<<22; ALL=(1<<N)-1

def inputbit(i):
 v=((1<<(1<<i))-1)<<(1<<i)
 size=2<<(i)
 while size<N:v |= v<<size;size*=2
 return v
V=[inputbit(i) for i in range(22)]

def outcome(seed,j):
 if seed==0:return 0
 if seed==1:return ALL
 if seed==2:return V[(j*7+3)%22]
 if seed==3:return (V[(j*5+1)%22]^V[(j*11+9)%22]) ^ (ALL if (j%3==0) else 0)
 raise ValueError(seed)

class Packed:
 def __init__(self,qnum=37,initial=None,bits=None,phase=0,measure_count=0):
  self.s=list(initial if initial is not None else V+[0]*(qnum-22))
  self.c=dict(bits or {});self.phase=phase;self.stack=[];self.m=measure_count
 def run(self,ops,seed,skip_zpow=False):
  for o in ops:
   g=o.raw&127;q=o.wires
   if o.raw==0x81:
    self.stack.append(self.c.get(o.condition,0));continue
   if o.raw==0x01:
    self.stack.pop();continue
   mask=ALL
   if self.stack:
    for x in self.stack:mask &=x
   if o.raw&128:mask &= self.c.get(o.condition,0)
   if g==0x40:self.c[o.measurement]=self.c.get(o.measurement,0)&(ALL^mask)
   elif g==0x41:self.c[o.measurement]=self.c.get(o.measurement,0)|mask
   elif g==0x42:self.c[o.measurement]=self.c.get(o.measurement,0)^mask
   elif g==0x11:self.s[q[0]]^=mask
   elif g==0x21:self.s[q[1]] ^= self.s[q[0]]&mask
   elif g==0x31:self.s[q[2]] ^=self.s[q[0]] & self.s[q[1]] & mask
   elif g==0x22:
    z=(self.s[q[0]]^self.s[q[1]])&mask;self.s[q[0]]^=z;self.s[q[1]]^=z
   elif g==0x32:
    z=self.s[q[0]]&(self.s[q[1]]^self.s[q[2]])&mask;self.s[q[1]]^=z;self.s[q[2]]^=z
   elif g==0x10:self.phase^=self.s[q[0]]&mask
   elif g==0x20:self.phase^=self.s[q[0]]&self.s[q[1]]&mask
   elif g==0x30:self.phase^=self.s[q[0]]&self.s[q[1]]&self.s[q[2]]&mask
   elif g==0x00:self.phase ^= mask
   elif g==0x50:
    m=outcome(seed,self.m);self.m+=1
    self.phase ^= self.s[q[0]]&m&mask
    # HMR is unconditional in this section; reset zero in any case
    assert mask==ALL,'conditional HMR requires a different instrument model'
    self.s[q[0]]=0;self.c[o.measurement]=m
   elif g==0x12:self.s[q[0]] &= ALL^mask
   elif g==0x13:
    if not skip_zpow:raise NotImplementedError('Z_POW in the phase suffix; not handled here')
   else:raise ValueError((hex(o.raw),q))
  assert not self.stack

def verify():
 st=time.time();ref=NativeKMB.read(REFERENCE);source,cand,_=construct(ref)
 assert NativeKMB.read(OUT/'rematerialized_36Q_segment_ONLY.kmb').ops==cand
 cases=[]
 for seed in range(4):
  p=Packed();p.run(ref.ops[:START],seed,skip_zpow=True)
  assert p.s[34]==0
  compressed=p.s[:34]+[p.s[36],p.s[35]]
  orig=Packed(initial=p.s,bits=p.c,phase=p.phase,measure_count=p.m)
  new=Packed(initial=compressed,bits=p.c,phase=p.phase,measure_count=p.m)
  orig.run(source,seed);new.run(cand,seed)
  assert orig.m==new.m
  mismatches={str(q):(orig.s[q]^new.s[q]).bit_count()for q in range(36) if orig.s[q]!=new.s[q]}
  assert orig.s[36]==0
  assert not mismatches,mismatches
  assert orig.phase==new.phase,('phase',seed,(orig.phase^new.phase).bit_count())
  assert orig.c==new.c,('classical',seed)
  cases.append(dict(seed=seed,inputs=N,hmr_measurements_in_region=orig.m-p.m,bit_mismatch=0,phase_mismatch=0,classical_mismatch=0,original_q36_zero=True))
 r=dict(source_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),candidate_segment_sha256=hashlib.sha256((OUT/'rematerialized_36Q_segment_ONLY.kmb').read_bytes()).hexdigest(),scope='actual 2962 source operations / 2970 compiled operations; 36Q chart-based suffix contract',all_input_basis_states=N,measurement_recipes=4,total_input_transcript_cases=4*N,formal_all_branches_proved=False,compositional_relational_proof='stable no-q34-use zone, universal one-CCX delayed-materialization identity, bit-exact q36 HMR renaming',cases=cases,complete_inv_sqrt_36Q=False,official_verifier_run=False,elapsed_s=round(time.time()-st,2))
 (OUT/'full_domain_verify.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2))
if __name__=='__main__':verify()
