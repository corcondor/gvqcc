import Std.Tactic.BVDecide

/-!
Concrete PR45 x PR46 semantic donor transfer. Parent native SHA256:
f7abc033dbed5477d5685225d9bf5fe262ceb888189ebcc3266ce23f9d15fd6d.
Candidate native SHA256:
90a798c0995a3ed1fece0aca556bcd0dd8b9c6ecd9f30fadd9b79022734f4f9e.
All 8 local reachability premises were separately checked by exact BDD on all
3,133,452 legal inputs and 1,174 independent potential HMR outcomes.
This file certifies the conditional actual gate-list equations and resources.
The full oracle, native parser and physical reachability are not Lean-proved.
-/
set_option maxRecDepth 65536
set_option maxHeartbeats 0

namespace GVQCC.SemanticDonorV9

inductive Gate where
  | x (q : Nat)
  | cx (a t : Nat)
  | ccx (a b t : Nat)
  deriving DecidableEq, Repr

def bit (s : BitVec 36) (q : Nat) : BitVec 36 := (s >>> q) &&& 1
def toggle (s : BitVec 36) (q : Nat) (v : BitVec 36) : BitVec 36 :=
  s ^^^ ((v &&& 1) <<< q)

def step (s : BitVec 36) : Gate → BitVec 36
  | .x q => toggle s q 1
  | .cx a t => toggle s t (bit s a)
  | .ccx a b t => toggle s t (bit s a &&& bit s b)

def run (gs : List Gate) (s : BitVec 36) : BitVec 36 := gs.foldl step s

def paid : List Gate → Nat
  | [] => 0
  | .ccx _ _ _ :: gs => 1 + paid gs
  | _ :: gs => paid gs

def wireOK : Gate → Bool
  | .x q => decide (q < 36)
  | .cx a t => decide (a < 36 ∧ t < 36 ∧ a ≠ t)
  | .ccx a b t => decide (a < 36 ∧ b < 36 ∧ t < 36 ∧ a ≠ b ∧ a ≠ t ∧ b ≠ t)

-- PR45 serialized index 5867; PR46 donor index 5882.
def old5867 : List Gate := [.ccx 16 33 3]
def new5867 : List Gate := [.cx 11 3, .cx 12 3, .cx 24 3, .cx 33 3]

theorem eq5867 (x : BitVec 36)
    (h : (bit x 16 &&& bit x 33) = (bit x 11 ^^^ bit x 12 ^^^ bit x 24 ^^^ bit x 33)) :
    run old5867 x = run new5867 x := by
  simp only [old5867, new5867, run, List.foldl_cons, List.foldl_nil, step, bit, toggle] at *
  bv_decide

theorem resource5867 :
    old5867.all wireOK = true ∧ new5867.all wireOK = true ∧
    paid old5867 = 1 ∧ paid new5867 = 0 := by decide

-- PR45 serialized index 6026; PR46 donor index 6079.
def old6026 : List Gate := [.ccx 24 16 3]
def new6026 : List Gate := [.cx 10 3, .cx 12 3, .cx 16 3, .cx 33 3]

theorem eq6026 (x : BitVec 36)
    (h : (bit x 24 &&& bit x 16) = (bit x 10 ^^^ bit x 12 ^^^ bit x 16 ^^^ bit x 33)) :
    run old6026 x = run new6026 x := by
  simp only [old6026, new6026, run, List.foldl_cons, List.foldl_nil, step, bit, toggle] at *
  bv_decide

theorem resource6026 :
    old6026.all wireOK = true ∧ new6026.all wireOK = true ∧
    paid old6026 = 1 ∧ paid new6026 = 0 := by decide

-- PR45 serialized index 7851; PR46 donor index 7916.
def old7851 : List Gate := [.ccx 19 7 3]
def new7851 : List Gate := [.x 3, .cx 7 3, .cx 10 3, .cx 13 3, .cx 19 3, .cx 33 3]

theorem eq7851 (x : BitVec 36)
    (h : (bit x 19 &&& bit x 7) = ((1 : BitVec 36) ^^^ bit x 7 ^^^ bit x 10 ^^^ bit x 13 ^^^ bit x 19 ^^^ bit x 33)) :
    run old7851 x = run new7851 x := by
  simp only [old7851, new7851, run, List.foldl_cons, List.foldl_nil, step, bit, toggle] at *
  bv_decide

theorem resource7851 :
    old7851.all wireOK = true ∧ new7851.all wireOK = true ∧
    paid old7851 = 1 ∧ paid new7851 = 0 := by decide

-- PR45 serialized index 8105; PR46 donor index 8179.
def old8105 : List Gate := [.ccx 25 6 34]
def new8105 : List Gate := [.cx 3 34, .cx 6 34, .cx 20 34, .cx 33 34]

theorem eq8105 (x : BitVec 36)
    (h : (bit x 25 &&& bit x 6) = (bit x 3 ^^^ bit x 6 ^^^ bit x 20 ^^^ bit x 33)) :
    run old8105 x = run new8105 x := by
  simp only [old8105, new8105, run, List.foldl_cons, List.foldl_nil, step, bit, toggle] at *
  bv_decide

theorem resource8105 :
    old8105.all wireOK = true ∧ new8105.all wireOK = true ∧
    paid old8105 = 1 ∧ paid new8105 = 0 := by decide

-- PR45 serialized index 8174; PR46 donor index 8251.
def old8174 : List Gate := [.ccx 31 20 8]
def new8174 : List Gate := [.cx 3 8, .cx 20 8, .cx 33 8, .cx 34 8]

theorem eq8174 (x : BitVec 36)
    (h : (bit x 31 &&& bit x 20) = (bit x 3 ^^^ bit x 20 ^^^ bit x 33 ^^^ bit x 34)) :
    run old8174 x = run new8174 x := by
  simp only [old8174, new8174, run, List.foldl_cons, List.foldl_nil, step, bit, toggle] at *
  bv_decide

theorem resource8174 :
    old8174.all wireOK = true ∧ new8174.all wireOK = true ∧
    paid old8174 = 1 ∧ paid new8174 = 0 := by decide

-- PR45 serialized index 8233; PR46 donor index 8311.
def old8233 : List Gate := [.ccx 9 34 15]
def new8233 : List Gate := [.cx 3 15, .cx 8 15, .cx 33 15, .cx 34 15]

theorem eq8233 (x : BitVec 36)
    (h : (bit x 9 &&& bit x 34) = (bit x 3 ^^^ bit x 8 ^^^ bit x 33 ^^^ bit x 34)) :
    run old8233 x = run new8233 x := by
  simp only [old8233, new8233, run, List.foldl_cons, List.foldl_nil, step, bit, toggle] at *
  bv_decide

theorem resource8233 :
    old8233.all wireOK = true ∧ new8233.all wireOK = true ∧
    paid old8233 = 1 ∧ paid new8233 = 0 := by decide

-- PR45 serialized index 9664; PR46 donor index 10293.
def old9664 : List Gate := [.ccx 26 27 30]
def new9664 : List Gate := [.cx 33 30]

theorem eq9664 (x : BitVec 36)
    (h : (bit x 26 &&& bit x 27) = (bit x 33)) :
    run old9664 x = run new9664 x := by
  simp only [old9664, new9664, run, List.foldl_cons, List.foldl_nil, step, bit, toggle] at *
  bv_decide

theorem resource9664 :
    old9664.all wireOK = true ∧ new9664.all wireOK = true ∧
    paid old9664 = 1 ∧ paid new9664 = 0 := by decide

-- PR45 serialized index 13598; PR46 donor index 15846.
def old13598 : List Gate := [.ccx 4 0 29]
def new13598 : List Gate := [.cx 3 29, .cx 4 29, .cx 19 29, .cx 27 29]

theorem eq13598 (x : BitVec 36)
    (h : (bit x 4 &&& bit x 0) = (bit x 3 ^^^ bit x 4 ^^^ bit x 19 ^^^ bit x 27)) :
    run old13598 x = run new13598 x := by
  simp only [old13598, new13598, run, List.foldl_cons, List.foldl_nil, step, bit, toggle] at *
  bv_decide

theorem resource13598 :
    old13598.all wireOK = true ∧ new13598.all wireOK = true ∧
    paid old13598 = 1 ∧ paid new13598 = 0 := by decide

theorem totalResource :
    (paid old5867 + paid old6026 + paid old7851 + paid old8105 + paid old8174 + paid old8233 + paid old9664 + paid old13598) = 8 ∧
    (paid new5867 + paid new6026 + paid new7851 + paid new8105 + paid new8174 + paid new8233 + paid new9664 + paid new13598) = 0 := by decide

end GVQCC.SemanticDonorV9
