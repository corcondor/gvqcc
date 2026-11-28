#!/usr/bin/env python3
"""Generate Lean-4 certificates of the REAL first invsqrt nonlinear register loan.

The Lean statements are independent of the Python bit-parallel verifier: the
prefix and the measured HMR body are emitted from the original KMB instruction
stream; Lean must prove both the reachability predicate and the arbitrary-
measurement-outcome transformation. No `sorry`, `native_decide`, or axiom used.
"""
from pathlib import Path
import hashlib
import sys
from native_kmb import NativeKMB
from build_prefix36 import SOURCE,OUTDIR,FIRST,LAST,toggle_cached_predicate, lend

before=NativeKMB.read(SOURCE).ops
borrowed=lend(before)
# Pre341 bit changes only. Conditional Z/CZ and Z_POW have no basis effect.
def instr(op,phase=False):
    base=op.raw&127; q=op.wires
    cls={0x11:'x',0x21:'cx',0x31:'ccx',0x22:'swap',0x50:'hmr',0x12:'reset',0x10:'z',0x20:'cz',0x30:'ccz',0x13:'rotation'}
    if op.raw in (0x81,0x01): return None
    if base in (0x00,0x40,0x41,0x42):return None
    if base not in cls:raise ValueError((hex(op.raw),q))
    if op.raw&0x80: 
        if base not in (0x10,0x20,0x30):raise ValueError(('unexpected classically conditional basis gate',op))
        return None
    name=cls[base]
    if not phase and name in ('z','cz','ccz','rotation'): return None
    if phase and name=='rotation': raise ValueError('unexpected phase rotation in HMR window')
    if not phase and name=='hmr':name='reset'
    return '.%s %s'%(name,' '.join(map(str,q)))

def gates(ops,phase=False):return ',\n    '.join(x for o in ops if (x:=instr(o,phase)) is not None)

head='''import Std.Tactic.BVDecide

/-!
Real 37-qubit KickMix invsqrt KMB (SHA256 bb676b95...), prefix op0..340 and
measured body op341..400. The result proves that one *specific* HMR lifetime
can be moved onto an existing line, yielding a 36Q prefix.
The 60,766-operation full 36Q oracle is NOT proved or built here.

All theorems use Lean `bv_decide`: SAT unsatisfiability proofs are independently
checked in the Lean kernel. No postulated axioms/sorries. The HMR model only
tracks computational state and relative (-1)^phase for a specified outcome; it
is exact for this X-basis measurement-reset and deterministic conditional
phase feedback because both candidate and baseline obtain identical results.
-/
set_option maxRecDepth 65536
set_option maxHeartbeats 0
set_option sat.timeout 480

namespace GVQCC36

inductive Gate where
  | x (t: Nat)
  | cx (a t: Nat)
  | ccx (a b t: Nat)
  | swap (a b: Nat)
  | reset (q: Nat)
  | hmr (q:Nat)
  | z (q:Nat)
  | cz (a b:Nat)
  | ccz (a b c:Nat)
  deriving DecidableEq, Repr

private def bit (s: BitVec 37) (i:Nat) : BitVec 37 := (s >>> i) &&& 1
private def xorWire (s:BitVec 37) (i:Nat) (v:BitVec 37) : BitVec 37 :=
  s ^^^ ((v &&& 1) <<< i)
private def zeroWire (s:BitVec 37) (i:Nat) : BitVec 37 :=
  s &&& ~~~((1:BitVec 37) <<< i)

private def evalWire (s:BitVec 37) : Gate → BitVec 37
  | .x t => xorWire s t 1
  | .cx a t => xorWire s t (bit s a)
  | .ccx a b t => xorWire s t ((bit s a) &&& (bit s b))
  | .swap a b =>
      let d := (bit s a) ^^^ (bit s b)
      xorWire (xorWire s a d) b d
  | .reset t => zeroWire s t
  | .hmr t => zeroWire s t
  | .z _ => s
  | .cz _ _ => s
  | .ccz _ _ _ => s

private def prefixRun (ops:List Gate) (s:BitVec37) : BitVec 37 :=
  ops.foldl evalWire s

structure State where
  wires:BitVec 37
  parity:Bool
  deriving DecidableEq, Repr

private def flip (s:State) (v:BitVec37) : State :=
  {s with parity:= Bool.xor s.parity (v.getLsbD 0)}
private def tick (m:Bool) (s:State) (g:Gate) : State :=
  match g with
  | .z q => flip s (bit s.wires q)
  | .cz a b => flip s ((bit s.wires a) &&& (bit s.wires b))
  | .ccz a b c => flip s ((bit s.wires a) &&& (bit s.wires b) &&& (bit s.wires c))
  | .hmr q =>
      let v := if m then bit s.wires q else 0
      {wires := zeroWire s.wires q, parity:= Bool.xor s.parity (v.getLsbD 0)}
  | _ => {s with wires := evalWire s.wires g}
private def run (ops:List Gate) (m:Bool) (s:State) : State :=
  ops.foldl (tick m) s

private def predicate (s:BitVec37) : BitVec37 :=
  ((~~~(bit s 19)) &&& (~~~((bit s 2) ^^^ (bit s 34)))) &&& 1

'''
pre='''-- Original instructions 0..340, emitted unchanged except pure diagonal
-- gates, classically conditional phase gates, and X/Z rotation (which do not
-- modify computational state). HMR is reset in this reachability invariant.
private def sourcePrefix : List Gate := [
    '''+gates(before[:FIRST])+''']

-- First gate q36=CCX and final q36=HMR; contains no Z_POW.
private def sourceMeasured : List Gate := [
    '''+gates(before[FIRST:LAST+1],True)+''']

private def candidateMeasured : List Gate := [
    '''+gates(borrowed[FIRST:LAST+1+7+7],True)+''']

'''
# Critical: borrowed[FIRST:LAST+15] slice: 7 before+60 body+7 after =74
assert len(borrowed[FIRST:LAST+15]) == (LAST-FIRST+1)+14
for op in before[FIRST:LAST+1]:assert all(i not in op.wires for i in (22,2,19,34))
pre='''-- Computation basis control path (diagonal corrections do not enter the state).
private def sourcePrefix : List Gate := [
    '''+gates(before[:FIRST])+''']

-- Original measured body, each HMR outcome m is a free Bool.
private def sourceMeasured : List Gate := [
    '''+gates(before[FIRST:LAST+1],True)+''']

-- The 36-qubit implementation: clear q22, use it as q36, measure q22,
-- reconstruct q22. q36 remains 0 in the 37-bit reference representation.
private def candidateMeasured : List Gate := [
    '''+gates(borrowed[FIRST:LAST+15],True)+''']

'''
proof='''-- Prove the actual 22-bit input domain is inside the borrowing invariant.
-- This is *not* an assumed precondition on the source's 4,194,304 inputs.
theorem actual_reachable_invariant (x:BitVec22) :
  let s := prefixRun sourcePrefix (x.setWidth 37)
  bit s 22 = predicate s ∧ bit s 36 = 0 := by
  simp only [sourcePrefix, prefixRun, List.foldl_cons, List.foldl_nil,
    evalWire, xorWire, bit, zeroWire, predicate, BitVec.setWidth]
  bv_decide

-- A stronger arbitrary-relative-phase and arbitrary-HMR-outcome theorem.
-- Branch equivalence is maintained for any initial state satisfying the
-- real invariant, independent of how that state became correlated with x.
theorem measured_lifetime_exact (s:BitVec37) (p m:Bool)
 (hcache:bit s 22 = predicate s) (hzero:bit s 36 = 0) :
    run sourceMeasured m ⟨s,p⟩ = run candidateMeasured m ⟨s,p⟩ := by
  simp only [sourceMeasured, candidateMeasured, run, List.foldl_cons,
    List.foldl_nil, tick, evalWire, xorWire, bit, zeroWire, flip, predicate,
    State.mk.injEq] at *
  bv_decide

private def ccxCost : List Gate → Nat
  | [] => 0
  | .ccx _ _ _::rest => 1+ccxCost rest
  | _::rest => ccxCost rest

theorem measured_lifetime_cost : ccxCost candidateMeasured = ccxCost sourceMeasured + 2 := by
  decide

end GVQCC36
'''
# If goals too computationally huge, Lean's bv_decide can be switched to
# a generated layered SAT proof of the same actual gate stream.
text=(head+pre+proof).replace('BitVec37','BitVec 37').replace('BitVec22','BitVec 22').replace('set_option sat.timeout 480\\n','')
out=Path(__file__).parent/'lean'/'GVQCC36.lean'
out.parent.mkdir(exist_ok=True)
out.write_text(text,encoding='utf-8')
print('wrote',out,len(text),'source',len(gates(before[:FIRST]).split(',')),'measured',len(gates(before[FIRST:LAST+1],True).split(',')),'changed',len(gates(borrowed[FIRST:LAST+15],True).split(',')))
