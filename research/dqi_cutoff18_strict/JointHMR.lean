import Mathlib
namespace GVQCC.JointHMR
section Ring
variable {R : Type*} [CommRing R]

/-- Controlled exchange of a whole field word; one selected factor repays every word. -/
theorem selected_factor (f y p q : R) :
    y * ((1-f)*p + f*q) = (1-f)*(y*p) + f*(y*q) := by ring

theorem selected_factor_inverse_active (y p q : R) (h : p*q=1) :
    (y*p)*q=y := by rw [mul_assoc,h,mul_one]

theorem batch_product_linearity (a b p q : R) :
    (a+b)*(p+q)=a*p+a*q+b*p+b*q := by ring

theorem elementary_inverse_step (a x : R) (h : (2:R)=0) :
    (1+a*x)*(1+a*x)=1+a^2*x^2 := by
  calc
    (1+a*x)*(1+a*x) = 1+2*(a*x)+a^2*x^2 := by ring
    _ = _ := by rw [h,zero_mul,add_zero]

/-- Characteristic-two truncated geometric factorization. -/
theorem factor_double (z : R) (h : (2:R)=0) :
    (1+z)*(1+z)=1+z^2 := by
  calc
    (1+z)*(1+z)=1+2*z+z^2 := by ring
    _ = _ := by rw [h,zero_mul,add_zero]
end Ring
end GVQCC.JointHMR

#print axioms GVQCC.JointHMR.selected_factor
#print axioms GVQCC.JointHMR.selected_factor_inverse_active
#print axioms GVQCC.JointHMR.batch_product_linearity
#print axioms GVQCC.JointHMR.elementary_inverse_step
#print axioms GVQCC.JointHMR.factor_double
