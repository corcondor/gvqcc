import Init
import Std
namespace GVQCC.FFTSeam316
variable {F : Type}
variable (add mul : F → F → F) (zero one : F)
/-- Additive-subspace split: the high half contributes t on the left
    and t+1 on the right; the two visits share the same high half. -/
theorem butterfly_right (l h t : F)
    (assoc : ∀ a b c, add (add a b) c = add a (add b c))
    (distrib : ∀ a b c, mul (add a b) c = add (mul a c) (mul b c))
    (unit : ∀ a, mul one a = a) :
    add (add l (mul t h)) h = add l (mul (add t one) h) := by
  rw [distrib, unit, assoc]
/-- Three shears restore the low word after the two recursive visits,
    assuming the high word is unchanged. -/
theorem butterfly_restore (l h t : F)
    (assoc : ∀ a b c, add (add a b) c = add a (add b c))
    (distrib : ∀ a b c, mul (add a b) c = add (mul a c) (mul b c))
    (unit : ∀ a, mul one a = a)
    (cancel : ∀ a, add a a = zero)
    (identity : ∀ a, add a zero = a) :
    add (add (add l (mul t h)) h) (mul (add t one) h) = l := by
  rw [butterfly_right add mul one l h t assoc distrib unit, assoc, cancel, identity]
/-- When the active degree is below the split, all high coefficients
    are outside the represented polynomial. No shear is required. -/
theorem inactive_split (l t : F)
    (mulzero : ∀ a, mul a zero = zero)
    (identity : ∀ a, add a zero = a) :
    add l (mul t zero) = l := by rw [mulzero, identity]
theorem zero_mask_skip (p : Bool) : Bool.xor p false = p := by
  cases p <;> decide
#print axioms butterfly_right
#print axioms butterfly_restore
#print axioms inactive_split
#print axioms zero_mask_skip
end GVQCC.FFTSeam316
