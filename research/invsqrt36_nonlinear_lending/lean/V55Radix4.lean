import Std.Tactic
namespace GVQCC.V55
def x (a b : Bool) := Bool.xor a b
theorem high_pair_affine (a b : Bool) :
    (a || b) = true → (a && b) = x true (x a b) := by
  cases a <;> cases b <;> decide
theorem two_slice_share (a b c h k : Bool) :
    x (h && a) (k && b) =
      x (x (h && x a c) (k && x b c)) ((x h k) && c) := by
  cases a <;> cases b <;> cases c <;> cases h <;> cases k <;> decide
theorem quadratic_transport (a b da db : Bool) :
    x ((x a da) && (x b db)) (a && b) =
      x (x (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide
theorem abel_transport (m0 m1 f0 f1 : Bool) :
    x (m1 && f1) (m0 && f0) =
      x ((x m1 m0) && f1) (m0 && (x f1 f0)) := by
  cases m0 <;> cases m1 <;> cases f0 <;> cases f1 <;> decide
theorem sibling_transport (p b : Bool) : x (p && !b) p = (p && b) := by
  cases p <;> cases b <;> decide
def lowBound : Nat → Nat
  | 0 => 0
  | n+1 => lowBound n + (n+1)*2^n
theorem discarded_bound17 : lowBound 17 = 2097153 := by decide
theorem discarded_scaled_bound : 16 * 2^17 + 1 = lowBound 17 := by decide
theorem measured_normalize_savings : 390 - 238 = (152 : Nat) := by decide
theorem partial_product_savings : 1581 - 969 = (612 : Nat) := by decide
end GVQCC.V55
