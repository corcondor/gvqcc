import Mathlib
namespace GVQCC.PackedContinuedFraction
theorem continuant_inverse {R : Type*} [CommRing R] (q n d : R) :
    (q*d+n)-q*d = n := by ring
theorem continuant_coprime_witness {R : Type*} [CommRing R]
    (q n d a b : R) (h : a*n+b*d=1) :
    a*(q*d+n)+(b-a*q)*d=1 := by
  calc
    _ = a*n+b*d := by ring
    _ = 1 := h
theorem packed_words (k r : ℕ) (hk : 0 < k) :
    r+r+(k+1)+(k-1)=2*(r+k) := by omega
theorem full_frame (i k : ℕ) (h : i+k ≤ 35) :
    2*i+2*(k+(35-i-k))=70 := by omega
theorem odd_power_composition {R : Type*} [Monoid R] (a : R) :
    ((a^3)^5)^17 = a^255 := by
  simp only [← pow_mul]
  norm_num
theorem odd_power_inverse {R : Type*} [Monoid R] (a : R)
    (h : a^256=1) : ((a^3)^5)^17*a=1 := by
  rw [odd_power_composition, ← pow_succ]
  exact h
#print axioms continuant_inverse
#print axioms continuant_coprime_witness
#print axioms packed_words
#print axioms full_frame
#print axioms odd_power_composition
#print axioms odd_power_inverse
end GVQCC.PackedContinuedFraction
