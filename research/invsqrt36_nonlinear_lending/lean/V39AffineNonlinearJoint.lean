import Std
namespace V39
def x (a b : Bool) : Bool := Bool.xor a b

-- Whole-oracle semantic phase relations: cancel across any intervening
-- operations, provided the evaluations are equal on the actual trajectories.
theorem phase_pair (p q : Bool) : x (x p q) q = p := by
  cases p <;> cases q <;> decide
theorem phase_triple (p a b : Bool) :
    x (x (x p a) b) (x a b) = p := by
  cases p <;> cases a <;> cases b <;> decide

-- Shared-control factor, both CCX use the same target. The basis change
-- is its own inverse. The guarded version is identical in each branch.
def shareTarget (a b c t : Bool) : Bool :=
  x (x t (a && b)) (a && c)
theorem share_target (a b c t : Bool) :
    shareTarget a b c t = x t (a && x b c) := by
  cases a <;> cases b <;> cases c <;> cases t <;> decide
theorem share_target_guarded (g a b c t : Bool) :
    x (x t (g && (a && b))) (g && (a && c)) =
      x t (g && (a && x b c)) := by
  cases g <;> cases a <;> cases b <;> cases c <;> cases t <;> decide

-- One shared product, two targets, emitted CNOT / CCX / CNOT.
theorem share_product (a b t u : Bool) :
    (x t (a && b), x u (a && b)) =
      (x t (a && b), x (x u t) (x t (a && b))) := by
  cases a <;> cases b <;> cases t <;> cases u <;> decide

-- CNOT row operation and the affine basis change are involutions.
theorem row_involution (a b : Bool) : x (x b a) a = b := by
  cases a <;> cases b <;> decide
theorem row_distributivity (a b c : Bool) :
    x (a && c) (b && c) = (x a b && c) := by
  cases a <;> cases b <;> cases c <;> decide

-- Phase transport by a shared nonlinear product.
theorem delta_product (u v a b : Bool) :
    (x u (a && b) && x v (a && b)) =
      x (u && v) ((a && b) && x (x u v) true) := by
  cases u <;> cases v <;> cases a <;> cases b <;> decide
end V39
