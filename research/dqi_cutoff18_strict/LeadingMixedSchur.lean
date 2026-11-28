import Mathlib

namespace GVQCC.LeadingMixedSchur
open Polynomial

section Leading
variable {F : Type*} [Field F]

/-- The highest coefficient of the second source shear is unchanged. -/
theorem leading_shear (A B : F[X]) (q : F) (n : ℕ)
    (hB : B.coeff (n+1) = 0) :
    (A + C q * B).coeff (n+1) = A.coeff (n+1) := by
  simp [coeff_add, coeff_C_mul, hB]

/-- Monic synthetic division transports the leading coefficient exactly. -/
theorem leading_division (A B Q : F[X]) (q t : F) (n : ℕ)
    (hB : B.coeff (n+1) = 0) (hQ : Q.coeff (n+1) = 0)
    (h : A + C q * B = (X + C t)*Q) :
    A.coeff (n+1) = Q.coeff n := by
  have he := congrArg (fun p : F[X] => p.coeff (n+1)) h
  simpa [coeff_add, coeff_C_mul, add_mul, coeff_X_mul, hB, hQ] using he

/-- Interpolation-only leading coordinate can be borrowed without losing it. -/
theorem leading_loan_restore (a b c : F) (hc : c ≠ 0) :
    (c*a+b-b)/c = a := by
  rw [add_sub_cancel_right]
  field_simp [hc]

/-- The nonzero interpolation factor is a product of distinct-node differences. -/
theorem node_product_ne_zero (xs : List F) (t : F)
    (h : ∀ x ∈ xs, t+x ≠ 0) : (xs.map (fun x => t+x)).prod ≠ 0 := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    simp only [List.map_cons, List.prod_cons]
    exact mul_ne_zero (h x (by simp)) (ih (fun y hy => h y (by simp [hy])))

end Leading

section Ring
variable {R : Type*} [CommRing R]

/-- Distinct-row/column Schur displacement numerator. Coincident pivots are
    also admitted; no derivative is required in the polynomial identity. -/
theorem mixed_displacement (x y t s u v w z q r : R) (h2 : (2 : R) = 0) :
    ((x+s)*u+q*v)*(r*((y+s)*w+q*z)+(y+t)*z) +
      (r*((x+s)*u+q*v)+(x+t)*v)*((y+s)*w+q*z) =
    (x+t)*(y+s)*(u*z+v*w)+(x+y)*((s+t)*u+q*v)*z := by
  calc
    _ = (x+t)*(y+s)*(u*z+v*w)+(x+y)*((s+t)*u+q*v)*z +
        2*(r*((x+s)*u+q*v)*((y+s)*w+q*z)+t*q*v*z-(x*s+t*y)*u*z) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

/-- Unit restoration by adding the same mixed transvection in characteristic 2. -/
theorem mixed_restore (a b q d : R) (h2 : (2 : R) = 0) :
    (d*a+q*b)+q*b=d*a := by
  calc
    _ = d*a+2*(q*b) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

/-- Rank-one product of pivot column and row, with common factors retained. -/
theorem rank_one_factor (a h f g : R) : (h*f)*(a*g)=(a*h)*(f*g) := by ring

end Ring

section Field
variable {F : Type*} [Field F]

theorem nonzero_pivot (a h : F) (ha : a ≠ 0) (hh : h ≠ 0) : a*h ≠ 0 :=
  mul_ne_zero ha hh

theorem normalized_rank_one (a h f g : F) (ha : a ≠ 0) (hh : h ≠ 0) :
    (h*f)*(a*g)/(a*h)=f*g := by
  rw [rank_one_factor]
  field_simp [ha, hh]

end Field

theorem coefficient_count : 2*17=34 ∧ 34*42=1428 ∧ 2*1428=2856 := by decide
theorem leading_storage : (2*(17+1)+2*17)*12+30=870 := by decide
theorem orientation_cardinality : 4096^2-1 > 4096*4095 := by decide

#print axioms leading_shear
#print axioms leading_division
#print axioms leading_loan_restore
#print axioms node_product_ne_zero
#print axioms mixed_displacement
#print axioms mixed_restore
#print axioms rank_one_factor
#print axioms nonzero_pivot
#print axioms normalized_rank_one
#print axioms coefficient_count
#print axioms leading_storage
#print axioms orientation_cardinality
end GVQCC.LeadingMixedSchur
