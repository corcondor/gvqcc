import Mathlib
namespace GVQCC.CentralSchur
variable {R : Type*} [CommRing R]
/-- Persistent masked evaluation form; update only the coefficient difference. -/
theorem delta_scalar (a b c x : R) (h : (2:R)=0) :
    c*(a*x)+(b+c*a)*x=b*x := by
  calc
    _ = b*x+2*(c*a*x) := by ring
    _ = _ := by rw [h, zero_mul, add_zero]

theorem delta_shared (a b c d l x y : R) (h : (2:R)=0) :
    l*(a*x+b*y)+((c+l*a)*x+(d+l*b)*y)=c*x+d*y := by
  calc
    _ = c*x+d*y+2*(l*a*x+l*b*y) := by ring
    _ = _ := by rw [h, zero_mul, add_zero]

/-- Laurent contraction carries a common scalar across both RHS. -/
theorem shared_bilinear (q a b c d : R) :
    q*(a+b)+(c+d)=q*a+c+(q*b+d) := by ring

/-- No cyclic wrap into the requested output window [r-1,k-1]. -/
theorem middle_no_wrap (k r m a b : Nat) (ha : a < k) (hb : b < r)
    (hm : k ≤ m) (hw : m ≤ a+b) : a+b-m < r-1 := by omega

/-- The adjoint repayment is computed from the final masked form. -/
theorem phase_cancel (x m : Bool) :
    Bool.xor (x && m) (x && m) = false := by cases x <;> cases m <;> decide

theorem fixed_workspace : 865+16+1+18=900 := by decide
#print axioms delta_scalar
#print axioms delta_shared
#print axioms shared_bilinear
#print axioms middle_no_wrap
#print axioms phase_cancel
#print axioms fixed_workspace
end GVQCC.CentralSchur
