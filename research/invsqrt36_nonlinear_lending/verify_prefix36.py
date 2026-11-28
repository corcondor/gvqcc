#!/usr/bin/env python3
"""Full-domain 2^22 bit-parallel 36Q-prefix vs 37Q source check.

Uses exact nonlinear premise q22=(!q19)&(!(q2^q34)); two CCX clear
loan and restore; measurements before and during the loan are compared.
A prefix check is NOT a full 60,766-op oracle verifier.
"""
from __future__ import annotations
import sys,random,hashlib,json,time
from pathlib import Path
from native_kmb import NativeKMB
from build_prefix36 import SOURCE,OUTDIR,FIRST,LAST,CTRL,CARRIER,GUEST

N=1<<22
ONES=(1<<N)-1

def input_mask(i:int)->int:
 shift=1<<i; pattern=((1<<shift)-1)<<shift; period=shift*2
 while period<N:
  pattern|=pattern<<period
  period*=2
 return pattern

def input_state(qcount:int):
 return [input_mask(i) for i in range(22)]+[0]*(qcount-22)

def run(ops, qcount, branch,check_precondition=False):
 s=input_state(qcount);phase=0;classical={};stack=[];hmrn=0
 rotations=[];snap={}
 for idx,o in enumerate(ops):
  raw=o.raw;g=raw&127;q=o.wires
  if idx==FIRST and check_precondition:
   f=(s[19]^ONES) & (s[2]^s[34]^ONES)
   snap['q22_nonlinear_identity']=s[22]==f
   snap['q36_zero']=s[36]==0
   if not snap['q22_nonlinear_identity'] or not snap['q36_zero']:
    raise AssertionError(('nonlinear lending premise failed', (s[22]^f).bit_count(),s[36].bit_count()))
  if raw==0x81:
   stack.append(bool(classical.get(o.condition,False)));continue
  if raw==0x01:
   assert stack;stack.pop();continue
  if g in(0x40,0x41,0x42):
   if (raw&0x80 and not classical.get(o.condition,False)) or(stack and not all(stack)):continue
   if g==0x40:classical[o.measurement]=False
   elif g==0x41:classical[o.measurement]=True
   else:classical[o.measurement]=not classical.get(o.measurement,False)
   continue
  if (raw&0x80 and not classical.get(o.condition,False)) or(stack and not all(stack)):continue
  if g==0x11:s[q[0]]^=ONES
  elif g==0x21:s[q[1]]^=s[q[0]]
  elif g==0x31:s[q[2]]^=s[q[0]]&s[q[1]]
  elif g==0x22:s[q[0]],s[q[1]]=s[q[1]],s[q[0]]
  elif g==0x32:
   c,a,b=q;t=s[c]&(s[a]^s[b]);s[a]^=t;s[b]^=t
  elif g==0x50:
   bit=branch(hmrn);hmrn+=1
   if bit:phase^=s[q[0]]
   s[q[0]]=0;classical[o.measurement]=bool(bit)
  elif g==0x12:s[q[0]]=0
  elif g==0x10:phase^=s[q[0]]
  elif g==0x20:phase^=s[q[0]]&s[q[1]]
  elif g==0x30:phase^=s[q[0]]&s[q[1]]&s[q[2]]
  elif g==0x13:rotations.append(s[q[0]]) # Rotation angles byte-identical; compare their controls.
  elif g==0x00:phase^=ONES
  else:raise ValueError((idx,hex(raw),q))
 assert not stack,stack
 return s,phase,classical,hmrn,rotations,snap

def verify():
 start=time.perf_counter(); source=NativeKMB.read(SOURCE)
 new=NativeKMB.read(OUTDIR/'invsqrt36_prefix_only_NOT_SUBMIT.kmb')
 old=source.ops[:415]
 assert len(new.ops)==len(old)+14 and new.header[1]==36
 assert all(w not in op.wires for op in old[FIRST:LAST+1] for w in (2,19,34,22))
 # Test possible measurement histories on the ENTIRE input domain, not a few xs.
 recipes={
  'allzero':lambda i:0,
  'allone':lambda i:1,
  'alternating':lambda i:i%2,
  'mod7':lambda i:(i*i+5*i+1)%7 in(1,2,5),
 }
 facts={}
 for name,recipe in recipes.items():
  a,pa,ca,ma,ra,snap=run(old,37,recipe,check_precondition=True)
  b,pb,cb,mb,rb,_=run(new.ops,36,recipe)
  assert ma==mb and ca==cb and pa==pb and ra==rb
  assert a[:36]==b
  assert a[36]==0
  facts[name]={'input_states_checked':N,'matching_state_wires':36,
              'matching_phase_bitmask':True,'matching_classical_registers':True,
              'measurement_events':ma,'angle_readbacks':len(ra),
              'q22_nonlinear_relation_all_inputs':snap['q22_nonlinear_identity'],
              'q36_zero_entry_all_inputs':snap['q36_zero']}
  print('PASS',name,'all',N,'inputs',ma,'HMR branches',flush=True)
 report={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
         'prefix36_sha256':hashlib.sha256((OUTDIR/'invsqrt36_prefix_only_NOT_SUBMIT.kmb').read_bytes()).hexdigest(),
         'proof_scope':'real KMB prefix through source op414, not full 60,766-op invsqrt',
         'branch_compositional_proof':'wire renaming via clearing lender q22 with 1 CCX predicate, and restoring it after HMR; body never touches q22, q2, q19 or q34; all borrowed HMR outcomes follow by conjugation',
         'reachable_relation':'Exhaustive 2^22 basis-input test; q22=(not q19) AND not(q2 XOR q34) and q36=0 for all x at op341; classical branch independence checked using four schedules',
         'full_input_domain':N,'branch_recipes':facts,
         'success':True,'complete_36q_candidate':False,'official_score_update':False,
         'seconds':time.perf_counter()-start}
 (OUTDIR/'prefix36_exact_verification.json').write_text(json.dumps(report,indent=2)+'\n')
 return report
if __name__=='__main__':
 rep=verify();print(json.dumps({k:v for k,v in rep.items()if k!='branch_recipes'},indent=2))
