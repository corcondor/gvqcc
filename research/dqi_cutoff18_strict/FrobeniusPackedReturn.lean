import Mathlib

namespace GVQCC.FrobeniusPackedReturn
section Algebra
variable {R : Type*} [CommRing R]

theorem square_add (a b : R) (h2 : (2:R)=0) :
    (a+b)^2=a^2+b^2 := by
  calc
    _ = a^2+b^2+2*(a*b) := by ring
    _ = _ := by rw [h2,zero_mul,add_zero]

/-- Bezout at half the degree; no full-degree derivative inverse is needed. -/
theorem half_bezout (A B u v h X : R) (h2 : (2:R)=0)
    (hh : u*A+v*B=h) :
    B^2*(X*u^2+v^2)+u^2*(A^2+X*B^2)=h^2 := by
  calc
    _ = (u*A+v*B)^2+2*(X*u^2*B^2-u*v*A*B) := by ring
    _ = _ := by rw [hh,h2,zero_mul,add_zero]

theorem derivative_inverse_at_root (A B u v h X : R) (h2 : (2:R)=0)
    (hh : u*A+v*B=h) (hp : A^2+X*B^2=0) :
    B^2*(X*u^2+v^2)=h^2 := by
  have z := half_bezout A B u v h X h2 hh
  rw [hp,mul_zero,add_zero] at z
  exact z

/-- Splitting N=P'V+PT into the two Frobenius parity components. -/
theorem two_rhs_split (A B C D E F G H X : R) (h2 : (2:R)=0)
    (hc : C = B*E+A*G+X*B*H)
    (hd : D = B*F+A*H+B*G) :
    C^2+X*D^2=B^2*(E^2+X*F^2)+(A^2+X*B^2)*(G^2+X*H^2) := by
  rw [hc,hd]
  simp only [square_add _ _ h2]
  ring

/-- Exact division gives the two lower-degree return equations. -/
theorem return_equations (A B C D q r G H X : R) (h2 : (2:R)=0)
    (hc : C+A*G=B*q) (hd : D+A*H=B*r) :
    C=B*(q+X*H)+A*G+X*B*H ∧
    D=B*(r+G)+A*H+B*G := by
  constructor
  · calc
      C = B*q-A*G := by rw [← hc]; ring
      _ = B*(q+X*H)+A*G+X*B*H-2*(A*G+X*B*H) := by ring
      _ = _ := by rw [h2,zero_mul,sub_zero]
  · calc
      D = B*r-A*H := by rw [← hd]; ring
      _ = B*(r+G)+A*H+B*G-2*(A*H+B*G) := by ring
      _ = _ := by rw [h2,zero_mul,sub_zero]

theorem ghost_repaid (B t H n : R) (h : B^2*t=H^2) :
    B^2*(n*t)=H^2*n := by
  calc
    _ = (B^2*t)*n := by ring
    _ = _ := by rw [h]

/-- The order of two triangular shears preserves the higher control words. -/
theorem return_shear (g h a b : R) (h2 : (2:R)=0) :
    (g+a*h+a*h,h+b+b)=(g,h) := by
  have hg : a*h+a*h=0 := by
    calc
      _ = 2*(a*h) := by ring
      _ = _ := by rw [h2,zero_mul]
  have hb : b+b=0 := by
    calc
      _ = 2*b := by ring
      _ = _ := by rw [h2,zero_mul]
  rw [add_assoc g, hg, add_zero, add_assoc h,hb,add_zero]

end Algebra

open scoped BigOperators
theorem transpose_hankel {R I J K : Type*} [CommRing R]
    [Fintype I] [Fintype J] [Fintype K]
    (a : I → K → R) (b : J → K → R) (t : K → R) (x : J → R)
    (i : I) :
    (∑ j, (∑ k, a i k * b j k * t k)*x j) =
      ∑ k, a i k * t k * (∑ j, b j k*x j) := by
  simp only [Finset.sum_mul, Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro k _
  apply Finset.sum_congr rfl
  intro j _
  ring

#print axioms square_add
#print axioms half_bezout
#print axioms derivative_inverse_at_root
#print axioms two_rhs_split
#print axioms return_equations
#print axioms ghost_repaid
#print axioms return_shear
#print axioms transpose_hankel
end GVQCC.FrobeniusPackedReturn
