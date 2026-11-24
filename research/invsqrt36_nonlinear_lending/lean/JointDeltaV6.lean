import Std.Tactic.BVDecide

/-! Actual selected V6 joint-delta donor slices on PR36 KMB
b1978632f8e7df632406099a7d0a7f2b0ec133df4b973439998226a8c8ff0c9f.
The 8110 and 8158 lemmas require reachable-state hypotheses established
by the independent whole-circuit BDD. The 42323 lemma is universal.
All three slices contain only computational-basis permutation gates:
they do not change the incoming relative phase or classical registers.
This is not a full oracle Lean proof or official scoring certificate. -/
namespace GVQCC.JointDeltaV6
set_option maxRecDepth 65536
set_option maxHeartbeats 0

inductive Gate where
  | x (q : Nat)
  | cx (a t : Nat)
  | ccx (a b t : Nat)
  | swap (a b : Nat)
  deriving DecidableEq, Repr

def bit (s : BitVec 36) (i : Nat) : BitVec 36 := (s >>> i) &&& 1

def toggle (s : BitVec 36) (i : Nat) (v : BitVec 36) : BitVec 36 :=
  s ^^^ ((v &&& 1) <<< i)

def tick (s : BitVec 36) : Gate → BitVec 36
  | .x q => toggle s q 1
  | .cx a t => toggle s t (bit s a)
  | .ccx a b t => toggle s t (bit s a &&& bit s b)
  | .swap a b =>
    let v := bit s a ^^^ bit s b
    toggle (toggle s a v) b v

def run (gs : List Gate) (s : BitVec 36) := gs.foldl tick s

def paid : List Gate → Nat
  | [] => 0
  | .ccx _ _ _ :: gs => 1 + paid gs
  | _ :: gs => paid gs

def wireOK : Gate → Bool
  | .x q => decide (q < 36)
  | .cx a t | .swap a t => decide (a < 36 ∧ t < 36 ∧ a ≠ t)
  | .ccx a b t => decide (a < 36 ∧ b < 36 ∧ t < 36 ∧ a ≠ b ∧ a ≠ t ∧ b ≠ t)

def residual8158 (x : BitVec 36) : BitVec 36 :=
  bit x 28 &&&
    (bit x 19 ^^^ (bit x 18 &&& bit x 19) ^^^ bit x 20 ^^^
     (bit x 18 &&& bit x 20) ^^^ (bit x 18 &&& bit x 21) ^^^
     (bit x 19 &&& bit x 21) ^^^ (bit x 20 &&& bit x 21))

def src8110 : List Gate := [.ccx 19 20 35,
  .x 20,
  .cx 21 20,
  .cx 18 20,
  .x 19,
  .cx 21 19,
  .cx 20 19,
  .cx 18 19,
  .cx 18 21,
  .x 21,
  .cx 18 28,
  .cx 19 28,
  .cx 19 28,
  .cx 18 28,
  .x 21,
  .cx 18 21,
  .cx 18 27,
  .cx 19 27,
  .cx 20 27,
  .cx 28 27,
  .cx 35 27,
  .cx 28 18,
  .cx 28 21,
  .ccx 18 21 35,
  .cx 28 21,
  .cx 28 18,
  .ccx 19 20 35,
  .x 35,
  .cx 18 35,
  .cx 20 35,
  .cx 21 35,
  .cx 35 27,
  .x 27]
def dst8110 : List Gate := [.x 20,
  .cx 21 20,
  .cx 18 20,
  .x 19,
  .cx 21 19,
  .cx 20 19,
  .cx 18 19,
  .cx 18 21,
  .x 21,
  .cx 18 28,
  .cx 19 28,
  .cx 19 28,
  .cx 18 28,
  .x 21,
  .cx 18 21,
  .cx 28 18,
  .cx 28 21,
  .cx 28 21,
  .cx 28 18,
  .cx 20 18,
  .cx 21 18,
  .ccx 18 19 27,
  .cx 21 18,
  .cx 20 18,
  .cx 21 27,
  .cx 28 27,
  .cx 21 18,
  .cx 21 19,
  .cx 28 19,
  .ccx 18 19 35,
  .cx 28 19,
  .cx 21 19,
  .cx 21 18,
  .cx 19 35,
  .cx 21 35,
  .cx 28 35,
  .cx 35 27]

theorem local_8110 (x : BitVec 36) (h : bit x 35 = 0) :
    run src8110 x = run dst8110 x := by
  simp only [src8110, dst8110, run, List.foldl_cons, List.foldl_nil,
    tick, bit, toggle] at *
  bv_decide

theorem resources_8110 :
    src8110.all wireOK = true ∧ dst8110.all wireOK = true ∧
    paid src8110 = 3 ∧ paid dst8110 = 2 := by decide

def src8158 : List Gate := [.ccx 19 28 27,
  .cx 21 19,
  .cx 20 19,
  .ccx 18 19 0,
  .ccx 0 28 27,
  .ccx 18 19 0,
  .ccx 0 28 27,
  .ccx 19 21 0,
  .ccx 0 28 27,
  .ccx 19 21 0,
  .ccx 0 28 27,
  .ccx 19 20 0]
def dst8158 : List Gate := [.cx 21 19,
  .cx 20 19,
  .ccx 19 20 0,
  .cx 21 20,
  .ccx 20 28 27,
  .cx 21 20]

theorem local_8158 (x : BitVec 36) (h : residual8158 x = 0) :
    run src8158 x = run dst8158 x := by
  simp only [src8158, dst8158, run, List.foldl_cons, List.foldl_nil,
    tick, residual8158, bit, toggle] at *
  bv_decide

theorem resources_8158 :
    src8158.all wireOK = true ∧ dst8158.all wireOK = true ∧
    paid src8158 = 10 ∧ paid dst8158 = 2 := by decide

def src42323 : List Gate := [.ccx 31 35 32,
  .ccx 31 35 30,
  .ccx 31 35 22,
  .ccx 31 35 19,
  .ccx 31 35 17,
  .cx 20 32,
  .cx 20 30,
  .cx 20 23,
  .cx 20 22,
  .cx 20 19,
  .cx 20 17,
  .swap 32 19]
def dst42323 : List Gate := [.ccx 31 35 22,
  .ccx 31 35 17,
  .cx 20 23,
  .cx 20 22,
  .cx 20 17,
  .cx 19 32,
  .cx 19 30,
  .ccx 31 35 19,
  .cx 20 19,
  .swap 32 19,
  .cx 32 19,
  .cx 32 30]

theorem local_42323 (x : BitVec 36)  :
    run src42323 x = run dst42323 x := by
  simp only [src42323, dst42323, run, List.foldl_cons, List.foldl_nil,
    tick, bit, toggle] 
  bv_decide

theorem resources_42323 :
    src42323.all wireOK = true ∧ dst42323.all wireOK = true ∧
    paid src42323 = 5 ∧ paid dst42323 = 3 := by decide

theorem joint_cost :
    paid src8110 + paid src8158 + paid src42323 = 18 ∧
    paid dst8110 + paid dst8158 + paid dst42323 = 7 := by decide

end GVQCC.JointDeltaV6
