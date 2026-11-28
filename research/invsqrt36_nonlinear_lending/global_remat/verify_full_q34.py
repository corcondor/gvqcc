#!/usr/bin/env python3
"""Full 2^22 basis-state witness for q34 redundant at source op 7293.
Analyses all PUSH/POP blocks before the cut for state identity over arbitrary inputs.
"""
from pathlib import Path
import json, hashlib,sys,time,collections
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from native_kmb import NativeKMB
from remat36 import REFERENCE as base, OUT
ops=NativeKMB.read(base).ops;CUT=7293;N=1<<22;ones=(1<<N)-1

def var(i):
 size=1<<i
 p=((1<<size)-1)<<size
 shift=2*size
 while shift<N:
  p |= p<<shift
  shift <<=1
 return p
start=time.time(); state=[var(i) for i in range(22)]+[0]*15
# Prove every PUSH/POP block is basis-identity unconditionally, including
# any nested condition, by affine symbolic matrices over Boolean variables.
def block_identity(events):
 wires=sorted({q for op in events for q in op.wires})
 if not wires:return True
 row={q:1<<(j+1) for j,q in enumerate(wires)}
 for op in events:
  typ=op.raw&127
  if typ==0x11:row[op.wires[0]]^=1
  elif typ==0x21:row[op.wires[1]]^=row[op.wires[0]]
  elif typ in (0x10,0x20,0x30,0x00):pass
  else:raise AssertionError(('unsupported PUSH/POP block',op))
 return all(row[q]==(1<<(i+1)) for i,q in enumerate(wires))
blocks=[];inside=[];depth=0
for i,op in enumerate(ops[:CUT]):
 g=op.raw&127
 if op.raw==0x81:
  if depth==0:inside=[];first=i
  depth+=1;continue
 if op.raw==0x01:
  depth-=1
  if depth==0:blocks.append(dict(first=first,last=i,ops=len(inside),identity=block_identity(inside)))
  continue
 if depth:inside.append(op)
assert depth==0
print('conditional blocks before cut',len(blocks),'non-identity blocks',sum(not b['identity'] for b in blocks),flush=True)
assert all(b['identity'] for b in blocks)
# Check no standalone classical conditional state mutation outside PUSH.
assert not [(i,o.raw) for i,o in enumerate(ops[:CUT]) if (o.raw&128) and (o.raw&127) in (0x11,0x21,0x31,0x22,0x32,0x12,0x50)]
# Use intrinsic basis unitaries, treating each proven-identity conditional block
# as *jointly* zero: exact computational state is independent of all outcomes.
depth=0
for i,op in enumerate(ops[:CUT]):
 raw=op.raw;g=raw&127;q=op.wires
 if raw==0x81:depth+=1;continue
 if raw==0x01:depth-=1;continue
 if depth:continue
 if g==0x11:state[q[0]]^=ones
 elif g==0x21:state[q[1]]^=state[q[0]]
 elif g==0x31:state[q[2]]^=state[q[0]] & state[q[1]]
 elif g==0x22:state[q[0]],state[q[1]]=state[q[1]],state[q[0]]
 elif g==0x32:
  a,b,c=q; t=state[a]&(state[b]^state[c]);state[b]^=t;state[c]^=t
 elif g in (0x50,0x12):state[q[0]]=0
 elif g in (0x00,0x10,0x20,0x30,0x13,0x40,0x41,0x42):pass
 else:raise AssertionError((i,hex(raw),q))
q34=state[34]; prediction=state[33] & (ones ^ state[5] ^ state[7] ^ state[15] ^ state[21]);delta=q34^prediction
report=dict(cut=CUT,source_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),all_inputs=N,input_qubits=22,condition_blocks=len(blocks),conditional_blocks_identity=all(b['identity'] for b in blocks),no_standalone_conditional_state_changes=True,formula='q34 = q33 & (1 XOR q5 XOR q7 XOR q15 XOR q21)',mismatches=delta.bit_count(),verified=delta==0,elapsed_seconds=round(time.time()-start,2),nontrivial_q34_popcount=q34.bit_count(),full_state_bitset_sha256=hashlib.sha256(b''.join(z.to_bytes(N//8,'little')for z in state)).hexdigest())
(OUT/'q34_full_proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
