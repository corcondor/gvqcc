import Mathlib
namespace GVQCC.SharedResidualFFT
variable {F : Type*} [Field F]
theorem shared_residual (rho m x p : F) : rho*m + rho*x*p = rho*(m+x*p) := by ring
theorem shared_coefficient (rho x a l m : F) (ha : a ≠ 0) :
    (rho*x*l/a)*m = rho*x*(l*(m/a)) := by
  field_simp [ha] <;> ring
theorem shear_restore {R : Type*} [CommRing R] (a b c : R) (h : (2:R)=0) :
    (a+c*b)+c*b=a := by
  calc
    _ = a+2*(c*b) := by ring
    _ = _ := by rw [h,zero_mul,add_zero]
theorem affine_split {R : Type*} [CommRing R] (a b c : R) :
    a+(c+1)*b=(a+c*b)+b := by ring
theorem exact_counts : 4024*72=289728 ∧ 4024*72*12=3476736 ∧
    4909739-2924655=1985084 := by decide
#print axioms shared_residual
#print axioms shared_coefficient
#print axioms shear_restore
#print axioms affine_split
#print axioms exact_counts
end GVQCC.SharedResidualFFT
