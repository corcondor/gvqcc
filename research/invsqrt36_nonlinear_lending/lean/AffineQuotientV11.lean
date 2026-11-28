import Std.Tactic.BVDecide
set_option maxRecDepth 65536
set_option maxHeartbeats 0
namespace GVQCC.AffineQuotientV11
inductive Gate where
  | cx (a t : Nat)
  | swap (a b : Nat)
  | ccx (a b t : Nat)
  deriving DecidableEq, Repr
def bit (s : BitVec 37) (q : Nat) : BitVec 37 := (s >>> q) &&& 1
def toggle (s : BitVec 37) (q : Nat) (v : BitVec 37) : BitVec 37 :=
  s ^^^ ((v &&& 1) <<< q)
def step (s : BitVec 37) : Gate → BitVec 37
  | .cx a t => toggle s t (bit s a)
  | .swap a b => toggle (toggle s a (bit s a ^^^ bit s b)) b (bit s a ^^^ bit s b)
  | .ccx a b t => toggle s t (bit s a &&& bit s b)
def run (gs : List Gate) (s : BitVec 37) : BitVec 37 := gs.foldl step s
def paid : List Gate → Nat
  | [] => 0
  | .ccx _ _ _ :: gs => 1 + paid gs
  | _ :: gs => paid gs
def legal36 : Gate → Bool
  | .cx a t => decide (a < 36 ∧ t < 36 ∧ a ≠ t)
  | .swap a b => decide (a < 36 ∧ b < 36 ∧ a ≠ b)
  | .ccx a b t => decide (a < 36 ∧ b < 36 ∧ t < 36 ∧ a ≠ b ∧ a ≠ t ∧ b ≠ t)

def old_cost6020 : List Gate := [.ccx 0 23 7, .cx 8 7, .cx 8 23, .cx 34 7, .cx 34 23, .cx 15 0, .ccx 0 23 33, .cx 23 33, .cx 23 8, .cx 33 7, .cx 0 23, .cx 34 8, .cx 15 0, .ccx 0 8 23]
def new_cost6020 : List Gate := [.cx 15 0, .cx 23 8, .cx 34 8, .ccx 0 8 33, .cx 34 8, .cx 23 8, .cx 15 0, .cx 8 33, .ccx 0 23 8, .cx 8 33, .cx 34 8, .cx 33 7, .cx 23 8, .cx 23 7, .cx 15 33, .cx 15 8, .cx 8 33, .swap 23 8, .cx 0 23]
theorem eq_cost6020 (s : BitVec 37) : run old_cost6020 s = run new_cost6020 s := by
  simp only [old_cost6020, new_cost6020, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost6020 : old_cost6020.all legal36 = true ∧ new_cost6020.all legal36 = true ∧ paid old_cost6020 = 3 ∧ paid new_cost6020 = 2 ∧ old_cost6020.length = 14 ∧ new_cost6020.length = 19 := by decide

def old_wide6572 : List Gate := [.ccx 18 19 27, .cx 28 27, .cx 28 19, .cx 21 27, .cx 21 19, .cx 20 18, .ccx 18 19 35, .cx 19 35, .cx 19 28, .cx 35 27, .swap 19 28, .cx 18 28, .cx 21 19, .cx 20 18, .ccx 18 19 28]
def new_wide6572 : List Gate := [.cx 20 18, .cx 21 19, .cx 28 19, .ccx 18 19 35, .cx 28 19, .cx 21 19, .cx 20 18, .cx 28 35, .cx 19 18, .ccx 18 19 28, .cx 19 18, .cx 28 35, .cx 35 27, .cx 28 35, .cx 21 35, .cx 21 28, .cx 20 28, .cx 19 35, .cx 18 28]
theorem eq_wide6572 (s : BitVec 37) : run old_wide6572 s = run new_wide6572 s := by
  simp only [old_wide6572, new_wide6572, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide6572 : old_wide6572.all legal36 = true ∧ new_wide6572.all legal36 = true ∧ paid old_wide6572 = 3 ∧ paid new_wide6572 = 2 ∧ old_wide6572.length = 15 ∧ new_wide6572.length = 19 := by decide

def old_cost244 : List Gate := [.cx 17 35, .cx 17 1, .cx 17 22, .cx 17 11, .cx 17 13, .cx 1 35]
def new_cost244 : List Gate := [.cx 17 11, .cx 17 13, .cx 17 22, .cx 1 35, .cx 17 1]
theorem eq_cost244 (s : BitVec 37) : run old_cost244 s = run new_cost244 s := by
  simp only [old_cost244, new_cost244, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost244 : old_cost244.all legal36 = true ∧ new_cost244.all legal36 = true ∧ paid old_cost244 = 0 ∧ paid new_cost244 = 0 ∧ old_cost244.length = 6 ∧ new_cost244.length = 5 := by decide

def old_cost430 : List Gate := [.cx 1 35, .cx 1 13, .cx 1 15, .cx 35 33, .cx 33 35, .cx 15 1, .cx 15 13]
def new_cost430 : List Gate := [.cx 1 35, .cx 33 35, .swap 33 35, .swap 1 15, .cx 1 15, .cx 1 13]
theorem eq_cost430 (s : BitVec 37) : run old_cost430 s = run new_cost430 s := by
  simp only [old_cost430, new_cost430, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_cost430 : old_cost430.all legal36 = true ∧ new_cost430.all legal36 = true ∧ paid old_cost430 = 0 ∧ paid new_cost430 = 0 ∧ old_cost430.length = 7 ∧ new_cost430.length = 6 := by decide

def old_wide284 : List Gate := [.cx 6 35, .cx 6 32, .cx 6 22, .cx 6 8, .cx 6 4, .cx 32 35]
def new_wide284 : List Gate := [.cx 6 22, .cx 32 35, .cx 6 32, .cx 6 8, .cx 6 4]
theorem eq_wide284 (s : BitVec 37) : run old_wide284 s = run new_wide284 s := by
  simp only [old_wide284, new_wide284, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide284 : old_wide284.all legal36 = true ∧ new_wide284.all legal36 = true ∧ paid old_wide284 = 0 ∧ paid new_wide284 = 0 ∧ old_wide284.length = 6 ∧ new_wide284.length = 5 := by decide

def old_wide290 : List Gate := [.cx 0 22, .cx 0 8, .cx 0 6, .swap 0 35, .cx 8 22, .cx 8 6]
def new_wide290 : List Gate := [.cx 8 6, .cx 8 22, .cx 0 8, .swap 0 35]
theorem eq_wide290 (s : BitVec 37) : run old_wide290 s = run new_wide290 s := by
  simp only [old_wide290, new_wide290, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide
theorem res_wide290 : old_wide290.all legal36 = true ∧ new_wide290.all legal36 = true ∧ paid old_wide290 = 0 ∧ paid new_wide290 = 0 ∧ old_wide290.length = 6 ∧ new_wide290.length = 4 := by decide
-- Exact local Boolean phase identity of the virtual82 macro.
-- q36 initially zero, a=q27,b=q28,c=q25 immediately before CCX.
-- y=q18 after the source CX(2,18); u,v are the restored data values.
-- This lemma concerns the phase polynomial, not the whole HMR instrument.
theorem virtual82_phase (a b c x y m : Bool) :
    let f := Bool.xor (Bool.xor (a && b) a) c
    let u := Bool.xor a c
    let v := !(Bool.xor b u)
    let p := !(Bool.xor x y)
    let corr := Bool.xor (Bool.xor (Bool.xor (Bool.xor c u) (c && v)) (c && u)) (u && v)
    Bool.xor (Bool.xor (f && p) (m && f)) (m && corr) =
      Bool.xor (Bool.xor ((a && b) && p) (a && p)) (c && p) := by
  bv_decide

theorem sink_phase (t a b m g : Bool) :
    (Bool.xor t (g && a && b) && m) =
      Bool.xor (t && m) (g && a && b && m) := by bv_decide

end GVQCC.AffineQuotientV11
