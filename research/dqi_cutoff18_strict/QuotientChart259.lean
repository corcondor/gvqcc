import Mathlib

namespace GVQCC.QuotientChart259
variable {R : Type*} [CommRing R]

theorem square_add_char2 (h2 : (2 : R) = 0) (a b : R) :
    (a+b)^2 = a^2+b^2 := by
  calc
    _ = a^2+b^2+2*a*b := by ring
    _ = _ := by rw [h2]; ring

/-- #246 half-degree identity, extended to an arbitrary retained square factor.
    No coprimality assumption is required for this polynomial identity. -/
theorem retained_square_factor (h2 : (2 : R) = 0)
    (h a b x p q u t z w : R)
    (hz : b*z = p+a*u) (hw : b*w = q+a*t) :
    (h*b)^2*((z+x*t)^2+x*(w+u)^2) =
      (h*p)^2+x*(h*q)^2+((h*a)^2+x*(h*b)^2)*(u^2+x*t^2) := by
  have hz' : b*(z+x*t) = p+a*u+x*b*t := by
    calc
      _ = b*z+x*b*t := by ring
      _ = _ := by rw [hz]
  have hw' : b*(w+u) = q+a*t+b*u := by
    calc
      _ = b*w+b*u := by ring
      _ = _ := by rw [hw]
  calc
    _ = h^2*((b*(z+x*t))^2+x*(b*(w+u))^2) := by ring
    _ = h^2*((p+a*u+x*b*t)^2+x*(q+a*t+b*u)^2) := by rw [hz', hw']
    _ = _ := by simp only [square_add_char2 h2, mul_pow]; ring

/-- Two representatives yielding the same numerator modulo the reduced
    denominator differ only by that denominator, given a Bezout witness. -/
theorem residue_unique_mod (d dd u v a b k : R)
    (hbez : u*d+v*dd=1) (hrel : dd*(a-b)=d*k) :
    a-b=d*(u*(a-b)+v*k) := by
  calc
    _ = (u*d+v*dd)*(a-b) := by rw [hbez,one_mul]
    _ = u*d*(a-b)+v*(dd*(a-b)) := by ring
    _ = _ := by rw [hrel]; ring

/-- Retaining the original denominator and the canonical residue keeps
    the numerator recoverable, rather than erasing its common factor. -/
theorem recover_numerator (h dd V D k : R) :
    h^2*dd*V-D*k = (h^2*dd)*V-D*k := by ring

theorem physical_root_value {F : Type*} [Field F]
    (h dd x U n V : F)
    (hh : h ≠ 0) (hd : dd ≠ 0) (hx : x ≠ 0) (hU : U ≠ 0)
    (hn : n=dd*V) :
    (h^2*n)/(x*U*(h^2*dd)) = V/(x*U) := by
  rw [hn]
  apply (div_eq_div_iff (mul_ne_zero (mul_ne_zero hx hU)
    (mul_ne_zero (pow_ne_zero 2 hh) hd)) (mul_ne_zero hx hU)).2
  ring

theorem restore_phase (m x y : Bool) (h : x=y) :
    Bool.xor (m && x) (m && y)=false := by
  subst y
  cases m <;> cases x <;> decide

end GVQCC.QuotientChart259

#print axioms GVQCC.QuotientChart259.square_add_char2
#print axioms GVQCC.QuotientChart259.retained_square_factor
#print axioms GVQCC.QuotientChart259.residue_unique_mod
#print axioms GVQCC.QuotientChart259.recover_numerator
#print axioms GVQCC.QuotientChart259.physical_root_value
#print axioms GVQCC.QuotientChart259.restore_phase
