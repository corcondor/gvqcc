import Mathlib

namespace GVQCC.GhostReturn
variable {K : Type*} [CommRing K]

theorem companion (l k t x y : K)
    (ht : t*(t+l)=k) (h2 : ∀ a : K, a+a=0) :
    (k*x+l*y)+(t+l)*y = t*(y+(t+l)*x) := by
  calc
    _ = k*x+t*y+(l*y+l*y) := by ring
    _ = k*x+t*y := by rw [h2, add_zero]
    _ = (t*(t+l))*x+t*y := by rw [ht]
    _ = _ := by ring

theorem cramer_first (c d l k x y : K) (h2 : ∀ a : K, a+a=0) :
    (c+d*l)*(c*x+d*y)+d*(d*k*x+(c+d*l)*y) =
    (c*(c+d*l)+d*d*k)*x := by
  calc
    _ = (c*(c+d*l)+d*d*k)*x + ((c+d*l)*d*y+(c+d*l)*d*y) := by ring
    _ = _ := by rw [h2, add_zero]

theorem cramer_second (c d l k x y : K) (h2 : ∀ a : K, a+a=0) :
    d*k*(c*x+d*y)+c*(d*k*x+(c+d*l)*y) =
    (c*(c+d*l)+d*d*k)*y := by
  calc
    _ = (c*(c+d*l)+d*d*k)*y + (d*k*c*x+d*k*c*x) := by ring
    _ = _ := by rw [h2, add_zero]

theorem conjugate_norm (a b t k : K) (ht : t*(t+1)=k)
    (h2 : ∀ z : K, z+z=0) :
    (a+b*t)*(a+b+b*t) = a*a+a*b+k*b*b := by
  calc
    _ = a*a+a*b+(b*b)*(t*(t+1))+(a*b*t+a*b*t) := by ring
    _ = a*a+a*b+b*b*k := by rw [ht,h2,add_zero]
    _ = _ := by ring

theorem trace_conjugate (a b t : K) (h2 : ∀ z : K, z+z=0) :
    (a+b*t)+(a+b*(t+1))=b := by
  calc
    _ = b+(a+a)+(b*t+b*t) := by ring
    _ = _ := by simp only [h2, add_zero]

theorem hmr_and_repay (m a b : Bool) :
    ((m && (a && b)) ^^ ((m && a) && b)) = false := by
  cases m <;> cases a <;> cases b <;> rfl

theorem simple_factor_guard (a b : Bool) :
    (a ^^ (a && b)) = (a && !b) := by
  cases a <;> cases b <;> rfl

theorem grouped_guard (a b c : Bool) :
    (a && !(b&&c)) = (a ^^ (a&&b&&c)) := by
  cases a <;> cases b <;> cases c <;> rfl

theorem dirty_target_involution (t x a b : Bool) :
    ((t ^^ ((a && !b)&&x)) ^^ ((a && !b)&&x)) = t := by
  cases t <;> cases x <;> cases a <;> cases b <;> rfl

#print axioms companion
#print axioms cramer_first
#print axioms cramer_second
#print axioms conjugate_norm
#print axioms trace_conjugate
#print axioms hmr_and_repay
#print axioms simple_factor_guard
#print axioms grouped_guard
#print axioms dirty_target_involution
end GVQCC.GhostReturn
