import Std.Tactic
namespace GVQCC.V56
def x (a b : Bool) : Bool := Bool.xor a b
def b (a : Bool) : Nat := if a then 1 else 0
def lo (p q r : Bool) : Bool := x (x p q) r
def hi (p q r : Bool) : Bool := x (x (p && q) (q && r)) (r && p)
theorem carry3 (p q r : Bool) :
    b p + b q + b r = b (lo p q r) + 2 * b (hi p q r) := by
  cases p <;> cases q <;> cases r <;> decide
theorem weighted_carry3 (w : Nat) (p q r : Bool) :
    w * b p + w * b q + w * b r =
      w * b (lo p q r) + (2*w) * b (hi p q r) := by
  cases p <;> cases q <;> cases r <;> simp [b, lo, hi, x] <;> omega
theorem carry3_majority_factored (p q r : Bool) :
    hi p q r = x q (x p q && x q r) := by
  cases p <;> cases q <;> cases r <;> decide
theorem pair_carry (w : Nat) (p q : Bool) :
    w*b p + w*b q = w*b (x p q) + (2*w)*b (p && q) := by
  cases p <;> cases q <;> simp [b, x] <;> omega
theorem complement_weight (w : Nat) (p : Bool) : w*b p + w*b (!p) = w := by
  cases p <;> simp [b]
theorem shear (u v : Bool) : (u && v) = x u (u && x u v) := by
  cases u <;> cases v <;> decide
theorem gauge_flip (a u v : Bool) : x a (u && v) = x (x a v) ((!u) && v) := by
  cases a <;> cases u <;> cases v <;> decide
theorem shared_prefix (p q : Bool) : (p && !q) = x p (p && q) := by
  cases p <;> cases q <;> decide
theorem factor_fanout (t z f : Bool) :
    x (x z t) (x t f) = x z f := by
  cases t <;> cases z <;> cases f <;> decide
theorem hmr_adjoint (m a u v : Bool) :
    x (m && x a (u && v)) (x (m && a) (m && u && v)) = false := by
  cases m <;> cases a <;> cases u <;> cases v <;> decide
end GVQCC.V56
