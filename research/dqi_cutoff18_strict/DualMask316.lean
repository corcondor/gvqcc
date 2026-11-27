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

/-- Every evaluation-span shift of an arbitrary mask is a direct syndrome phase.
This is a semantic identity, not a claim that the residual mask is cheap. -/
theorem dualMaskTranslation
    {F I J : Type*} [CommSemiring F] [Fintype I] [Fintype J]
    (e m : I → F) (c : J → F) (h : J → I → F) :
    (∑ x, e x * (m x + ∑ i, c i * h i x)) =
    (∑ x, e x * m x) + ∑ i, c i * (∑ x, e x * h i x) := by
  simp only [mul_add, Finset.sum_add_distrib]
  rw [dualMaskFactorization e c h]

/-- The common factor in a padded rational pair cancels at a simple
physical root; the derivative of the padding term drops out there. -/
theorem paddedRootResidue {F : Type*} [Field F]
    (g dg d dd n : F) (hd : d = 0) (hg : g ≠ 0) :
    (g*n)/(dg*d+g*dd) = n/dd := by
  rw [hd, mul_zero, zero_add]
  by_cases h : dd = 0
  · simp [h]
  · field_simp [hg, h]

/-- Two cubic phases with a shared control plane fold to one product. -/
theorem sharedPhasePlane (a b c d : Bool) :
    Bool.xor (a && b && c) (a && b && d) =
    (a && b && Bool.xor c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

#print axioms dualMaskTranslation
#print axioms paddedRootResidue
#print axioms sharedPhasePlane
#print axioms dualMaskFactorization
end GVQCC
