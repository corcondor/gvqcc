#!/usr/bin/env python3
"""Independent KMB-v2 compiler for exact 7-bit J=4 XOR angle loaders.
Builds caches of all low/high address monomials, a GF(2) product decomposition,
phase-correct HMR deallocation, and XOR updates on arbitrary DIRTY word inputs.

Unlike source of published 3375T family, these KMBs are newly compiled from the
original chemistry words and commute-rescheduled tree. Adaption of the public
GF(2) tensor interface from mrmeows/tensorqrom (Apache-2.0). Performance only
qualifies after native official verifier; this compiler is a correctness oracle.
"""
from __future__ import annotations
import os,sys,types,argparse,json,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
sys.modules.setdefault('kickmix',types.ModuleType('kickmix'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import tensorqrom as tq
sys.path.insert(0,str(Path(__file__).resolve().parent))
from qhdl_kmb import write_kmb,read
from chemistry_j_scheduler import delta_for
from angle_full_truth import anf_full7

L=16;HB=77;QSEL=11;BROT=7;J=4

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def bits(x):
 while x:
  k=(x&-x).bit_length()-1
  yield k;x &= x-1

class Emitter:
 def __init__(self,J=4):
  self.J=J;self.op=[];self.q1=[];self.q2=[[],[]];self.q3=[[],[],[]];self.b0=[];self.bc=[];self.nextq=11+J*7;self.nextb=0
  self.regs=[('selection',[(True,i) for i in range(11)])]+[(f'word_{j}',[(True,11+j*7+b) for b in range(7)]) for j in range(J)]
  self.count=Counter()
 def emit(self,name,*q,bit=None,cond=None):
  code={'X':0x11,'CX':0x21,'CCX':0x31,'HMR':0x50,'CZ_IF':0xa0}[name]
  if (code==0xa0)!=(cond is not None):raise AssertionError((name,cond))
  self.op.append(code);self.count[name]+=1
  if len(q)==1:self.q1.append(q[0])
  elif len(q)==2:self.q2[0].append(q[0]);self.q2[1].append(q[1])
  elif len(q)==3:
   for i,v in enumerate(q):self.q3[i].append(v)
  if bit is not None:self.b0.append(bit)
  if cond is not None:self.bc.append(cond)
 def alloc(self):q=self.nextq;self.nextq+=1;return q
 def samplebit(self):b=self.nextb;self.nextb+=1;return b
 def monomials(self,length,offset):
  qq={}
  made=[]
  for m in range(1,length):
   top=m.bit_length()-1
   if m==(1<<top):qq[m]=offset+top
   else:
    t=self.alloc();self.emit('CCX',qq[m^(1<<top)],offset+top,t);qq[m]=t;made.append((qq[m^(1<<top)],offset+top,t))
  return qq,made
 def erase_monomials(self,made):
  for a,b,t in reversed(made):
   bit=self.samplebit();self.emit('HMR',t,bit=bit)
   self.emit('CZ_IF',a,b,cond=bit)
 def write(self,path):
  streams={'qqq0':self.q3[0],'qqq1':self.q3[1],'qqq2':self.q3[2], 'qq0':self.q2[0],'qq1':self.q2[1],'q0':self.q1,'b0':self.b0,'bc':self.bc}
  write_kmb(str(path),np.array(self.op,dtype=np.uint8),streams,registers=self.regs,num_qubits=self.nextq,num_bits=self.nextb)
  parsed=read(str(path));assert parsed.num_qubits==self.nextq and parsed.num_bits==self.nextb
  assert parsed.counts['qqq']==self.count['CCX']
  return {'Q':self.nextq,'bits':self.nextb,'operations':len(self.op),'CCX':self.count['CCX'],'CX':self.count['CX'],'X':self.count['X'],'HMR':self.count['HMR'],'CZ_IF':self.count['CZ_IF'],'sha256':sha(path)}

def compile_oracle(delta,terms,out,sign_corrections=None,logical6=False):
 global HB
 HB=(len(delta)+L-1)//L
 E=Emitter(delta.shape[1]);C=anf_full7(delta,(L-1).bit_length())
 if logical6:
  C=C[:,:,[7*j+b for j in range(delta.shape[1]) for b in range(6)]].copy()
 if not np.array_equal(tq.mixed_of(terms,C.shape[0]-1,C.shape[1]-1,C.shape[2]),C[1:,1:]):raise AssertionError('invalid tensor products')
 low=C[:,0].copy();high=C[0].copy();high[0]=0
 # carry one-basis product corrections exactly, not approximations
 vl=tq._monomial_values(L,L)
 vh=tq._monomial_values(HB,HB)
 high_bits=max(1,(HB-1).bit_length());corrected=[]
 for a1,b1,a2,b2,s in terms:
  for o in bits(s):
   if a2:
    tl=((vl @ np.array([(a1>>i)&1 for i in range(L-1)],np.uint8))&1)
    tr=((vl @ np.array([(a2>>i)&1 for i in range(L-1)],np.uint8))&1)
    low[:,o]^=tq.mobius(tl&tr)
   if b2:
    hl=((vh @ np.array([(b2>>i)&1 for i in range(HB-1)],np.uint8))&1)
    hr=((vh @ np.array([(b1>>i)&1 for i in range(HB-1)],np.uint8))&1)
    truth=np.zeros(1<<high_bits,dtype=np.uint8);truth[:HB]=hl&hr
    high[:,o]^=tq.mobius(truth)[:HB]
 low[0]^=high[0];high[0]=0
 high_cache,high_made=E.monomials(HB,(L-1).bit_length())
 low_cache,low_made=E.monomials(L,0)
 def qb(z):
  return low_cache[z+1] if z<L-1 else high_cache[z-(L-1)+1]
 def fanout(s):
  targets=[]
  for o in bits(s):
   bit_index=(7*(o//6)+o%6) if logical6 else o
   targets.append(11+bit_index)
   if sign_corrections is not None and bit_index%7==5:targets.append(11+bit_index+1)
  return targets
 def parity_product(a1,b1,a2,b2,s):
  m1=a1|(b2<<(L-1));m2=a2|(b1<<(L-1))
  assert m1 and m2 and m1!=m2
  p1=next(bits(m1));chain=[(z,p1) for z in bits(m1) if z!=p1]
  if (m2>>p1)&1:m2 ^= m1^(1<<p1)
  p2=next(z for z in bits(m2) if z!=p1)
  chain += [(z,p2) for z in bits(m2) if z!=p2]
  for src,dst in chain:E.emit('CX',qb(src),qb(dst))
  targets=fanout(s);assert targets
  for z in targets[1:]:E.emit('CX',targets[0],z)
  E.emit('CCX',qb(p1),qb(p2),targets[0])
  for z in reversed(targets[1:]):E.emit('CX',targets[0],z)
  for src,dst in reversed(chain):E.emit('CX',qb(src),qb(dst))
 for t in terms:parity_product(*t)
 for m in range(L):
  outs=np.flatnonzero(low[m]);
  for o in outs:
   targets=fanout(1<<int(o))
   for target in targets:
    if m==0:E.emit('X',target)
    else:E.emit('CX',low_cache[m],target)
 for m in range(1,HB):
  for o in np.flatnonzero(high[m]):
   for target in fanout(1<<int(o)):E.emit('CX',high_cache[m],target)
 E.erase_monomials(low_made);E.erase_monomials(high_made)
 if sign_corrections is not None:
  for j,terms in enumerate(sign_corrections):
   for ai,bi in terms:
    if ai==bi:E.emit('CX',ai,11+j*7+6)
    else:E.emit('CCX',ai,bi,11+j*7+6)
 return E.write(out)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',default='/mnt/data/GVQCC_MULTIAXIS_20261122/chem_schedule_J4_SAME_SHAPE_RESEARCH.npz');ap.add_argument('--out',default='/mnt/data/GVQCC_MULTIAXIS_20261122/candidate_j4_kmb');ap.add_argument('--banks',type=int,default=None);ap.add_argument('--J',type=int,default=4);a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 with np.load(a.source) as z: W=z['angle_words'].astype(np.uint8)
 report=[]
 global J
 J=a.J
 if a.banks is None:a.banks=(75+J-1)//J
 for k in range(a.banks):
  delta=delta_for(list(range(75)),W,J,k)
  C=anf_full7(delta,4)
  terms=tq.per_output(C)
  r=compile_oracle(delta,terms,out/f'angle_k_{k}.kmb');r.update(k=k,scheme='per_output_multilinear_paired_cache',num_truth_rows=len(delta))
  report.append(r);print('bank',k,'T',r['CCX'],'Q',r['Q'],'ops',r['operations'],flush=True)
 doc={'status':'REAL_KMB_GENERATED_INDEPENDENT_FULL_PHASE_CHECK_PENDING','source':str(a.source),'source_sha256':sha(a.source),'banks':report,'total_T_per_pass':sum(r['CCX'] for r in report),'cap_128':max(r['Q'] for r in report)<=128,'warning':'No native KickMix verifier available; exhaustive logical/measurement-branch check must be run separately; a score not earned by these KMBs'}
 (out/'compilation_receipt.json').write_text(json.dumps(doc,indent=2)+'\n')
if __name__=='__main__':main()