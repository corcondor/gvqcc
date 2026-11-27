import Mathlib

namespace GVQCC.HalfBezoutMagnitude

variable {R : Type*} [CommRing R]

theorem square_add_char2 (h2 : (2 : R) = 0) (a b : R) :
    (a + b)^2 = a^2 + b^2 := by
  calc
    (a+b)^2 = a^2+b^2+2*a*b := by ring
    _ = a^2+b^2 := by rw [h2]; ring

theorem half_identity (h2 : (2 : R) = 0) (a b x p0 p1 u t z w : R)
    (hz : b*z = p0+a*u) (hw : b*w = p1+a*t) :
    b^2*((z+x*t)^2+x*(w+u)^2) =
      p0^2+x*p1^2+(a^2+x*b^2)*(u^2+x*t^2) := by
  have hv0 : b*(z+x*t) = p0+a*u+x*b*t := by
    calc
      _ = b*z+x*b*t := by ring
      _ = _ := by rw [hz]
  have hv1 : b*(w+u) = p1+a*t+b*u := by
    calc
      _ = b*w+b*u := by ring
      _ = _ := by rw [hw]
  calc
    _ = (b*(z+x*t))^2+x*(b*(w+u))^2 := by ring
    _ = (p0+a*u+x*b*t)^2+x*(p1+a*t+b*u)^2 := by rw [hv0,hv1]
    _ = _ := by simp only [square_add_char2 h2, mul_pow]; ring

theorem quotient_frame (h2 : (2 : R) = 0) (q : R →+ R) (c x u t : R) :
    c+x*t+q (q t)+q (u+q t) = c+q u+x*t := by
  have h : q (q t)+q (q t) = 0 := by
    calc
      _ = 2*q (q t) := by ring
      _ = 0 := by rw [h2, zero_mul]
  rw [map_add]
  calc
    _ = c+q u+x*t+(q (q t)+q (q t)) := by ring
    _ = _ := by rw [h,add_zero]

theorem root_identity {F : Type*} [Field F] (h2 : (2 : F) = 0)
    (a b x p0 p1 u t z w e : F)
    (hz : b*z = p0+a*u) (hw : b*w = p1+a*t)
    (hr : a^2+x*b^2 = 0) (hp : p0^2+x*p1^2 = (x*e)*b^2)
    (hb : b ≠ 0) :
    (z+x*t)^2+x*(w+u)^2 = x*e := by
  have h := half_identity h2 a b x p0 p1 u t z w hz hw
  rw [hr, zero_mul, add_zero, hp] at h
  apply mul_left_cancel₀ (pow_ne_zero 2 hb)
  calc
    b^2*((z+x*t)^2+x*(w+u)^2) = (x*e)*b^2 := h
    _ = b^2*(x*e) := by ring

#print axioms square_add_char2
#print axioms half_identity
#print axioms quotient_frame
#print axioms root_identity
end GVQCC.HalfBezoutMagnitude
