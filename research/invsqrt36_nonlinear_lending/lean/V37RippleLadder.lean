import Std.Tactic
namespace GVQCC.V37
def x (a b : Bool) : Bool := Bool.xor a b
def carry (a b c : Bool) : Bool := x (x (a && b) (a && c)) (b && c)
def majCarry (a b c : Bool) : Bool := x a (x b a && x c a)
def recover (v bp cp : Bool) : Bool × Bool × Bool :=
  let a := x v (bp && cp)
  let c := x cp a
  (a, x bp c, c)
theorem majority_eq (a b c : Bool) : majCarry a b c = carry a b c := by
  cases a <;> cases b <;> cases c <;> decide
theorem maj_uma (a b c : Bool) :
    recover (majCarry a b c) (x b a) (x c a) = (a, x (x a b) c, c) := by
  cases a <;> cases b <;> cases c <;> decide
def reference (c : Bool) : List (Bool × Bool) → List (Bool × Bool) × Bool
  | [] => ([], c)
  | (a,b) :: xs =>
      let r := reference (carry a b c) xs
      ((a, x (x a b) c) :: r.1, r.2)
def ladder (c : Bool) : List (Bool × Bool) → List (Bool × Bool) × Bool
  | [] => ([], c)
  | (a,b) :: xs =>
      let v := majCarry a b c
      let r := ladder v xs
      let z := recover v (x b a) (x c a)
      ((z.1,z.2.1) :: r.1, r.2)
theorem ladder_correct (xs : List (Bool × Bool)) (c : Bool) :
    ladder c xs = reference c xs := by
  induction xs generalizing c with
  | nil => rfl
  | cons ab xs ih =>
    rcases ab with ⟨a,b⟩
    simp only [ladder, reference, maj_uma]
    rw [ih, majority_eq]
theorem reverse_chart (a b c : Bool) :
    x (x (a && b) c) ((!b) && a) = x a c := by
  cases a <;> cases b <;> cases c <;> decide
theorem reverse_phase (a c m : Bool) : x (m && a) (m && x a c) = (m && c) := by
  cases a <;> cases c <;> cases m <;> decide
theorem clean_presample (m c : Bool) : x (m && false) (m && c) = (m && c) := by
  cases m <;> cases c <;> decide
theorem dirty_bridge (a b d t v : Bool) :
    x (x d (a && b)) (a && b) = d ∧
    x v (t && x d (a && b)) = x (x v (t && d)) (t && a && b) := by
  cases a <;> cases b <;> cases d <;> cases t <;> cases v <;> decide
theorem phase_pair (m p : Bool) : x (m && p) (m && p) = false := by
  cases m <;> cases p <;> decide
end GVQCC.V37
