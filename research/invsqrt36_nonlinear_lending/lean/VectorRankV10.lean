import Std.Tactic.BVDecide
set_option maxRecDepth 65536
set_option maxHeartbeats 0
namespace GVQCC.VectorRankV10
inductive Gate where
  | x (q : Nat)
  | cx (a t : Nat)
  | swap (a b : Nat)
  | ccx (a b t : Nat)
  deriving DecidableEq, Repr
def bit (s : BitVec 37) (q : Nat) : BitVec 37 := (s >>> q) &&& 1
def toggle (s : BitVec 37) (q : Nat) (v : BitVec 37) : BitVec 37 := s ^^^ ((v &&& 1) <<< q)
def step (s : BitVec 37) : Gate → BitVec 37
  | .x q => toggle s q 1
  | .cx a t => toggle s t (bit s a)
  | .swap a b => toggle (toggle s a (bit s a ^^^ bit s b)) b (bit s a ^^^ bit s b)
  | .ccx a b t => toggle s t (bit s a &&& bit s b)
def run (gs : List Gate) (s : BitVec 37) : BitVec 37 := gs.foldl step s
def paid : List Gate → Nat
  | [] => 0
  | .ccx _ _ _ :: gs => 1 + paid gs
  | _ :: gs => paid gs
def legal36 : Gate → Bool
  | .x q => decide (q < 36)
  | .cx a t => decide (a < 36 ∧ t < 36 ∧ a ≠ t)
  | .swap a b => decide (a < 36 ∧ b < 36 ∧ a ≠ b)
  | .ccx a b t => decide (a < 36 ∧ b < 36 ∧ t < 36 ∧ a ≠ b ∧ a ≠ t ∧ b ≠ t)
-- All-state equivalence for actual unguarded native gate lists. No reachability assumptions.

def old_cost6125 : List Gate := [.ccx 15 23 7, .cx 34 15, .ccx 22 23 7]
def new_cost6125 : List Gate := [.cx 22 15, .ccx 23 15 7, .cx 22 15, .cx 34 15]
theorem eq_cost6125 (s : BitVec 37) : run old_cost6125 s = run new_cost6125 s := by
  simp only [old_cost6125, new_cost6125, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost6125 : old_cost6125.all legal36 = true ∧ new_cost6125.all legal36 = true ∧ paid old_cost6125 = 2 ∧ paid new_cost6125 = 1 := by decide

def old_cost10980 : List Gate := [.ccx 0 17 21, .ccx 0 17 27]
def new_cost10980 : List Gate := [.cx 21 27, .ccx 17 0 21, .cx 21 27]
theorem eq_cost10980 (s : BitVec 37) : run old_cost10980 s = run new_cost10980 s := by
  simp only [old_cost10980, new_cost10980, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost10980 : old_cost10980.all legal36 = true ∧ new_cost10980.all legal36 = true ∧ paid old_cost10980 = 2 ∧ paid new_cost10980 = 1 := by decide

def old_cost11387 : List Gate := [.ccx 26 31 27, .cx 8 15, .cx 19 15, .cx 12 15, .cx 35 15, .cx 22 15, .cx 18 15, .cx 26 0, .ccx 26 31 27]
def new_cost11387 : List Gate := [.cx 8 15, .cx 19 15, .cx 12 15, .cx 35 15, .cx 22 15, .cx 18 15, .cx 26 0]
theorem eq_cost11387 (s : BitVec 37) : run old_cost11387 s = run new_cost11387 s := by
  simp only [old_cost11387, new_cost11387, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost11387 : old_cost11387.all legal36 = true ∧ new_cost11387.all legal36 = true ∧ paid old_cost11387 = 2 ∧ paid new_cost11387 = 0 := by decide

def old_cost26354 : List Gate := [.ccx 19 34 4, .ccx 19 34 10]
def new_cost26354 : List Gate := [.cx 4 10, .ccx 34 19 4, .cx 4 10]
theorem eq_cost26354 (s : BitVec 37) : run old_cost26354 s = run new_cost26354 s := by
  simp only [old_cost26354, new_cost26354, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost26354 : old_cost26354.all legal36 = true ∧ new_cost26354.all legal36 = true ∧ paid old_cost26354 = 2 ∧ paid new_cost26354 = 1 := by decide

def old_cost28016 : List Gate := [.ccx 5 33 0, .ccx 5 33 35]
def new_cost28016 : List Gate := [.cx 0 35, .ccx 33 5 0, .cx 0 35]
theorem eq_cost28016 (s : BitVec 37) : run old_cost28016 s = run new_cost28016 s := by
  simp only [old_cost28016, new_cost28016, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost28016 : old_cost28016.all legal36 = true ∧ new_cost28016.all legal36 = true ∧ paid old_cost28016 = 2 ∧ paid new_cost28016 = 1 := by decide

def old_cost29885 : List Gate := [.ccx 5 19 23, .cx 2 17, .cx 34 17, .cx 22 33, .cx 2 33, .cx 19 33, .cx 15 33, .cx 25 33, .cx 0 33, .cx 18 33, .cx 16 33, .cx 31 33, .ccx 5 19 33]
def new_cost29885 : List Gate := [.cx 23 33, .ccx 19 5 23, .cx 23 33, .cx 2 17, .cx 34 17, .cx 22 33, .cx 2 33, .cx 19 33, .cx 15 33, .cx 25 33, .cx 0 33, .cx 18 33, .cx 16 33, .cx 31 33]
theorem eq_cost29885 (s : BitVec 37) : run old_cost29885 s = run new_cost29885 s := by
  simp only [old_cost29885, new_cost29885, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost29885 : old_cost29885.all legal36 = true ∧ new_cost29885.all legal36 = true ∧ paid old_cost29885 = 2 ∧ paid new_cost29885 = 1 := by decide

def old_cost31374 : List Gate := [.ccx 5 19 23, .cx 19 33, .cx 15 33, .cx 0 33, .cx 18 33, .cx 12 33, .ccx 5 19 33, .cx 19 20, .cx 15 20, .cx 13 20, .cx 18 20, .cx 30 20, .cx 3 20, .cx 12 20, .cx 31 20, .cx 14 20, .ccx 5 19 20]
def new_cost31374 : List Gate := [.cx 20 23, .cx 20 33, .ccx 19 5 20, .cx 20 33, .cx 20 23, .cx 19 33, .cx 15 33, .cx 0 33, .cx 18 33, .cx 12 33, .cx 19 20, .cx 15 20, .cx 13 20, .cx 18 20, .cx 30 20, .cx 3 20, .cx 12 20, .cx 31 20, .cx 14 20]
theorem eq_cost31374 (s : BitVec 37) : run old_cost31374 s = run new_cost31374 s := by
  simp only [old_cost31374, new_cost31374, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost31374 : old_cost31374.all legal36 = true ∧ new_cost31374.all legal36 = true ∧ paid old_cost31374 = 3 ∧ paid new_cost31374 = 1 := by decide

def old_cost31565 : List Gate := [.ccx 5 19 20, .cx 12 20, .cx 30 20, .cx 18 20, .cx 23 20, .cx 13 20, .cx 15 20, .cx 19 20, .cx 10 20, .cx 20 28, .cx 34 28, .ccx 5 19 28]
def new_cost31565 : List Gate := [.cx 20 28, .ccx 19 5 20, .cx 20 28, .cx 12 20, .cx 30 20, .cx 18 20, .cx 23 20, .cx 13 20, .cx 15 20, .cx 19 20, .cx 10 20, .cx 20 28, .cx 34 28]
theorem eq_cost31565 (s : BitVec 37) : run old_cost31565 s = run new_cost31565 s := by
  simp only [old_cost31565, new_cost31565, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost31565 : old_cost31565.all legal36 = true ∧ new_cost31565.all legal36 = true ∧ paid old_cost31565 = 2 ∧ paid new_cost31565 = 1 := by decide

def old_cost31588 : List Gate := [.ccx 5 19 28, .cx 34 28, .cx 20 28, .cx 10 20, .cx 19 20, .cx 15 20, .cx 13 20, .cx 23 20, .cx 18 20, .cx 30 20, .cx 12 20, .ccx 5 19 20]
def new_cost31588 : List Gate := [.ccx 19 5 20, .cx 34 28, .cx 20 28, .cx 10 20, .cx 19 20, .cx 15 20, .cx 13 20, .cx 23 20, .cx 18 20, .cx 30 20, .cx 12 20]
theorem eq_cost31588 (s : BitVec 37) : run old_cost31588 s = run new_cost31588 s := by
  simp only [old_cost31588, new_cost31588, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost31588 : old_cost31588.all legal36 = true ∧ new_cost31588.all legal36 = true ∧ paid old_cost31588 = 2 ∧ paid new_cost31588 = 1 := by decide

def old_wide6674 : List Gate := [.ccx 20 28 27, .cx 21 20, .ccx 0 28 27]
def new_wide6674 : List Gate := [.cx 20 0, .ccx 28 0 27, .cx 20 0, .cx 21 20]
theorem eq_wide6674 (s : BitVec 37) : run old_wide6674 s = run new_wide6674 s := by
  simp only [old_wide6674, new_wide6674, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide6674 : old_wide6674.all legal36 = true ∧ new_wide6674.all legal36 = true ∧ paid old_wide6674 = 2 ∧ paid new_wide6674 = 1 := by decide

def old_wide12420 : List Gate := [.ccx 10 11 35, .ccx 10 11 0]
def new_wide12420 : List Gate := [.cx 0 35, .ccx 11 10 0, .cx 0 35]
theorem eq_wide12420 (s : BitVec 37) : run old_wide12420 s = run new_wide12420 s := by
  simp only [old_wide12420, new_wide12420, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide12420 : old_wide12420.all legal36 = true ∧ new_wide12420.all legal36 = true ∧ paid old_wide12420 = 2 ∧ paid new_wide12420 = 1 := by decide

def old_wide12526 : List Gate := [.ccx 0 4 2, .swap 1 2, .ccx 3 4 1]
def new_wide12526 : List Gate := [.cx 3 0, .ccx 4 0 2, .cx 3 0, .swap 1 2]
theorem eq_wide12526 (s : BitVec 37) : run old_wide12526 s = run new_wide12526 s := by
  simp only [old_wide12526, new_wide12526, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide12526 : old_wide12526.all legal36 = true ∧ new_wide12526.all legal36 = true ∧ paid old_wide12526 = 2 ∧ paid new_wide12526 = 1 := by decide

def old_wide13160 : List Gate := [.ccx 4 25 35, .cx 23 31, .cx 22 31, .cx 21 31, .cx 20 31, .cx 16 31, .cx 8 31, .cx 4 10, .ccx 4 25 35]
def new_wide13160 : List Gate := [.cx 23 31, .cx 22 31, .cx 21 31, .cx 20 31, .cx 16 31, .cx 8 31, .cx 4 10]
theorem eq_wide13160 (s : BitVec 37) : run old_wide13160 s = run new_wide13160 s := by
  simp only [old_wide13160, new_wide13160, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide13160 : old_wide13160.all legal36 = true ∧ new_wide13160.all legal36 = true ∧ paid old_wide13160 = 2 ∧ paid new_wide13160 = 0 := by decide

def old_wide15121 : List Gate := [.ccx 24 35 26, .ccx 30 33 26, .swap 33 26, .cx 26 18, .cx 34 18, .ccx 24 35 33]
def new_wide15121 : List Gate := [.ccx 33 30 26, .swap 33 26, .cx 26 18, .cx 34 18]
theorem eq_wide15121 (s : BitVec 37) : run old_wide15121 s = run new_wide15121 s := by
  simp only [old_wide15121, new_wide15121, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide15121 : old_wide15121.all legal36 = true ∧ new_wide15121.all legal36 = true ∧ paid old_wide15121 = 3 ∧ paid new_wide15121 = 1 := by decide

def old_wide15477 : List Gate := [.ccx 0 33 2, .cx 18 29, .cx 17 29, .ccx 29 33 2]
def new_wide15477 : List Gate := [.cx 17 0, .cx 18 0, .cx 29 0, .ccx 33 0 2, .cx 29 0, .cx 18 0, .cx 17 0, .cx 18 29, .cx 17 29]
theorem eq_wide15477 (s : BitVec 37) : run old_wide15477 s = run new_wide15477 s := by
  simp only [old_wide15477, new_wide15477, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide15477 : old_wide15477.all legal36 = true ∧ new_wide15477.all legal36 = true ∧ paid old_wide15477 = 2 ∧ paid new_wide15477 = 1 := by decide

def old_wide28136 : List Gate := [.ccx 31 35 22, .ccx 31 35 17, .cx 20 23, .cx 20 22, .cx 20 17, .cx 19 32, .cx 19 30, .ccx 31 35 19]
def new_wide28136 : List Gate := [.cx 17 19, .cx 17 22, .cx 17 30, .cx 17 32, .ccx 35 31 17, .cx 17 32, .cx 17 30, .cx 17 22, .cx 17 19, .cx 20 23, .cx 20 22, .cx 20 17, .cx 19 32, .cx 19 30]
theorem eq_wide28136 (s : BitVec 37) : run old_wide28136 s = run new_wide28136 s := by
  simp only [old_wide28136, new_wide28136, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide28136 : old_wide28136.all legal36 = true ∧ new_wide28136.all legal36 = true ∧ paid old_wide28136 = 3 ∧ paid new_wide28136 = 1 := by decide

def old_wide28210 : List Gate := [.ccx 31 35 15, .ccx 31 35 5]
def new_wide28210 : List Gate := [.cx 5 15, .ccx 35 31 5, .cx 5 15]
theorem eq_wide28210 (s : BitVec 37) : run old_wide28210 s = run new_wide28210 s := by
  simp only [old_wide28210, new_wide28210, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide28210 : old_wide28210.all legal36 = true ∧ new_wide28210.all legal36 = true ∧ paid old_wide28210 = 2 ∧ paid new_wide28210 = 1 := by decide

def old_wide28894 : List Gate := [.ccx 17 21 20, .ccx 34 35 20, .cx 3 20, .cx 9 20, .cx 16 20, .cx 17 20, .swap 24 20, .cx 27 31, .cx 27 11, .swap 27 24, .cx 21 5, .cx 20 25, .cx 20 24, .cx 20 22, .cx 20 15, .cx 20 6, .cx 20 5, .cx 23 22, .swap 27 25, .swap 27 22, .cx 34 22, .ccx 34 35 22]
def new_wide28894 : List Gate := [.ccx 21 17 20, .cx 20 25, .ccx 35 34 20, .cx 20 25, .cx 3 20, .cx 9 20, .cx 16 20, .cx 17 20, .swap 24 20, .cx 27 31, .cx 27 11, .swap 27 24, .cx 21 5, .cx 20 25, .cx 20 24, .cx 20 22, .cx 20 15, .cx 20 6, .cx 20 5, .cx 23 22, .swap 27 25, .swap 27 22, .cx 34 22]
theorem eq_wide28894 (s : BitVec 37) : run old_wide28894 s = run new_wide28894 s := by
  simp only [old_wide28894, new_wide28894, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide28894 : old_wide28894.all legal36 = true ∧ new_wide28894.all legal36 = true ∧ paid old_wide28894 = 3 ∧ paid new_wide28894 = 2 := by decide

def old_wide29799 : List Gate := [.ccx 30 35 11, .ccx 30 35 5]
def new_wide29799 : List Gate := [.cx 5 11, .ccx 35 30 5, .cx 5 11]
theorem eq_wide29799 (s : BitVec 37) : run old_wide29799 s = run new_wide29799 s := by
  simp only [old_wide29799, new_wide29799, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide29799 : old_wide29799.all legal36 = true ∧ new_wide29799.all legal36 = true ∧ paid old_wide29799 = 2 ∧ paid new_wide29799 = 1 := by decide

def old_wide31581 : List Gate := [.ccx 24 28 10, .cx 30 3, .cx 9 3, .cx 33 7, .cx 30 7, .cx 28 7, .cx 26 7, .cx 25 7, .cx 21 7, .cx 19 7, .cx 17 7, .cx 13 7, .ccx 24 28 7]
def new_wide31581 : List Gate := [.cx 7 10, .ccx 28 24 7, .cx 7 10, .cx 30 3, .cx 9 3, .cx 33 7, .cx 30 7, .cx 28 7, .cx 26 7, .cx 25 7, .cx 21 7, .cx 19 7, .cx 17 7, .cx 13 7]
theorem eq_wide31581 (s : BitVec 37) : run old_wide31581 s = run new_wide31581 s := by
  simp only [old_wide31581, new_wide31581, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide31581 : old_wide31581.all legal36 = true ∧ new_wide31581.all legal36 = true ∧ paid old_wide31581 = 2 ∧ paid new_wide31581 = 1 := by decide

def old_wide33019 : List Gate := [.ccx 24 28 10, .swap 20 10, .cx 28 7, .cx 26 7, .cx 21 7, .cx 19 7, .cx 14 7, .ccx 24 28 7]
def new_wide33019 : List Gate := [.cx 7 10, .ccx 28 24 7, .cx 7 10, .swap 20 10, .cx 28 7, .cx 26 7, .cx 21 7, .cx 19 7, .cx 14 7]
theorem eq_wide33019 (s : BitVec 37) : run old_wide33019 s = run new_wide33019 s := by
  simp only [old_wide33019, new_wide33019, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide33019 : old_wide33019.all legal36 = true ∧ new_wide33019.all legal36 = true ∧ paid old_wide33019 = 2 ∧ paid new_wide33019 = 1 := by decide

def old_wide33193 : List Gate := [.ccx 24 28 2, .cx 14 2, .cx 18 2, .cx 19 2, .cx 20 2, .cx 22 2, .cx 26 2, .cx 28 2, .cx 31 2, .cx 2 8, .cx 9 8, .ccx 24 28 8]
def new_wide33193 : List Gate := [.cx 2 8, .ccx 28 24 2, .cx 2 8, .cx 14 2, .cx 18 2, .cx 19 2, .cx 20 2, .cx 22 2, .cx 26 2, .cx 28 2, .cx 31 2, .cx 2 8, .cx 9 8]
theorem eq_wide33193 (s : BitVec 37) : run old_wide33193 s = run new_wide33193 s := by
  simp only [old_wide33193, new_wide33193, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide33193 : old_wide33193.all legal36 = true ∧ new_wide33193.all legal36 = true ∧ paid old_wide33193 = 2 ∧ paid new_wide33193 = 1 := by decide

def old_wide33216 : List Gate := [.ccx 24 28 8, .cx 9 8, .cx 2 8, .cx 31 2, .cx 28 2, .cx 26 2, .cx 22 2, .cx 20 2, .cx 19 2, .cx 18 2, .cx 14 2, .ccx 24 28 2]
def new_wide33216 : List Gate := [.ccx 28 24 2, .cx 9 8, .cx 2 8, .cx 31 2, .cx 28 2, .cx 26 2, .cx 22 2, .cx 20 2, .cx 19 2, .cx 18 2, .cx 14 2]
theorem eq_wide33216 (s : BitVec 37) : run old_wide33216 s = run new_wide33216 s := by
  simp only [old_wide33216, new_wide33216, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide33216 : old_wide33216.all legal36 = true ∧ new_wide33216.all legal36 = true ∧ paid old_wide33216 = 2 ∧ paid new_wide33216 = 1 := by decide

end GVQCC.VectorRankV10
