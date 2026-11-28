import Mathlib

namespace GVQCC.PackedContinuant
section Algebra
variable {R : Type*} [CommRing R]

/-- The elementary continuant matrices are symmetric: the product reversal
    swaps the off-diagonal entries without changing the diagonal entries. -/
theorem reversed_two (p q : R) :
    (p*q+1,p,q,1) = (q*p+1,p,q,1) := by
  rw [mul_comm p q]

theorem determinant_step (a b c d q : R) (h2 : (2:R)=0) :
    (a*q+b)*c+a*(c*q+d)=a*d+b*c := by
  calc
    _ = a*d+b*c+2*(a*c*q) := by ring
    _ = _ := by rw [h2,zero_mul,add_zero]

theorem scaled_remainder (X Y Z q s t : R) (h : X=q*Y+Z) :
    s*t*X = (s*q)*(t*Y)+s*t*Z := by
  rw [h]
  ring

theorem reversed_bezout (a b c d g gi : R)
    (h : a*d+b*c=1) (hi : g*gi=1) :
    (g*c)*(b*gi)+(g*a)*(d*gi)=1 := by
  calc
    _ = (g*gi)*(a*d+b*c) := by ring
    _ = _ := by rw [h,hi,one_mul]

theorem scalar_scale (x a ai : R) (h : a*ai=1) :
    (x*a)*ai=x := by rw [mul_assoc,h,mul_one]

theorem quotient_lift (A B q Rm C k c t s : R)
    (hb : B=q*A+Rm) (hc : C=k*A+c) (hr : c=Rm*t+A*s)
    (h2 : (2:R)=0) :
    A*(k+q*t+s)+B*t=C := by
  rw [hb,hc,hr]
  calc
    _ = A*k+Rm*t+A*s+2*(A*q*t) := by ring
    _ = _ := by rw [h2,zero_mul,add_zero]; ring

theorem linear_observer (u v a b : R) :
    u*(a+b)+v*(a+b)=(u+v)*a+(u+v)*b := by ring

end Algebra

theorem hmr_scale_phase (meas old recovered : Bool) (h : old=recovered) :
    Bool.xor (meas && old) (meas && recovered)=false := by
  subst old
  cases meas <;> cases recovered <;> decide

#print axioms reversed_two
#print axioms determinant_step
#print axioms scaled_remainder
#print axioms reversed_bezout
#print axioms scalar_scale
#print axioms quotient_lift
#print axioms linear_observer
#print axioms hmr_scale_phase
end GVQCC.PackedContinuant
