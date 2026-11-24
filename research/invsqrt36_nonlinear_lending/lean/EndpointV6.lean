import Std.Tactic.BVDecide

/-! Concrete V5-wide serialized KMB interval [35195,35225).
No reachability assumption. All 36-bit basis states; gates are unsigned
basis permutations, so equality extends linearly on the local quantum state.
The full-program BDD verification is separate. -/
namespace GVQCC.V6Endpoint
inductive Gate where
  | cx (a b : Nat)
  | ccx (a b t : Nat)
  | swap (a b : Nat)
  deriving DecidableEq

private def bit (s : BitVec 36) (i : Nat) : BitVec 36 := (s >>> i) &&& 1
private def xorWire (s : BitVec 36) (i : Nat) (v : BitVec 36) : BitVec 36 :=
  s ^^^ (v <<< i)
def step (s : BitVec 36) : Gate → BitVec 36
  | .cx a b => xorWire s b (bit s a)
  | .ccx a b t => xorWire s t (bit s a &&& bit s b)
  | .swap a b => xorWire (xorWire s a (bit s a ^^^ bit s b)) b (bit s a ^^^ bit s b)
def run (gs : List Gate) (s : BitVec 36) : BitVec 36 := gs.foldl step s
def old : List Gate := [
  .cx 19 17,
  .cx 25 17,
  .ccx 17 29 33,
  .cx 25 17,
  .cx 19 17,
  .cx 21 33,
  .cx 29 33,
  .swap 18 33,
  .cx 18 21,
  .swap 21 20,
  .cx 20 18,
  .cx 20 29,
  .cx 21 20,
  .cx 21 29,
  .cx 29 20,
  .cx 19 17,
  .cx 25 17,
  .ccx 17 20 29,
  .cx 25 17,
  .cx 19 17,
  .swap 33 29,
  .cx 33 21,
  .cx 21 35,
  .cx 33 35,
  .cx 17 35,
  .cx 18 35,
  .cx 19 35,
  .cx 20 35,
  .cx 21 35,
  .cx 25 35]
def new : List Gate := [
  .cx 33 20,
  .cx 29 35,
  .swap 29 33,
  .cx 25 35,
  .cx 21 35,
  .swap 21 29,
  .cx 20 35,
  .swap 20 33,
  .cx 19 35,
  .swap 18 29,
  .cx 17 35]
def paid : List Gate → Nat
  | [] => 0
  | .ccx _ _ _ :: gs => 1 + paid gs
  | _ :: gs => paid gs
set_option maxRecDepth 10000 in
theorem concrete_equivalence (s : BitVec 36) : run old s = run new s := by
  simp only [old, new, run, List.foldl_cons, List.foldl_nil, step, bit, xorWire]
  bv_decide
theorem old_cost : paid old = 2 := by decide
theorem new_cost : paid new = 0 := by decide
theorem old_length : old.length = 30 := by decide
theorem new_length : new.length = 11 := by decide
#print axioms concrete_equivalence
end GVQCC.V6Endpoint
