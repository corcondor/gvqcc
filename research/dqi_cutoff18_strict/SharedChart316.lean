import Mathlib

namespace GVQCC.SharedChart316

/-- The difference of two quadratic evaluations is affine in the base point. -/
theorem quadratic_delta {F : Type*} [Field F] (a b c d p q r s t z : F) :
    ((a+t*p)*(b+t*q)+(c+t*r)*(d+t*s)) -
    ((a+z*p)*(b+z*q)+(c+z*r)*(d+z*s)) =
    (t-z)*(a*q+p*b+c*s+r*d)+(t^2-z^2)*(p*q+r*s) := by ring

/-- Characteristic two makes the affine update its own inverse. -/
theorem delta_involution {F : Type*} [Field F] [CharP F 2] (x d : F) :
    x+d+d=x := by
  have ht : (2:F)=0 := CharP.cast_eq_zero F 2
  calc
    x+d+d=x+2*d := by ring
    _=x := by rw [ht,zero_mul,add_zero]

/-- First component of conjugate(u)*v + b*u, in the quadratic basis. -/
theorem split_real {F : Type*} [Field F] (a b c d k : F) :
    (a+b)*c+k*b*d+b*a=(a+b)*c+b*(k*d+a) := by ring

theorem split_imag {F : Type*} [Field F] [CharP F 2] (a b c d : F) :
    (a+b)*d+b*c+b*d+b^2=a*d+b*c+b^2 := by
  have ht : (2:F)=0 := CharP.cast_eq_zero F 2
  calc
    _ = a*d+b*c+b^2+2*(b*d) := by ring
    _ = _ := by rw [ht,zero_mul,add_zero]

/-- Difference transport through an AND ladder with arbitrary dirty loan bits. -/
def carry : List (Bool × Bool) → Bool → Bool
  | [], x => x
  | (c,d)::rest, x => carry rest (Bool.xor d (x && c))

def gain : List (Bool × Bool) → Bool
  | [] => true
  | (c,_)::rest => c && gain rest

theorem carry_diff (xs : List (Bool × Bool)) (a b : Bool) :
    Bool.xor (carry xs a) (carry xs b) = (Bool.xor a b && gain xs) := by
  induction xs generalizing a b with
  | nil => cases a <;> cases b <;> rfl
  | cons p ps ih =>
    obtain ⟨c,d⟩ := p
    simp only [carry,gain]
    rw [ih]
    cases a <;> cases b <;> cases c <;> cases d <;> rfl

/-- The two passes of the dirty ladder cancel the unknown initial loan bit. -/
theorem borrowed_and (xs : List (Bool × Bool)) (x y d last : Bool) :
    Bool.xor (carry xs (Bool.xor d (x && y)) && last)
      (carry xs d && last) = (x && y && gain xs && last) := by
  have h := carry_diff xs (Bool.xor d (x && y)) d
  cases ha : carry xs (Bool.xor d (x && y)) <;>
    cases hb : carry xs d <;>
    cases x <;> cases y <;> cases d <;> cases last <;>
    cases hg : gain xs <;> simp_all

/-- The third choice is implied by the previously proved quadratic-three
condition; two badness bits suffice for the binary output tag. -/
theorem two_tests (bad1 bad2 : Bool) :
    (Bool.xor (Bool.xor true bad1) (bad1 && bad2), bad1) =
      (if bad1 then (if bad2 then (true,true) else (false,true))
       else (true,false)) := by cases bad1 <;> cases bad2 <;> rfl

theorem zero_product_update (a b t : Bool) (h : (a && b) = false) :
    Bool.xor t (a && b)=t := by rw [h]; cases t <;> rfl

end GVQCC.SharedChart316
#print axioms GVQCC.SharedChart316.quadratic_delta
#print axioms GVQCC.SharedChart316.delta_involution
#print axioms GVQCC.SharedChart316.split_real
#print axioms GVQCC.SharedChart316.split_imag
#print axioms GVQCC.SharedChart316.carry_diff
#print axioms GVQCC.SharedChart316.borrowed_and
#print axioms GVQCC.SharedChart316.two_tests
#print axioms GVQCC.SharedChart316.zero_product_update
