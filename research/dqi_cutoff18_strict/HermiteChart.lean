import Mathlib

namespace GVQCC.HermiteChart
open scoped BigOperators
open Polynomial
variable {F : Type*} [Field F]

/-- Hermite residues determine a rational function under the strict cross-degree
bound, provided the cross numerator vanishes modulo the Hermite modulus. -/
theorem cross_unique (n₁ d₁ n₂ d₂ h : Polynomial F)
    (hd : h ∣ n₁*d₂-n₂*d₁)
    (hl : (n₁*d₂-n₂*d₁).natDegree < h.natDegree) :
    n₁*d₂ = n₂*d₁ := by
  apply sub_eq_zero.mp
  by_contra hn
  exact (not_le_of_gt hl) (Polynomial.natDegree_le_of_dvd hd hn)

theorem translated_value (n d c : F) (hd : d ≠ 0) :
    (n+c*d)/d = n/d+c := by
  field_simp

/-- A degree-zero offset in a rational function leaves its derivative unchanged:
the formal quotient numerator acquires two cancelling terms. -/
theorem translated_derivative (n d np dp c : F) :
    (np+c*dp)*d-(n+c*d)*dp = np*d-n*dp := by ring

/-- A monic triangular coefficient map preserves equality of prefixes.
This is used for converting a constant error in the Hermite polynomial
into a defect of the last filtered moment only. -/
theorem triangular_prefix (n : ℕ) (a b k : ℕ → F)
    (h : ∀ i, i < n →
      a i + (∑ j ∈ Finset.range i, k (i-j)*a j) =
      b i + (∑ j ∈ Finset.range i, k (i-j)*b j)) :
    ∀ i, i < n → a i = b i := by
  intro i
  induction i using Nat.strong_induction_on with
  | h i ih =>
    intro hi
    have hs : (∑ j ∈ Finset.range i, k (i-j)*a j) =
        (∑ j ∈ Finset.range i, k (i-j)*b j) := by
      apply Finset.sum_congr rfl
      intro j hj
      have hj' := Finset.mem_range.mp hj
      rw [ih j hj' (lt_trans hj' hi)]
    have hh := h i hi
    rw [hs] at hh
    exact add_right_cancel hh

/-- If a moment error is restricted to the final coordinate, all earlier
triangular coefficient coordinates agree. -/
theorem last_only_prefix (n : ℕ) (a b k : ℕ → F)
    (h : ∀ i, i+1 < n →
      a i + (∑ j ∈ Finset.range i, k (i-j)*a j) =
      b i + (∑ j ∈ Finset.range i, k (i-j)*b j)) :
    ∀ i, i+1 < n → a i = b i := by
  have h' : ∀ i, i < n-1 →
      a i + (∑ j ∈ Finset.range i, k (i-j)*a j) =
      b i + (∑ j ∈ Finset.range i, k (i-j)*b j) := by
    intro i hi
    exact h i (by omega)
  intro i hi
  exact triangular_prefix (n-1) a b k h' i (by omega)

/-- Exact phase correction when the erroneous decoded word is known:
the correction is the mask pairing with the difference. This identity does
not assert that the corrupted native decoder actually exposes that word. -/
theorem phase_difference {A : Type*} [AddCommGroup A]
    (L : A →+ ZMod 2) (actual expected : A) :
    L actual + L (expected-actual) = L expected := by
  rw [map_sub]
  ring

end GVQCC.HermiteChart
#print axioms GVQCC.HermiteChart.cross_unique
#print axioms GVQCC.HermiteChart.translated_value
#print axioms GVQCC.HermiteChart.translated_derivative
#print axioms GVQCC.HermiteChart.triangular_prefix
#print axioms GVQCC.HermiteChart.last_only_prefix
#print axioms GVQCC.HermiteChart.phase_difference
