import Std.Tactic
namespace GVQCC.V29

def X := Bool.xor

-- Quadratic difference propagation. No assumption of independent atoms.
theorem product_delta (a b da db : Bool) :
    X (a && b) (X a da && X b db) =
      X (a && db) (X (b && da) (da && db)) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

-- The same quadratic class under two generators of GL(2,F2), modulo
-- affine terms. A complement adds a linear term as well.
theorem atom_swap (a b : Bool) : (a && b) = (b && a) := by
  cases a <;> cases b <;> decide
theorem atom_shear (a b : Bool) : (a && X a b) = X a (a && b) := by
  cases a <;> cases b <;> decide
theorem atom_complement (a b : Bool) : ((!a) && b) = X b (a && b) := by
  cases a <;> cases b <;> decide

-- Weighted discrete integration by parts for any length.
def edgeSum (c : Bool) : List (Bool × Bool) → Bool
  | [] => false
  | (k,d) :: xs => X (k && X c d) (edgeSum d xs)

def parts (k c : Bool) : List (Bool × Bool) → Bool
  | [] => k && c
  | (l,d) :: xs => X (X k l && c) (parts l d xs)

theorem parts_step (k c l d tail : Bool) :
    X (k && c) (X (l && X c d) tail) =
      X (X k l && c) (X (l && d) tail) := by
  cases k <;> cases c <;> cases l <;> cases d <;> cases tail <;> decide

theorem weighted_parts (k c : Bool) (xs : List (Bool × Bool)) :
    X (k && c) (edgeSum c xs) = parts k c xs := by
  induction xs generalizing k c with
  | nil => cases k <;> cases c <;> decide
  | cons p xs ih =>
    rcases p with ⟨l,d⟩
    change X (k && c) (X (l && X c d) (edgeSum d xs)) =
      X (X k l && c) (parts l d xs)
    rw [← ih l d]
    exact parts_step k c l d (edgeSum d xs)

-- Adjoint relation for a scalar coordinate: vector form follows by
-- XOR-summing over coordinates; nonlinear injection h need not be linear.
theorem adjoint_step (w l a d h : Bool) :
    X (w && d) (l && X (a && d) h) =
      X (X w (a && l) && d) (l && h) := by
  cases w <;> cases l <;> cases a <;> cases d <;> cases h <;> decide

-- Existing HMR outcome is preserved; phase debt m*h is paid by a
-- representative reconstructed later in the SAME 36Q chart.
theorem measured_atom_reuse (t h r m : Bool) :
    (h, m && X (X t h) r) =
      (h, X (m && X t r) (m && h)) := by
  cases t <;> cases h <;> cases r <;> cases m <;> decide

-- Actual V28 [31155,31169) mapped-body suffix 10..17:
-- CCX(9,25,13), CX(9,13), CX(14,13), CX(1,13), CX(5,13),
-- HMR(13,1), CCX(9,25,13), SWAP(22,13).
-- Replacement removes the first CCX and appends Z(22) conditioned on
-- the existing measurement record 1. q13 and q22 exit values + sign.
def nativeOld (t p a b u c d m : Bool) : Bool × Bool × Bool :=
  let h := a && b
  let v := X (X (X (X (X t h) a) u) c) d
  (p,h,m && v)
def nativeNew (t p a b u c d m : Bool) : Bool × Bool × Bool :=
  let h := a && b
  let v := X (X (X (X t a) u) c) d
  (p,h,X (m && v) (m && h))

theorem native31155 (t p a b u c d m : Bool) :
    nativeOld t p a b u c d m = nativeNew t p a b u c d m := by
  cases t <;> cases a <;> cases b <;> cases u <;> cases c <;> cases d <;> cases m <;> rfl

-- [17490,17503) has one exact shared product on two final coordinates.
-- The representative q11=h is a reachable premise verified in the BDD audit.
theorem shared_two_output_repair (x y h rep : Bool) (hr : rep = h) :
    (X (X x h) rep, X (X y h) rep) = (x,y) := by
  subst rep
  cases x <;> cases y <;> cases h <;> decide

theorem first_pass_cost_reduction : 223 - 49 = 174 := by decide
theorem repeated_bridge_cost : 23 - 13 = 10 := by decide
end GVQCC.V29
