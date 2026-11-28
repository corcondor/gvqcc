import Mathlib
namespace GVQCC.TransposedMiddle
open scoped BigOperators

theorem middle_entry {F T : Type*} [CommSemiring F] [Fintype T]
    (x : T → F) (lag : T → ℕ → F) (a r j i k : ℕ) (hj : j < r)
    (hd : r - 1 - j + i < k)
    (cert : ∀ d, d < k → (∑ t, lag t a * x t ^ d) = if a = d then 1 else 0) :
    (∑ t, lag t a * x t ^ (r-1-j) * x t ^ i) =
      if a + j = r - 1 + i then 1 else 0 := by
  have h : (a = r - 1 - j + i) ↔ (a + j = r - 1 + i) := by omega
  simp_rw [mul_assoc, ← pow_add]
  rw [cert _ hd, h]

theorem middle_accumulate {F A J T : Type*} [CommSemiring F]
    [Fintype A] [Fintype J] [Fintype T]
    (b : A → F) (p : J → F) (u : T → A → F) (v : T → J → F)
    (w : T → F) (M : A → J → F) (z : F)
    (cert : ∀ a j, (∑ t, u t a * v t j * w t) = M a j) :
    z + (∑ t, (∑ a, b a * u t a) * (∑ j, p j * v t j) * w t) =
      z + ∑ a, ∑ j, (b a * p j) * M a j := by
  congr 1
  calc
    _ = ∑ t, ∑ a, ∑ j, (b a * p j) * (u t a * v t j * w t) := by
      apply Finset.sum_congr rfl
      intro t _
      simp only [Finset.sum_mul, Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro a _
      apply Finset.sum_congr rfl
      intro j _
      ring
    _ = ∑ a, ∑ j, ∑ t, (b a * p j) * (u t a * v t j * w t) := by
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro a _
      rw [Finset.sum_comm]
    _ = _ := by
      apply Finset.sum_congr rfl
      intro a _
      apply Finset.sum_congr rfl
      intro j _
      rw [← Finset.mul_sum, cert]

theorem restore {R : Type*} [CommRing R] (x y : R) (h : (2:R)=0) :
    (x+y)+y=x := by
  calc
    _ = x+2*y := by ring
    _ = _ := by rw [h, zero_mul, add_zero]

theorem residual_additive {A : Type*} [AddCommMonoid A] (f : A → A)
    (x y : A) (h : f (x+y) = f x + f y) :
    f (x+y)+(x+y)=(f x+x)+(f y+y) := by
  rw [h]
  ac_rfl

theorem paid_counts : 122*42=5124 ∧ 108*42=4536 ∧
    5124-4536=588 ∧ 70200-588=69612 := by decide

#print axioms middle_entry
#print axioms middle_accumulate
#print axioms restore
#print axioms residual_additive
#print axioms paid_counts
end GVQCC.TransposedMiddle
