import Mathlib

namespace GVQCC.TransposedMiddle
open scoped BigOperators

section Tensor
variable {F : Type*} [Field F]

/-- Transpose the interpolation of the product of the target-dual polynomial
and the reversed payload. Only l+r-1 evaluations are needed, provided the
monomial reconstruction matrix is an inverse evaluation matrix. -/
theorem middle_basis {l r : ℕ} (hl : 0 < l) (hr : 0 < r)
    (x : Fin (l+r-1) → F)
    (w : Fin (l+r-1) → Fin (l+r-1) → F)
    (h : ∀ a : Fin (l+r-1), ∀ d : ℕ, d < l+r-1 →
      (∑ z, w z a * x z ^ d) = if a.val = d then 1 else 0)
    (a : Fin (l+r-1)) (b : Fin r) (i : Fin l) :
    (∑ z, w z a * x z ^ (r-1-b.val) * x z ^ i.val) =
      (if a.val+b.val = r-1+i.val then 1 else 0) := by
  have hb := b.isLt
  have hi := i.isLt
  have hd : r-1-b.val+i.val < l+r-1 := by omega
  have he : a.val = r-1-b.val+i.val ↔ a.val+b.val = r-1+i.val := by omega
  calc
    _ = ∑ z, w z a * x z ^ (r-1-b.val+i.val) := by
      apply Finset.sum_congr rfl
      intro z hz
      rw [pow_add]
      ring
    _ = _ := by rw [h a _ hd]; simp [he]

/-- Truncated convolution is the projection of the ordinary polynomial
product after 2n-1 point interpolation. -/
theorem truncated_basis {n : ℕ} (hn : 0 < n)
    (x : Fin (2*n-1) → F) (w : Fin (2*n-1) → Fin n → F)
    (h : ∀ i : Fin n, ∀ d : ℕ, d < 2*n-1 →
      (∑ z, w z i * x z ^ d) = if i.val = d then 1 else 0)
    (a b i : Fin n) :
    (∑ z, x z ^ a.val * x z ^ b.val * w z i) =
      (if i.val = a.val+b.val then 1 else 0) := by
  have ha := a.isLt
  have hb := b.isLt
  have hd : a.val+b.val < 2*n-1 := by omega
  calc
    _ = ∑ z, w z i * x z ^ (a.val+b.val) := by
      apply Finset.sum_congr rfl
      intro z hz
      rw [pow_add]
      ring
    _ = _ := h i _ hd

/-- Tensor factorization on coefficient basis vectors extends to all
payloads by bilinearity, not just the tested basis vectors. -/
theorem bilinear_accumulation {I J Z : Type*} [Fintype I] [Fintype J] [Fintype Z]
    (c : I → F) (p : J → F) (u : Z → I → F) (v : Z → J → F)
    (w : Z → F) (T : I → J → F)
    (h : ∀ a b, T a b = ∑ z, u z a * v z b * w z) :
    (∑ a, ∑ b, c a * p b * T a b) =
      ∑ z, (∑ a, c a * u z a) * (∑ b, p b * v z b) * w z := by
  symm
  calc
    _ = ∑ z, ∑ a, ∑ b, (c a * p b) * (u z a * v z b * w z) := by
      apply Finset.sum_congr rfl
      intro z _
      simp only [Finset.sum_mul, Finset.mul_sum]
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro a _
      apply Finset.sum_congr rfl
      intro b _
      ring
    _ = ∑ a, ∑ b, ∑ z, (c a * p b) * (u z a * v z b * w z) := by
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro a _
      rw [Finset.sum_comm]
    _ = _ := by
      apply Finset.sum_congr rfl
      intro a _
      apply Finset.sum_congr rfl
      intro b _
      rw [← Finset.mul_sum, h]

end Tensor

section Ring
variable {R : Type*} [CommRing R]

/-- Characteristic-two squaring has no mixed coefficient. -/
theorem square_no_cross (a b : R) (h2 : (2:R)=0) :
    (a+b)^2 = a^2+b^2 := by
  calc
    _ = a^2+b^2+2*(a*b) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

/-- A block update on disjoint live target words is a reversible shear. -/
theorem shear_restore (a b c : R) (h2 : (2:R)=0) :
    (a+b*c)+b*c = a := by
  calc
    _ = a+2*(b*c) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

/-- In a quadratic tower, the cached norm depends only on the scalar. -/
theorem retained_norm (a b beta k : R) (h2 : (2:R)=0) (hb : beta^2+beta=k) :
    (a+b*beta)*(a+b*(beta+1))=a^2+a*b+k*b^2 := by
  calc
    _ = a^2+a*b+(beta^2+beta)*b^2+2*(a*b*beta) := by ring
    _ = _ := by rw [hb,h2,zero_mul,add_zero]

/-- HMR phase debt of a retained function can be repaid once. -/
theorem phase_repay (m f : R) (h2 : (2:R)=0) :
    m*f+m*f=0 := by
  calc
    _ = 2*(m*f) := by ring
    _ = _ := by rw [h2,zero_mul]

end Ring

theorem middle_count_8_9 : 8+9-1=16 := by decide
theorem trunc_count_17 : 2*17-1=33 := by decide
theorem reciprocal_cache_cost : 66+36=102 ∧ 66+21=87 ∧ 66+18=84 := by decide
theorem integrated_cost : 2*96462-2*79632=33660 := by decide
theorem native_seam_budget : 852+33+1+13=899 := by decide

#print axioms middle_basis
#print axioms truncated_basis
#print axioms bilinear_accumulation
#print axioms square_no_cross
#print axioms shear_restore
#print axioms retained_norm
#print axioms phase_repay
#print axioms middle_count_8_9
#print axioms trunc_count_17
#print axioms reciprocal_cache_cost
#print axioms integrated_cost
#print axioms native_seam_budget
end GVQCC.TransposedMiddle
