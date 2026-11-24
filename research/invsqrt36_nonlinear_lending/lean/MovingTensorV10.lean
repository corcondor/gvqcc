import Std.Tactic.BVDecide

/- V10: actual native gate lists from moving-frame and shared-atom passes.
   Unconditional Boolean action; no HMR or diagonal phase gates in these slices.
   Their controlled versions preserve equality under an unchanged common guard.
   Universal 37-bit equality, not just sampled reachable states. -/
namespace GVQCC.MovingTensorV10
set_option maxRecDepth 65536
set_option maxHeartbeats 0
inductive Gate where
  | x (q : Nat)
  | cx (a t : Nat)
  | ccx (a b t : Nat)
  | swap (a b : Nat)
  deriving DecidableEq, Repr

def bit (s : BitVec 37) (q : Nat) : BitVec 37 := (s >>> q) &&& 1
def toggle (s : BitVec 37) (q : Nat) (v : BitVec 37) : BitVec 37 := s ^^^ (v <<< q)
def step (s : BitVec 37) : Gate → BitVec 37
  | .x q => toggle s q 1
  | .cx a t => toggle s t (bit s a)
  | .ccx a b t => toggle s t (bit s a &&& bit s b)
  | .swap a b =>
    let v := bit s a ^^^ bit s b
    toggle (toggle s a v) b v

def run (gs : List Gate) (s : BitVec 37) : BitVec 37 := gs.foldl step s
def paid (gs : List Gate) : Nat := (gs.filter fun g => match g with | .ccx _ _ _ => true | _ => false).length
def wireOK (g : Gate) : Bool := match g with
  | .x a => a < 36
  | .cx a b | .swap a b => a < 36 && b < 36 && a != b
  | .ccx a b c => a < 36 && b < 36 && c < 36 && a != b && b != c && a != c

def old_cost_moving : List Gate := [.ccx 0 23 7, .cx 8 7, .cx 8 23, .cx 34 7, .cx 34 23, .cx 15 0, .ccx 0 23 33, .cx 23 33, .cx 23 8, .cx 33 7, .cx 0 23, .cx 34 8, .cx 15 0, .ccx 0 8 23, .x 23, .cx 0 23, .cx 8 23, .cx 15 0, .cx 34 0, .cx 33 23, .ccx 8 15 22]
def new_cost_moving : List Gate := [.cx 8 7, .cx 8 23, .cx 34 7, .cx 34 23, .cx 15 0, .ccx 0 23 33, .cx 23 33, .cx 23 8, .cx 33 7, .cx 0 23, .cx 34 8, .cx 15 0, .x 23, .cx 0 23, .cx 8 23, .cx 15 0, .cx 34 0, .cx 33 23, .cx 7 23, .cx 15 0, .cx 34 0, .ccx 0 8 7, .cx 34 0, .cx 15 0, .cx 7 23, .ccx 15 8 22]
theorem equiv_cost_moving (s : BitVec 37) : run old_cost_moving s = run new_cost_moving s := by
  simp only [old_cost_moving, new_cost_moving, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem resources_cost_moving : paid old_cost_moving = 4 ∧ paid new_cost_moving = 3 ∧ old_cost_moving.all wireOK = true ∧ new_cost_moving.all wireOK = true := by decide

def old_wide_moving1 : List Gate := [.ccx 18 19 27, .cx 28 27, .cx 28 19, .cx 21 27, .cx 21 19, .cx 20 18, .ccx 18 19 35, .cx 19 35, .cx 19 28, .cx 35 27, .swap 19 28, .cx 18 28, .cx 21 19, .cx 20 18, .ccx 18 19 28, .x 28, .cx 18 28, .cx 19 28, .cx 20 18, .cx 21 18, .cx 35 28, .ccx 19 20 0]
def new_wide_moving1 : List Gate := [.cx 28 27, .cx 28 19, .cx 21 27, .cx 21 19, .cx 20 18, .ccx 18 19 35, .cx 19 35, .cx 19 28, .cx 35 27, .swap 19 28, .cx 18 28, .cx 21 19, .cx 20 18, .x 28, .cx 18 28, .cx 19 28, .cx 20 18, .cx 21 18, .cx 35 28, .cx 27 28, .cx 20 18, .cx 21 18, .ccx 18 19 27, .cx 21 18, .cx 20 18, .cx 27 28, .ccx 19 20 0]
theorem equiv_wide_moving1 (s : BitVec 37) : run old_wide_moving1 s = run new_wide_moving1 s := by
  simp only [old_wide_moving1, new_wide_moving1, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem resources_wide_moving1 : paid old_wide_moving1 = 4 ∧ paid new_wide_moving1 = 3 ∧ old_wide_moving1.all wireOK = true ∧ new_wide_moving1.all wireOK = true := by decide

def old_wide_moving2 : List Gate := [.ccx 24 35 26, .ccx 30 33 26, .swap 33 26, .cx 26 18, .cx 34 18, .ccx 24 35 33, .ccx 24 35 18]
def new_wide_moving2 : List Gate := [.swap 33 26, .cx 26 18, .cx 34 18, .ccx 30 26 33, .ccx 24 35 18]
theorem equiv_wide_moving2 (s : BitVec 37) : run old_wide_moving2 s = run new_wide_moving2 s := by
  simp only [old_wide_moving2, new_wide_moving2, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem resources_wide_moving2 : paid old_wide_moving2 = 4 ∧ paid new_wide_moving2 = 2 ∧ old_wide_moving2.all wireOK = true ∧ new_wide_moving2.all wireOK = true := by decide

def old_wide_moving3 : List Gate := [.ccx 17 21 20, .ccx 34 35 20, .cx 3 20, .cx 9 20, .cx 16 20, .cx 17 20, .swap 24 20, .cx 27 31, .cx 27 11, .swap 27 24, .cx 21 5, .cx 20 25, .cx 20 24, .cx 20 22, .cx 20 15, .cx 20 6, .cx 20 5, .cx 23 22, .swap 27 25, .swap 27 22, .cx 34 22, .ccx 34 35 22]
def new_wide_moving3 : List Gate := [.cx 3 20, .cx 9 20, .cx 16 20, .cx 17 20, .swap 24 20, .cx 27 31, .cx 27 11, .swap 27 24, .cx 21 5, .cx 20 25, .cx 20 24, .cx 20 22, .cx 20 15, .cx 20 6, .cx 20 5, .cx 23 22, .swap 27 25, .swap 27 22, .cx 34 22, .cx 22 25, .cx 35 34, .ccx 34 35 22, .cx 35 34, .cx 22 25, .cx 22 25, .cx 35 22, .cx 22 25, .ccx 17 21 25]
theorem equiv_wide_moving3 (s : BitVec 37) : run old_wide_moving3 s = run new_wide_moving3 s := by
  simp only [old_wide_moving3, new_wide_moving3, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem resources_wide_moving3 : paid old_wide_moving3 = 3 ∧ paid new_wide_moving3 = 2 ∧ old_wide_moving3.all wireOK = true ∧ new_wide_moving3.all wireOK = true := by decide

def old_cost_atom : List Gate := [.ccx 5 19 23, .cx 19 33, .cx 15 33, .cx 0 33, .cx 18 33, .cx 12 33, .ccx 5 19 33, .cx 19 20, .cx 15 20, .cx 13 20, .cx 18 20, .cx 30 20, .cx 3 20, .cx 12 20, .cx 31 20, .cx 14 20, .ccx 5 19 20]
def new_cost_atom : List Gate := [.cx 19 33, .cx 15 33, .cx 0 33, .cx 18 33, .cx 12 33, .cx 19 20, .cx 15 20, .cx 13 20, .cx 18 20, .cx 30 20, .cx 3 20, .cx 12 20, .cx 31 20, .cx 14 20, .cx 20 23, .cx 20 33, .ccx 5 19 20, .cx 20 33, .cx 20 23]
theorem equiv_cost_atom (s : BitVec 37) : run old_cost_atom s = run new_cost_atom s := by
  simp only [old_cost_atom, new_cost_atom, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem resources_cost_atom : paid old_cost_atom = 3 ∧ paid new_cost_atom = 1 ∧ old_cost_atom.all wireOK = true ∧ new_cost_atom.all wireOK = true := by decide

def old_wide_atom : List Gate := [.ccx 31 35 22, .ccx 31 35 17, .cx 20 23, .cx 20 22, .cx 20 17, .cx 19 32, .cx 19 30, .ccx 31 35 19]
def new_wide_atom : List Gate := [.cx 20 23, .cx 20 22, .cx 20 17, .cx 19 32, .cx 19 30, .cx 17 19, .cx 17 22, .ccx 31 35 17, .cx 17 22, .cx 17 19]
theorem equiv_wide_atom (s : BitVec 37) : run old_wide_atom s = run new_wide_atom s := by
  simp only [old_wide_atom, new_wide_atom, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem resources_wide_atom : paid old_wide_atom = 3 ∧ paid new_wide_atom = 1 ∧ old_wide_atom.all wireOK = true ∧ new_wide_atom.all wireOK = true := by decide

end GVQCC.MovingTensorV10
