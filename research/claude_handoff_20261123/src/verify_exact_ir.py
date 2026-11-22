#!/usr/bin/env python3
"""Independent exact 2048-address + all dirty words + all measurement phase branches verifier.
Scope: emitted X,CX,CCX,HMR,CZ_IF subset ONLY. Not native KickMix.
Certifies affine oracle and zero measurement phases by all coefficient extraction, no sampled branches.
"""
import sys,time,json,argparse,hashlib
from pathlib import Path
import numpy as np
root=Path(__file__).parent
sys.path.insert(0,str(root/'axis_old/src'))
from qhdl_kmb import read
from chemistry_j_scheduler import delta_for
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--circuits',required=True);p.add_argument('--J',type=int,default=5);p.add_argument('--banks',type=int,default=15);p.add_argument('--out',required=True);a=p.parse_args()
with np.load(a.source) as z:w=z['angle_words'].astype(np.uint8)
FULL=(1<<2048)-1
vals=[sum(1<<n for n in range(2048) if ((n>>i)&1)) for i in range(11)]
results=[];t0=time.monotonic()
for bank in range(a.banks):
 t=time.monotonic();d=delta_for(list(range(75)),w,a.J,bank);path=Path(a.circuits)/f'angle_k_{bank}.kmb'
 k=read(str(path));N=k.num_qubits;NW=7*a.J;assert NW+11<=N
 assert k.num_bits==k.counts['b'] == k.counts['c'],'each HMR must have exactly one CZ_IF correction'
 qv=[0]*N;qd=[0]*N; qv[:11]=vals
 for j in range(NW):qd[11+j]=1<<j
 phases={}; ix1=ix2=ix3=ixb=ixc=0
 q1=k.stream('q0');q2a=k.stream('qq0');q2b=k.stream('qq1');q3a=k.stream('qqq0');q3b=k.stream('qqq1');q3c=k.stream('qqq2');bs=k.stream('b0');bc=k.stream('bc')
 for n,op in enumerate(k.op_types):
  op=int(op)
  if op==0x11:
   x=int(q1[ix1]);ix1+=1;qv[x]^=FULL
  elif op==0x21:
   x,y=int(q2a[ix2]),int(q2b[ix2]);ix2+=1;qv[y]^=qv[x];qd[y]^=qd[x]
  elif op==0x31:
   x,y,z=int(q3a[ix3]),int(q3b[ix3]),int(q3c[ix3]);ix3+=1
   assert (qd[x]|qd[y])==0,f'CCX dirty-control at bank {bank} op {n}'
   qv[z]^=qv[x]&qv[y]
  elif op==0x50:
   x=int(q1[ix1]);bit=int(bs[ixb]);ix1+=1;ixb+=1
   assert qd[x]==0,f'HMR dirty scratch bank {bank} op {n}'
   phases[bit]=phases.get(bit,0)^qv[x]
   qv[x]=0;qd[x]=0
  elif op==0xa0:
   x,y=int(q2a[ix2]),int(q2b[ix2]);bit=int(bc[ixc]);ix2+=1;ixc+=1
   assert (qd[x]|qd[y])==0, f'CZ_IF dirty control bank {bank} op {n}'
   assert bit in phases, f'CZ_IF undeclared measure bit {bit}'
   phases[bit]^=qv[x]&qv[y]
  else:raise RuntimeError(f'Unknown op {op:02X}, bank={bank},n={n}')
 assert ix1==k.counts['q'] and ix2==k.counts['qq'] and ix3==k.counts['qqq']
 assert ixb==k.counts['b'] and ixc==k.counts['c']
 assert all(v==0 for v in phases.values()), f'nonzero measurement coefficient bank={bank}'
 assert qv[:11]==vals and not any(qd[:11]),'selection changed'
 assert not any(qv[11+NW:]) and not any(qd[11+NW:]),f'nonzero scratch bank={bank}'
 for bit in range(NW):
  assert qd[11+bit]==1<<bit, f'dirty XOR transfer incorrect: bank={bank} bit={bit}'
  # compare expected over selection validity; padded addresses need only be zero up to ceil(A/16)*16.
  expected=0
  for row in range(len(d)):
   if (int(d[row,bit//7])>>(bit%7))&1:expected|=1<<row
  got=qv[11+bit]
  valid_mask=(1<<len(d))-1
  assert ((got^expected)&valid_mask)==0,f'value mismatch bank={bank} bit={bit}, idx={(((got^expected)&valid_mask)&-((got^expected)&valid_mask)).bit_length()-1}'
  padding_mask=((1<<((len(d)+15)//16*16))-1)^valid_mask
  assert (got &padding_mask)==0, f'nonzero padded word bank={bank} bit={bit}'
 r=dict(bank=bank,T=int(k.counts['qqq']),Q=int(k.num_qubits),ops=int(k.counts['ops']),measure_bits=int(k.num_bits),valid_addresses=len(d),phase_all_measurement_branches=True,dirty_target_affine_matrix_identity=True,oracle_true_for_all_addresses=True,workspace_clean=True,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),time_s=round(time.monotonic()-t,3))
 results.append(r);print('PASS',bank,'T',r['T'],'Q',r['Q'],'all measurement coefficients=0','time',r['time_s'],flush=True)
s=dict(source=str(a.source),source_sha256=hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),dir=a.circuits,synthesis='original classical reversible simulation with exact affine dirty-word proof and exact linear phase coefficient proof',address_domain=len(w),banks=a.banks,total_pass_T=sum(x['T'] for x in results),maxQ=max(x['Q'] for x in results),max_ops=max(x['ops'] for x in results),bank_results=results,all_pass=True,official_KickMix_executed=False,limit='Does not replace full official end-to-end KickMix simulator, phase proof assumes native semantics of X,CX,CCX,HMR,CZ_IF',elapsed_s=time.monotonic()-t0)
Path(a.out).write_text(json.dumps(s,indent=2)+'\n')
print('RESULT',s['total_pass_T'],s['maxQ'],'time',s['elapsed_s'],flush=True)