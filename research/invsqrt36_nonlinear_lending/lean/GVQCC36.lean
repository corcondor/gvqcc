import Std.Tactic.BVDecide

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

private def prefixRun (ops:List Gate) (s:BitVec 37) : BitVec 37 :=
  ops.foldl evalWire s

structure State where
  wires:BitVec 37
  parity:Bool
  deriving DecidableEq, Repr

private def flip (s:State) (v:BitVec 37) : State :=
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

private def predicate (s:BitVec 37) : BitVec 37 :=
  ((~~~(bit s 19)) &&& (~~~((bit s 2) ^^^ (bit s 34)))) &&& 1

-- Computation basis control path (diagonal corrections do not enter the state).
private def sourcePrefix : List Gate := [
    .x 22,
    .x 22,
    .cx 20 21,
    .swap 21 19,
    .x 19,
    .x 21,
    .ccx 19 21 22,
    .x 18,
    .ccx 22 18 23,
    .cx 23 20,
    .cx 23 18,
    .cx 22 21,
    .cx 22 20,
    .cx 22 18,
    .cx 19 21,
    .swap 20 18,
    .cx 0 18,
    .x 20,
    .x 21,
    .reset 22,
    .cx 0 18,
    .x 18,
    .cx 0 18,
    .x 18,
    .x 17,
    .ccx 23 17 22,
    .x 16,
    .ccx 22 16 24,
    .cx 24 18,
    .cx 24 16,
    .cx 23 17,
    .cx 22 18,
    .cx 22 17,
    .cx 22 16,
    .swap 18 17,
    .swap 17 16,
    .x 17,
    .x 18,
    .reset 22,
    .cx 0 16,
    .x 16,
    .cx 0 16,
    .x 16,
    .x 15,
    .ccx 24 15 22,
    .x 14,
    .ccx 22 14 25,
    .cx 25 16,
    .cx 25 14,
    .cx 24 15,
    .cx 22 16,
    .cx 22 15,
    .cx 22 14,
    .swap 16 15,
    .swap 15 14,
    .x 15,
    .x 16,
    .reset 22,
    .cx 0 14,
    .x 14,
    .cx 0 14,
    .x 14,
    .x 13,
    .ccx 25 13 22,
    .x 12,
    .ccx 22 12 26,
    .cx 26 14,
    .cx 26 12,
    .cx 25 13,
    .cx 22 14,
    .cx 22 13,
    .cx 22 12,
    .swap 14 13,
    .swap 13 12,
    .x 13,
    .x 14,
    .reset 22,
    .cx 0 12,
    .x 12,
    .cx 0 12,
    .x 12,
    .x 11,
    .ccx 26 11 22,
    .x 10,
    .ccx 22 10 27,
    .cx 27 12,
    .cx 27 10,
    .cx 26 11,
    .cx 22 12,
    .cx 22 11,
    .cx 22 10,
    .swap 12 11,
    .swap 11 10,
    .x 11,
    .x 12,
    .reset 22,
    .cx 0 10,
    .x 10,
    .cx 0 10,
    .x 10,
    .x 9,
    .ccx 27 9 22,
    .x 8,
    .ccx 22 8 28,
    .cx 28 10,
    .cx 28 8,
    .cx 27 9,
    .cx 22 10,
    .cx 22 9,
    .cx 22 8,
    .swap 10 9,
    .swap 9 8,
    .x 9,
    .x 10,
    .reset 22,
    .cx 0 8,
    .x 8,
    .cx 0 8,
    .x 8,
    .x 7,
    .ccx 28 7 22,
    .x 6,
    .ccx 22 6 29,
    .cx 29 8,
    .cx 29 6,
    .cx 28 7,
    .cx 22 8,
    .cx 22 7,
    .cx 22 6,
    .swap 8 7,
    .swap 7 6,
    .x 7,
    .x 8,
    .reset 22,
    .cx 0 6,
    .x 6,
    .cx 0 6,
    .x 6,
    .x 5,
    .ccx 29 5 22,
    .x 4,
    .ccx 22 4 30,
    .cx 30 6,
    .cx 30 4,
    .cx 29 5,
    .cx 22 6,
    .cx 22 5,
    .cx 22 4,
    .swap 6 5,
    .swap 5 4,
    .x 5,
    .x 6,
    .reset 22,
    .cx 0 4,
    .x 4,
    .cx 0 4,
    .x 4,
    .x 3,
    .ccx 30 3 22,
    .x 2,
    .ccx 22 2 31,
    .cx 31 4,
    .cx 31 2,
    .cx 30 3,
    .cx 22 4,
    .cx 22 3,
    .cx 22 2,
    .swap 4 3,
    .swap 3 2,
    .x 3,
    .x 4,
    .reset 22,
    .cx 0 2,
    .x 2,
    .cx 0 2,
    .x 2,
    .cx 0 2,
    .x 2,
    .cx 31 1,
    .cx 2 1,
    .cx 2 0,
    .swap 1 0,
    .x 0,
    .x 1,
    .cx 31 0,
    .cx 31 0,
    .x 1,
    .cx 2 1,
    .cx 2 0,
    .x 19,
    .ccx 19 1 22,
    .x 19,
    .x 1,
    .cx 0 1,
    .cx 0 2,
    .cx 2 0,
    .cx 2 1,
    .swap 0 21,
    .swap 1 20,
    .swap 2 21,
    .swap 3 15,
    .swap 4 16,
    .swap 5 17,
    .swap 6 18,
    .swap 7 11,
    .swap 8 12,
    .swap 9 13,
    .swap 10 14,
    .swap 11 13,
    .swap 12 14,
    .swap 13 32,
    .swap 14 34,
    .swap 15 32,
    .swap 16 34,
    .swap 20 32,
    .swap 21 34,
    .swap 32 34,
    .cx 2 32,
    .x 32,
    .x 19,
    .ccx 19 32 13,
    .cx 18 32,
    .x 23,
    .ccx 23 32 14,
    .x 23,
    .cx 23 19,
    .cx 24 19,
    .ccx 19 16 33,
    .x 19,
    .cx 24 19,
    .cx 18 21,
    .cx 12 21,
    .cx 8 21,
    .cx 4 21,
    .cx 6 21,
    .cx 25 19,
    .cx 26 19,
    .cx 28 19,
    .cx 29 19,
    .ccx 19 21 35,
    .cx 6 21,
    .cx 4 21,
    .cx 8 21,
    .cx 18 21,
    .cx 33 4,
    .cx 33 21,
    .cx 13 4,
    .cx 13 21,
    .cx 0 10,
    .cx 0 21,
    .cx 6 10,
    .cx 4 10,
    .cx 4 21,
    .cx 4 32,
    .cx 10 4,
    .cx 10 32,
    .cx 8 4,
    .cx 8 10,
    .cx 8 32,
    .cx 12 10,
    .cx 16 4,
    .cx 16 10,
    .cx 16 32,
    .cx 18 4,
    .cx 18 10,
    .cx 21 10,
    .cx 32 4,
    .cx 32 10,
    .cx 32 21,
    .cx 6 16,
    .cx 13 16,
    .cx 33 16,
    .cx 32 16,
    .cx 10 16,
    .cx 24 19,
    .cx 27 19,
    .ccx 19 16 4,
    .cx 29 19,
    .cx 28 19,
    .cx 27 19,
    .cx 26 19,
    .cx 25 19,
    .cx 24 19,
    .cx 23 19,
    .cx 10 16,
    .cx 32 16,
    .cx 33 16,
    .cx 13 16,
    .cx 6 16,
    .cx 24 23,
    .cx 26 23,
    .cx 27 23,
    .cx 29 23,
    .cx 30 23]

-- Original measured body, each HMR outcome m is a free Bool.
private def sourceMeasured : List Gate := [
    .ccx 23 32 36,
    .cx 30 23,
    .cx 29 23,
    .cx 27 23,
    .cx 26 23,
    .cx 24 23,
    .cx 36 4,
    .cx 36 32,
    .cx 36 35,
    .cx 36 6,
    .cx 36 8,
    .cx 4 32,
    .cx 4 35,
    .cx 4 0,
    .cx 4 6,
    .cx 10 4,
    .cx 10 0,
    .cx 10 6,
    .cx 21 32,
    .cx 21 35,
    .cx 21 6,
    .cx 32 36,
    .cx 32 4,
    .cx 32 0,
    .cx 32 8,
    .cx 35 4,
    .cx 35 0,
    .cx 35 6,
    .cx 33 36,
    .cx 33 4,
    .cx 33 0,
    .cx 33 8,
    .cx 14 36,
    .cx 14 35,
    .cx 14 32,
    .cx 14 6,
    .cx 14 8,
    .cx 13 36,
    .cx 13 4,
    .cx 13 35,
    .cx 13 32,
    .cx 13 0,
    .cx 13 8,
    .cx 0 4,
    .cx 0 35,
    .cx 0 6,
    .cx 6 36,
    .cx 6 35,
    .cx 6 0,
    .cx 6 8,
    .cx 8 36,
    .cx 8 35,
    .cx 8 32,
    .cx 8 0,
    .cx 16 32,
    .cx 16 0,
    .cx 16 6,
    .cx 18 0,
    .cx 18 8,
    .hmr 36]

-- The 36-qubit implementation: clear q22, use it as q36, measure q22,
-- reconstruct q22. q36 remains 0 in the 37-bit reference representation.
private def candidateMeasured : List Gate := [
    .cx 2 34,
    .x 19,
    .x 34,
    .ccx 19 34 22,
    .x 34,
    .x 19,
    .cx 2 34,
    .ccx 23 32 22,
    .cx 30 23,
    .cx 29 23,
    .cx 27 23,
    .cx 26 23,
    .cx 24 23,
    .cx 22 4,
    .cx 22 32,
    .cx 22 35,
    .cx 22 6,
    .cx 22 8,
    .cx 4 32,
    .cx 4 35,
    .cx 4 0,
    .cx 4 6,
    .cx 10 4,
    .cx 10 0,
    .cx 10 6,
    .cx 21 32,
    .cx 21 35,
    .cx 21 6,
    .cx 32 22,
    .cx 32 4,
    .cx 32 0,
    .cx 32 8,
    .cx 35 4,
    .cx 35 0,
    .cx 35 6,
    .cx 33 22,
    .cx 33 4,
    .cx 33 0,
    .cx 33 8,
    .cx 14 22,
    .cx 14 35,
    .cx 14 32,
    .cx 14 6,
    .cx 14 8,
    .cx 13 22,
    .cx 13 4,
    .cx 13 35,
    .cx 13 32,
    .cx 13 0,
    .cx 13 8,
    .cx 0 4,
    .cx 0 35,
    .cx 0 6,
    .cx 6 22,
    .cx 6 35,
    .cx 6 0,
    .cx 6 8,
    .cx 8 22,
    .cx 8 35,
    .cx 8 32,
    .cx 8 0,
    .cx 16 32,
    .cx 16 0,
    .cx 16 6,
    .cx 18 0,
    .cx 18 8,
    .hmr 22,
    .cx 2 34,
    .x 19,
    .x 34,
    .ccx 19 34 22,
    .x 34,
    .x 19,
    .cx 2 34]

-- Prove the actual 22-bit input domain is inside the borrowing invariant.
-- This is *not* an assumed precondition on the source's 4,194,304 inputs.
theorem actual_reachable_invariant (x:BitVec 22) :
  let s := prefixRun sourcePrefix (x.setWidth 37)
  bit s 22 = predicate s ∧ bit s 36 = 0 := by
  simp only [sourcePrefix, prefixRun, List.foldl_cons, List.foldl_nil,
    evalWire, xorWire, bit, zeroWire, predicate, BitVec.setWidth]
  bv_decide

-- A stronger arbitrary-relative-phase and arbitrary-HMR-outcome theorem.
-- Branch equivalence is maintained for any initial state satisfying the
-- real invariant, independent of how that state became correlated with x.
theorem measured_lifetime_exact (s:BitVec 37) (p m:Bool)
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
