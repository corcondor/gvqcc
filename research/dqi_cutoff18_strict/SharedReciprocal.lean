import Mathlib

namespace GVQCC.SharedReciprocal

section Field
variable {F : Type*} [Field F]

/-- Retain the retired scalar alpha=a/h through the child solve. -/
theorem retired_pivot (a h p : F) (ha : a ≠ 0) (hh : h ≠ 0) :
    (p/h)/(a/h) = p/a := by
  field_simp [ha, hh] <;> ring

theorem retired_restore (a h : F) (hh : h ≠ 0) :
    (a/h)*h = a := by
  field_simp [hh]

theorem pair_cancel (p d : F) (hd : d ≠ 0) :
    (p/d)*d = p := by
  field_simp [hd]

/-- Linear interpolation frame commutes with a scalar transvection. -/
theorem interpolation_transport {V : Type*} [AddCommGroup V] [Module F V]
    (L : V →ₗ[F] V) (a b : V) (r : F) :
    L (a + r • b) = L a + r • L b := by
  simp

/-- The retired interpolation coordinate can be restored without a clean word. -/
theorem interpolation_restore (a c b : F) (hc : c ≠ 0) :
    ((c*a+b)-b)/c = a := by
  rw [add_sub_cancel_right]
  field_simp [hc]

/-- Nonmonic triangular Bezout application keeps the leading factor. -/
theorem nonmonic_step (b y z : F) (hb : b ≠ 0) :
    b*(y+z/b) = b*y+z := by
  field_simp [hb] <;> ring

theorem shared_inverse (s r p : F) (h : s*r = 1) :
    (p*s)*r = p := by
  rw [mul_assoc, h, mul_one]

end Field

section Ring
variable {R : Type*} [CommRing R]

/-- Quadratic extension norm: conjugate beta -> beta+1. -/
theorem tower_norm (a b beta k : R) (h2 : (2 : R) = 0)
    (hb : beta^2+beta = k) :
    (a+b*beta)*(a+b*(beta+1)) = a^2+a*b+k*b^2 := by
  calc
    _ = a^2+a*b+(beta^2+beta)*b^2+2*(a*b*beta) := by ring
    _ = _ := by rw [hb, h2, zero_mul, add_zero]

theorem phase_repay (x m : R) (h2 : (2 : R) = 0) :
    m*x+m*x = 0 := by
  calc
    _ = 2*(m*x) := by ring
    _ = _ := by rw [h2, zero_mul]

end Ring

theorem cache_cost : 85*102+170*42 = 15810 := by decide
theorem compact_seam : 852+13+31 = 896 := by decide
theorem shared_scale_count : 17*14-17*4 = 170 := by decide

#print axioms retired_pivot
#print axioms retired_restore
#print axioms pair_cancel
#print axioms interpolation_transport
#print axioms interpolation_restore
#print axioms nonmonic_step
#print axioms shared_inverse
#print axioms tower_norm
#print axioms phase_repay
#print axioms cache_cost
#print axioms compact_seam
#print axioms shared_scale_count
end GVQCC.SharedReciprocal
