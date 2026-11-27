import Mathlib

namespace GVQCC
open scoped BigOperators

/-- A mask in the dual span of the syndrome map needs no decoding. -/
theorem dualMaskFactorization
    {F I J : Type*} [CommSemiring F] [Fintype I] [Fintype J]
    (e : I → F) (c : J → F) (h : J → I → F) :
    (∑ x, e x * (∑ i, c i * h i x)) =
    ∑ i, c i * (∑ x, e x * h i x) := by
  calc
    _ = ∑ x, ∑ i, e x * (c i * h i x) := by
      simp only [Finset.mul_sum]
    _ = ∑ i, ∑ x, e x * (c i * h i x) := Finset.sum_comm
    _ = _ := by
      apply Finset.sum_congr rfl
      intro i _
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro x _
      ring

#print axioms dualMaskFactorization
end GVQCC
