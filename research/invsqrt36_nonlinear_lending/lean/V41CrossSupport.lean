import Std
namespace V41
def bx (a b : Bool) : Bool := Bool.xor a b
def evalPhase (xs : List Bool) : Bool :=
  match xs with
  | [] => false
  | x :: tail => bx x (evalPhase tail)

theorem xor_assoc (a b c : Bool) :
    bx (bx a b) c = bx a (bx b c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem eval_append (xs ys : List Bool) :
    evalPhase (xs ++ ys) = bx (evalPhase xs) (evalPhase ys) := by
  induction xs with
  | nil =>
    change evalPhase ys = bx false (evalPhase ys)
    cases h : evalPhase ys <;> simp [h, bx]
  | cons a xs ih =>
    simp only [List.cons_append, evalPhase, ih]
    exact (xor_assoc a (evalPhase xs) (evalPhase ys)).symm

theorem kernel_union (xs ys : List Bool)
    (h : evalPhase xs = false) (k : evalPhase ys = false) :
    evalPhase (xs ++ ys) = false := by
  rw [eval_append, h, k]
  rfl

-- Two supports can share a monomial even if their support sets differ.
theorem cancel_shared_atom (a b c : Bool) :
    bx (bx a b) (bx b c) = bx a c := by
  cases a <;> cases b <;> cases c <;> decide

-- If an updated nonlinear target is an affine residual r, measure its old
-- value and correct both the product and the residual. Their XOR is zero.
theorem reset_debt (m t a b r : Bool)
    (h : r = bx t (a && b)) :
    bx (m && t) (bx (m && (a && b)) (m && r)) = false := by
  subst r
  cases m <;> cases t <;> cases a <;> cases b <;> decide

-- Phase debt telescopes under transported writes.
theorem carry_phase (m x y : Bool) :
    bx (m && x) (m && bx x y) = (m && y) := by
  cases m <;> cases x <;> cases y <;> decide

theorem direct_record (m : Bool) :
    (if m then true else false) = m := by
  cases m <;> decide

end V41
