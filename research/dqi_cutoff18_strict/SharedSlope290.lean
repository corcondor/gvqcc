import Mathlib

namespace GVQCC.SharedSlope290

theorem sentinel_comparator (a : Nat) (h : a ≤ 4095) :
    min a 4095 = a ∧ max a 4095 = 4095 :=
  ⟨min_eq_left h, max_eq_right h⟩

theorem truncated_count_safe (n baseline : Nat) (h : baseline < n % 32) :
    baseline < n := lt_of_lt_of_le h (Nat.mod_le n 32)

theorem count_lower_bound (n : Nat) : n % 32 ≤ n := Nat.mod_le n 32

theorem strict_leaf_reduction (N old actual : Nat)
    (h : old < actual % 32) (ha : actual ≤ N) :
    11 * (N - actual) < 11 * (N - old) := by
  have h' := truncated_count_safe actual old h
  omega

theorem count_preserved_by_swap (a b target : Nat) :
    (if a = target then 1 else 0) + (if b = target then 1 else 0) =
    (if b = target then 1 else 0) + (if a = target then 1 else 0) := by
  omega

-- Algebraic phase multiplex identity only: not a physical KMB certificate.
theorem exclusive_phase (l m a b : Bool) :
    (l && m) = false →
    Bool.xor (l && a) (m && b) = (if l then a else if m then b else false) := by
  cases l <;> cases m <;> cases a <;> cases b <;> decide

theorem instruction_reduction : 67262375 - 66786263 = 476112 := by decide

#print axioms sentinel_comparator
#print axioms truncated_count_safe
#print axioms count_lower_bound
#print axioms strict_leaf_reduction
#print axioms count_preserved_by_swap
#print axioms exclusive_phase
#print axioms instruction_reduction

end GVQCC.SharedSlope290
