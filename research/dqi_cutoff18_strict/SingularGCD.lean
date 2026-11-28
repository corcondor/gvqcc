import Mathlib

namespace GVQCC.SingularGCD
section
variable {R : Type*} [CommRing R]

theorem residue_lift (a b q r k c s t rho p : R)
    (h2 : (2:R)=0) (hb : b=a*q+r) (hp : p=a*k+c)
    (hc : c=rho+r*t+a*s) :
    p=rho+a*(k+q*t+s)+b*t := by
  rw [hp,hc,hb]
  calc
    _ = rho+a*(k+q*t+s)+(a*q+r)*t-2*(a*q*t) := by ring
    _ = _ := by rw [h2,zero_mul,sub_zero]

theorem gcd_quotient_lift (a b h u v k p rho : R)
    (hp : p=h*k+rho) (hk : k=a*u+b*v) :
    p=h*a*u+h*b*v+rho := by rw [hp,hk]; ring

theorem common_square_factor (a b h x : R) :
    (h*a)^2+x*(h*b)^2=h^2*(a^2+x*b^2) := by ring

theorem dirty_tail (d y n v t z : R)
    (hz : d*z=n+v) (ht : t=d*y+n+v) :
    t=d*(y+z) := by rw [mul_add,hz,ht]; ring

theorem parity_numerator (d a t z : R) (h : d*t=a) :
    d*(1+z*t)=d+z*a := by
  calc
    _ = d+z*(d*t) := by ring
    _ = _ := by rw [h]

theorem phase_repayment (m a b rho : Bool)
    (h : Bool.xor a b = rho) :
    Bool.xor (Bool.xor (m && a) (m && b)) (m && rho) = false := by
  cases m <;> cases a <;> cases b <;> cases rho <;> simp_all

end
theorem radical_root_union {F : Type*} [Field F] (h q : F) :
    h^2*q=0 ↔ h=0 ∨ q=0 := by
  simp [pow_two,mul_eq_zero]

theorem chart_budget (a b : Nat) (ha : a<b) (hb : b≤17) :
    12*(a+b+2+2*b+5)≤900 := by omega

#print axioms residue_lift
#print axioms gcd_quotient_lift
#print axioms common_square_factor
#print axioms dirty_tail
#print axioms parity_numerator
#print axioms phase_repayment
#print axioms radical_root_union
#print axioms chart_budget
end GVQCC.SingularGCD
