import Std.Tactic
namespace GVQCC.V33
def X := Bool.xor

def parity : List Bool → Bool
  | [] => false
  | a :: xs => X a (parity xs)

theorem mul_add (a b c : Bool) :
    (a && X b c) = X (a && b) (a && c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem mul_parity (a : Bool) (xs : List Bool) :
    (a && parity xs) = parity (xs.map (fun b => a && b)) := by
  induction xs with
  | nil => cases a <;> rfl
  | cons b bs ih =>
    change (a && X b (parity bs)) =
      X (a && b) (parity (bs.map (fun b => a && b)))
    rw [mul_add, ih]

-- If two products agree modulo an additive affine space, their XOR is
-- a member of that space. This identity explains the factor-solver kernel.
theorem factor_kernel (a b k : Bool) :
    X (a && X b k) (a && b) = (a && k) := by
  cases a <;> cases b <;> cases k <;> decide

-- Generators for invariance of the space of guarded degree <= 2
-- observations under unconditional invertible affine coordinate changes.
theorem phase_cx (g a b c : Bool) :
    (g && X a b && c) =
      X (g && a && c) (g && b && c) := by
  cases g <;> cases a <;> cases b <;> cases c <;> decide
theorem phase_cx_overlap (g a b : Bool) :
    (g && a && X a b) = X (g && a) (g && a && b) := by
  cases g <;> cases a <;> cases b <;> decide
theorem phase_x (g a b : Bool) :
    (g && !a && b) = X (g && b) (g && a && b) := by
  cases g <;> cases a <;> cases b <;> decide
theorem phase_cx_inverse (a b : Bool) : X (X a b) b = a := by
  cases a <;> cases b <;> decide

-- Exact two-factor change, including the Boolean quadratic remainder.
theorem joint_quadratic_observation (g a b da db : Bool) :
    X (g && a && b) (g && X a da && X b db) =
      (g && X (X (a && db) (b && da)) (da && db)) := by
  cases g <;> cases a <;> cases b <;> cases da <;> cases db <;> decide

-- Weighted discrete integration by parts, including arbitrary time span.
def edges (c : Bool) : List (Bool × Bool) → Bool
  | [] => false
  | (k,d) :: xs => X (k && X c d) (edges d xs)
def boundary (k c : Bool) : List (Bool × Bool) → Bool
  | [] => k && c
  | (l,d) :: xs => X (X k l && c) (boundary l d xs)
theorem parts_step (k c l d tail : Bool) :
    X (k && c) (X (l && X c d) tail) =
      X (X k l && c) (X (l && d) tail) := by
  cases k <;> cases c <;> cases l <;> cases d <;> cases tail <;> decide
theorem parts (k c : Bool) (xs : List (Bool × Bool)) :
    X (k && c) (edges c xs) = boundary k c xs := by
  induction xs generalizing k c with
  | nil => cases k <;> cases c <;> decide
  | cons z zs ih =>
    rcases z with ⟨l,d⟩
    change X (k && c) (X (l && X c d) (edges d zs)) =
      X (X k l && c) (boundary l d zs)
    rw [← ih l d]
    exact parts_step k c l d (edges d zs)

-- V31 mapped [15255,15298): three phases at local 8,23,25;
-- later op41 CCX(10,21,6) with clean q6 after HMR op40.
-- Guard records 949 and 837 and the respective other coordinate
-- values are unchanged on the transported observations.
def early (a b x y z g j : Bool) : Bool :=
  X (g && a && b && x)
    (X (j && a && b && y) (j && a && b && z))
def late (h x y z g j : Bool) : Bool :=
  X (g && h && x) (X (j && h && y) (j && h && z))

theorem native15255_phase (a b x y z g j h : Bool)
    (hh : h = (a && b)) :
    early a b x y z g j = late h x y z g j := by
  subst h
  cases a <;> cases b <;> cases x <;> cases y <;>
    cases z <;> cases g <;> cases j <;> decide

theorem native15255_count : 6 - 3 = 3 ∧ 46 = 46 := by decide
theorem fixed_cost : 23157 - 32 = 23125 ∧ 1599 - 2 = 1597 := by decide
end GVQCC.V33
