import Mathlib

namespace GVQCC.CrossStageNorm

section Field
variable {F : Type*} [Field F]

def norm64 (a : F) : F := a ^ 65
def invNorm64 (a : F) : F := (norm64 a)⁻¹
def norm8 (a : F) : F := a ^ 9

theorem norm64_mul (a h : F) : norm64 (a*h) = norm64 a * norm64 h := by
  simp [norm64,mul_pow]

theorem norm64_div (a h : F) : norm64 (a/h) = norm64 a / norm64 h := by
  simp [norm64,div_pow]

theorem norm64_fixed (a : F) (h : a^4096 = a) : (norm64 a)^64 = norm64 a := by
  unfold norm64
  calc
    (a^65)^64 = a^4160 := by rw [← pow_mul]
    _ = a^4096*a^64 := by rw [← pow_add]
    _ = a*a^64 := by rw [h]
    _ = a^65 := by rw [← pow_succ']

theorem norm64_ne_zero (a : F) (ha : a ≠ 0) : norm64 a ≠ 0 := by
  exact pow_ne_zero _ ha

theorem norm64_inverse (a : F) : norm64 a⁻¹ = invNorm64 a := by
  simp [norm64,invNorm64,inv_pow]

theorem invnorm_mul (a h : F) :
    invNorm64 (a*h) = invNorm64 a * invNorm64 h := by
  simp [invNorm64,norm64_mul,mul_inv_rev, mul_comm]

theorem invnorm_div (a h : F) :
    invNorm64 (a/h) = invNorm64 a * norm64 h := by
  unfold invNorm64
  rw [norm64_div, div_eq_mul_inv, mul_inv_rev, inv_inv, mul_comm]

theorem invnorm_repay (a h : F) (hh : h ≠ 0) :
    invNorm64 (a*h)*norm64 h = invNorm64 a := by
  rw [invnorm_mul, mul_assoc]
  change invNorm64 a * ((norm64 h)⁻¹ * norm64 h) = invNorm64 a
  rw [inv_mul_cancel₀ (norm64_ne_zero h hh), mul_one]

theorem invnorm_repay_reverse (a h : F) (hh : h ≠ 0) :
    invNorm64 (a/h)*invNorm64 h = invNorm64 a := by
  rw [invnorm_div, mul_assoc]
  change invNorm64 a * (norm64 h * (norm64 h)⁻¹) = invNorm64 a
  rw [mul_inv_cancel₀ (norm64_ne_zero h hh), mul_one]

/-- Form the full inverse only while it is needed. The carried norm is
    independent of how the field element was recovered in Schur. -/
theorem reconstruct_inverse (a : F) (ha : a ≠ 0) :
    a^64 * invNorm64 a = a⁻¹ := by
  unfold invNorm64 norm64
  apply (mul_left_cancel₀ ha)
  rw [mul_inv_cancel₀ ha, ← mul_assoc, ← pow_succ']
  exact mul_inv_cancel₀ (pow_ne_zero _ ha)

theorem transported_inverse (a h : F) (ha : a ≠ 0) (hh : h ≠ 0) :
    (a*h)^64*(invNorm64 a*invNorm64 h) = (a*h)⁻¹ := by
  rw [← invnorm_mul]
  exact reconstruct_inverse _ (mul_ne_zero ha hh)

theorem transported_inverse_reverse (a h : F) (ha : a ≠ 0) (hh : h ≠ 0) :
    (a/h)^64*(invNorm64 a*norm64 h) = (a/h)⁻¹ := by
  rw [← invnorm_div]
  exact reconstruct_inverse _ (div_ne_zero ha hh)

theorem norm8_mul (a h : F) : norm8 (a*h) = norm8 a*norm8 h := by
  simp [norm8,mul_pow]

theorem tower_norm_comp (a : F) : norm8 (norm64 a) = a^585 := by
  simp [norm8,norm64,← pow_mul]

/-- Nonzero scale roundtrip for the physical normalized pivot. -/
theorem restore_pivot (a h : F) (hh : h ≠ 0) : (a/h)*h = a := by
  field_simp

theorem scale_inverse_with_cache (x a : F) (ha : a ≠ 0) :
    (x*a⁻¹)*a = x ∧ (x*a)*a⁻¹ = x := by
  constructor
  · rw [mul_assoc,inv_mul_cancel₀ ha,mul_one]
  · rw [mul_assoc,mul_inv_cancel₀ ha,mul_one]

/-- Factor the inverse-norm carry and its repayment, not the full word
    reciprocal. Valid for arbitrary nonzero h. -/
theorem carry_roundtrip (c n : F) (hn : n ≠ 0) :
    (c*n⁻¹)*n=c ∧ (c*n)*n⁻¹=c :=
  scale_inverse_with_cache c n hn

theorem cache_two_rhs (x y a : F) (ha : a ≠ 0) :
    ((x/a)*a,(y/a)*a)=(x,y) := by
  apply Prod.ext <;> field_simp

end Field

section Ring
variable {R : Type*} [CommRing R]

/-- Polynomial coordinate expression for the quadratic tower norm. -/
theorem tower_product (u v t k : R) (h2 : (2:R)=0)
    (hk : t^2+t=k) :
    (u+t*v)*(u+(t+1)*v) = u^2+u*v+k*v^2 := by
  calc
    _ = u^2+u*v+(t^2+t)*v^2+2*t*u*v := by ring
    _ = _ := by rw [hk,h2,zero_mul,zero_mul,zero_mul,add_zero]

/-- Squared denominators are still accounted for under the same norm. -/
theorem square_norm (a : R) : (a^2)^65=(a^65)^2 := by
  rw [← pow_mul,← pow_mul]

end Ring

theorem phase_transport (x restored m : Bool) (h : restored=x) :
    Bool.xor (m && x) (m && restored)=false := by
  subst restored
  cases m <;> cases x <;> decide

theorem phase_transport_pair (x y x' y' m n : Bool) (hx : x'=x) (hy : y'=y) :
    Bool.xor (Bool.xor (m && x) (n && y))
      (Bool.xor (m && x') (n && y'))=false := by
  subst x'
  subst y'
  cases x <;> cases y <;> cases m <;> cases n <;> decide

theorem wide_budget : 71*12+45=897 ∧ 897+1=898 := by decide
theorem compact_budget : 71*12+33=885 ∧ 885+1=886 := by decide
theorem wide_cost : 3*84-(66+0+66+15+6+30+24)=45 ∧ 17*45=765 := by decide
theorem compact_cost : 3*84-(66+66+15+12+15+6+30+24)=18 ∧ 17*18=306 := by decide

#print axioms norm64_mul
#print axioms norm64_div
#print axioms norm64_fixed
#print axioms norm64_ne_zero
#print axioms norm64_inverse
#print axioms invnorm_mul
#print axioms invnorm_div
#print axioms invnorm_repay
#print axioms invnorm_repay_reverse
#print axioms reconstruct_inverse
#print axioms transported_inverse
#print axioms transported_inverse_reverse
#print axioms norm8_mul
#print axioms tower_norm_comp
#print axioms restore_pivot
#print axioms scale_inverse_with_cache
#print axioms carry_roundtrip
#print axioms cache_two_rhs
#print axioms tower_product
#print axioms square_norm
#print axioms phase_transport
#print axioms phase_transport_pair
#print axioms wide_budget
#print axioms compact_budget
#print axioms wide_cost
#print axioms compact_cost
end GVQCC.CrossStageNorm
