import Mathlib

namespace GVQCC.MultiscaleDual

section Ring
variable {R : Type*} [CommRing R]

theorem fixed_leading (a b kap l m l' m' : R)
    (hk : a*kap=b) (h : l'+kap*m'=l+kap*m) :
    a*l'+b*m'=a*l+b*m := by
  rw [← hk]
  calc
    _ = a*(l'+kap*m') := by ring
    _ = a*(l+kap*m) := by rw [h]
    _ = _ := by ring

theorem gauge_line (r c kap nu mu : R) :
    r+(nu+kap*mu)+c*mu=r+nu+(c+kap)*mu := by ring

theorem zero_score (r nu c kap mu : R) (h2 : (2:R)=0) :
    r+nu+(c+kap)*mu=0 ↔ (c+kap)*mu=r+nu := by
  constructor
  · intro h
    linear_combination h - (r+nu)*h2
  · intro h
    rw [h]
    calc
      _ = 2*(r+nu) := by ring
      _ = 0 := by rw [h2, zero_mul]

theorem quotient_defect (x u v f p q rem : R) (h : f=p*q+rem) :
    x*(u+v*x)*f = x*(u+v*x)*rem + x*(u+v*x)*p*q := by
  rw [h]; ring

theorem quotient_at_root (x u v f p q rem : R) (h : f=p*q+rem)
    (hp : p=0) : x*(u+v*x)*f=x*(u+v*x)*rem := by
  rw [h,hp,zero_mul,zero_add]

theorem parity_factor (a b h x : R) :
    (h*a)^2+x*(h*b)^2=h^2*(a^2+x*b^2) := by ring

open scoped BigOperators
theorem dual_contract {I : Type*} [Fintype I]
    (p s : I → R) (c : R) :
    c*(∑ i, p i*s i)=∑ i,c*p i*s i := by
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro i _
  ring
end Ring

theorem multiplicity_split (n : Nat) : n=2*(n/2)+n%2 := by omega

#print axioms fixed_leading
#print axioms gauge_line
#print axioms zero_score
#print axioms quotient_defect
#print axioms quotient_at_root
#print axioms parity_factor
#print axioms dual_contract
#print axioms multiplicity_split
end GVQCC.MultiscaleDual
