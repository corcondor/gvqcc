import Mathlib
namespace GVQCC.BlockedResidue
open scoped BigOperators
section
variable {R : Type*} [CommRing R]
theorem split_accumulation {I : Type*} [DecidableEq I]
    (f : I → R) (s t : Finset I) (h : Disjoint s t) :
    (∑ i ∈ s ∪ t, f i) = (∑ i ∈ s, f i) + ∑ i ∈ t, f i :=
  Finset.sum_union h

theorem affine_shear_undo (x y a : R) (h : (2:R)=0) :
    (x + a*y) + a*y = x := by
  calc
    _ = x + 2*(a*y) := by ring
    _ = _ := by rw [h,zero_mul,add_zero]

theorem normalization_distributes (s a b : R) :
    s*(a+b)=s*a+s*b := by ring

theorem scaled_pivot (s r x a y : R) (h : s*r=1) :
    (r*x)*s=x ∧ y+a*(r*x)=y+(a*r)*x := by
  constructor
  · calc
      (r*x)*s=(s*r)*x := by ring
      _=x := by rw [h,one_mul]
  · ring

theorem two_rhs_rectangle (a b c d u v : R) :
    ((a*u+b*v),(c*u+d*v)) =
      (u*a+v*b,u*c+v*d) := by
  apply Prod.ext
  · change a*u+b*v = u*a+v*b
    ring
  · change c*u+d*v = u*c+v*d
    ring

theorem residue_lift (a b q r k c s t rho p : R)
    (h2 : (2:R)=0) (hb : b=a*q+r) (hp : p=a*k+c)
    (hc : c=rho+r*t+a*s) :
    p=rho+a*(k+q*t+s)+b*t := by
  rw [hp,hc,hb]
  calc
    _ = rho+a*(k+q*t+s)+(a*q+r)*t-2*(a*q*t) := by ring
    _ = _ := by rw [h2,zero_mul,sub_zero]
end

theorem measured_repayment (m x y z : Bool) (h : Bool.xor x y = z) :
    Bool.xor (Bool.xor (m && x) (m && y)) (m && z) = false := by
  cases m <;> cases x <;> cases y <;> cases z <;> simp_all

#print axioms split_accumulation
#print axioms affine_shear_undo
#print axioms normalization_distributes
#print axioms scaled_pivot
#print axioms two_rhs_rectangle
#print axioms residue_lift
#print axioms measured_repayment
end GVQCC.BlockedResidue
