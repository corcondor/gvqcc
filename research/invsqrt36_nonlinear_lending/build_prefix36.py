#!/usr/bin/env python3
"""Nonlocal register lending for the first measured inverse-sqrt reduction.

This builds an independently executable 36Q *PREFIX* circuit and a full 37Q
round-trip candidate (unchanged total T). Neither is a complete 36Q oracle.
The single reduction crosses a 60-operation reversible/measurement window.

This is a proof-producing partial compiler, not a competitive submission.
"""
from __future__ import annotations
from dataclasses import dataclass,replace
from pathlib import Path
import hashlib,json,struct,sys,os
from native_kmb import NativeKMB,Op

SOURCE=Path(os.environ.get('GVQCC_INVSQRT_KMB', Path(__file__).parent/'inputs'/'invsqrt.kmb'))
OUTDIR=Path(__file__).resolve().parent/'outputs'
FIRST=341
LAST=400
RESTORE_AT=401
CTRL=26
CARRIER=28
GUEST=36
HEADER=struct.Struct('<4I9Q'); PACK=struct.Struct('<QQ')

# At source op341 the ORIGINAL reachable state satisfies the exact Boolean
# relation q22 = (not q19) and (not (q2 xor q34)).
# Proof by bit-parallel evaluation over all 2^22 inputs is in verify_prefix36.py.
# The controls 2, 19 and 34 and carrier 22 are never touched by the source body.
# Each borrow/unborrow costs ONE CCX plus free Clifford gates.
def toggle_cached_predicate() -> list[Op]:
    return [
       Op(0x21,(2,34)),
       Op(0x11,(19,)),
       Op(0x11,(34,)),
       Op(0x31,(19,34,22)),
       Op(0x11,(34,)),
       Op(0x11,(19,)),
       Op(0x21,(2,34)),
    ]

def lend(ops:list[Op]):
 assert ops[FIRST].raw==0x31 and ops[FIRST].wires==(23,32,GUEST)
 assert ops[LAST].raw==0x50 and ops[LAST].wires==(GUEST,)
 for op in ops[FIRST:LAST+1]:
  for w in (2,19,34,22):
   assert w not in op.wires,(op,'lender or control touched')
 before=toggle_cached_predicate()
 body=[replace(op,wires=tuple(22 if q==GUEST else q for q in op.wires)) for op in ops[FIRST:LAST+1]]
 after=toggle_cached_predicate()
 return ops[:FIRST]+before+body+after+ops[LAST+1:]

def byte_emit(reference:NativeKMB, modified_ops:list[Op],qcount:int)->bytes:
 # Keep REGISTER_TARGETS exact, including register name and all 22 input wires.
 data={i:bytearray() for i in range(1,12)}
 rotations=reference.sections[10][1]
 assert len(rotations)==reference.header[10]*16
 # This converter only deletes/renames non-angle instructions; the order and
 # count of Z_POWs are retained for both full and prefix outputs.
 nangles=sum((op.raw&0x7F)==0x13 for op in modified_ops)
 data[10]+=rotations[:16*nangles]
 data[11]+=reference.sections[11][1]
 cols={0:(),1:(7,),2:(5,6),3:(2,3,4)}
 for op in modified_ops:
  if any(x>=qcount for x in op.wires):
   raise AssertionError('unmapped reference to removed physical wire')
  data[1].append(op.raw)
  for c,q in zip(cols[(op.raw>>4)&3],op.wires):data[c]+=struct.pack('<I',q)
  if op.raw&0x40:
   assert op.measurement is not None
   data[8]+=struct.pack('<I',op.measurement)
  if op.raw&0x80:
   assert op.condition is not None
   data[9]+=struct.pack('<I',op.condition)
 h=list(reference.header)
 h[1]=qcount;h[4]=len(modified_ops)
 h[5]=sum(((o.raw>>4)&3)==3 for o in modified_ops)
 h[6]=sum(((o.raw>>4)&3)==2 for o in modified_ops)
 h[7]=sum(((o.raw>>4)&3)==1 for o in modified_ops)
 h[8]=sum(bool(o.raw&0x40) for o in modified_ops)
 h[9]=sum(bool(o.raw&0x80) for o in modified_ops)
 h[10]=nangles
 buf=bytearray(reference.prefix16+HEADER.pack(*h))
 for kind, raw in reference.sections:
  p=raw if kind==0 else bytes(data[kind])
  buf+=PACK.pack(kind,len(p))+p
 return bytes(buf)

def build():
 OUTDIR.mkdir(exist_ok=True)
 ref=NativeKMB.read(SOURCE)
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='bb676b95f94c923cc5482f6cd8d457ab5ff3e8180c8f7cfd2c9678335d0ba56b'
 changed=lend(ref.ops)
 # Good candidate prefix ends after original correction (op414).
 prefix=changed[:415+14]
 assert all(GUEST not in op.wires for op in prefix)
 full=OUTDIR/'invsqrt37_first_lend.kmb'
 part=OUTDIR/'invsqrt36_prefix_only_NOT_SUBMIT.kmb'
 full.write_bytes(byte_emit(ref,changed,37))
 part.write_bytes(byte_emit(ref,prefix,36))
 assert NativeKMB.read(full).ops==changed
 assert NativeKMB.read(part).ops==prefix
 assert NativeKMB.read(full).header[1]==37
 assert NativeKMB.read(part).header[1]==36
 orig_t=sum((o.raw&127)==0x31 for o in ref.ops)
 new_t=sum((o.raw&127)==0x31 for o in changed)
 assert orig_t+2==new_t
 results={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'source_ops':len(ref.ops),'source_Q':ref.header[1],
          'source_CCX':orig_t,'source_HMR':sum((o.raw&127)==0x50 for o in ref.ops),
          'borrow_first_op':FIRST,'borrow_last_op':LAST,
          'cleaning_function':'q22 XOR ((not q19) AND (not (q2 XOR q34)))',
          'borrowed_original_wire':GUEST,
          'restoring_function':'same nonlinear predicate after HMR',
          'prefix_state_relation':'For all 2^22 x: q22 == not q19 AND not(q2 XOR q34), q36 == 0 immediately before op341',
          'full_mutation_Q':37,'full_mutation_CCX':new_t,'full_mutation_extra_CX':4,
          'prefix_mutation_Q':36,'prefix_complete_oracle':False,
          'full_mutation_complete_36Q':False,
          'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in (full,part)}}
 (OUTDIR/'construction.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps(results,indent=2))
 return results
if __name__=='__main__': build()
