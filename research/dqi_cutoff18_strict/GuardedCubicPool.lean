import Mathlib

namespace GVQCC.GuardedCubicPool
open scoped BigOperators

/-- A phase table may share arbitrary Boolean basis functions across guards,
even when guards overlap. The residue includes the full lower-degree phase debt. -/
theorem pool_phase {I J : Type*} [Fintype I] [Fintype J]
    (g : I → ZMod 2) (A : I → J → ZMod 2)
    (c : J → ZMod 2) (r : I → ZMod 2) :
    (∑ i, g i*((∑ j,A i j*c j)+r i)) =
      (∑ j,(∑ i,g i*A i j)*c j)+(∑ i,g i*r i) := by
  simp only [mul_add,Finset.sum_add_distrib,Finset.mul_sum,Finset.sum_mul]
  congr 1
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  apply Finset.sum_congr rfl
  intro i _
  ring

theorem pool_refinement {I J : Type*} [Fintype I] [Fintype J]
    (g : I → ZMod 2) (A : I → J → ZMod 2)
    (c : J → ZMod 2) (r old : I → ZMod 2)
    (cert : ∀ i, old i = (∑ j,A i j*c j)+r i) :
    (∑ i,g i*old i) =
      (∑ j,(∑ i,g i*A i j)*c j)+(∑ i,g i*r i) := by
  simp_rw [cert]
  exact pool_phase g A c r

/-- Classical flags may be updated by XOR, not OR, so repeated
contributions and nonexclusive guards cancel correctly. -/
theorem guard_xor (a b p : ZMod 2) : (a+b)*p = a*p+b*p := by ring

theorem phase_debt (a b r : ZMod 2) (h : a = b+r) : a+b=r := by
  rw [h]
  calc
    _ = (2 : ZMod 2)*b+r := by ring
    _ = r := by rw [show (2 : ZMod 2) = 0 by decide, zero_mul, zero_add]

/-- Pull back a binary mask through a linear coordinate map. -/
theorem mask_transpose {I J : Type*} [Fintype I] [Fintype J]
    (M : I → J → ZMod 2) (m : I → ZMod 2) (e : J → ZMod 2) :
    (∑ i,m i*(∑ j,M i j*e j)) =
      ∑ j,(∑ i,m i*M i j)*e j := by
  simp only [Finset.mul_sum,Finset.sum_mul]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  apply Finset.sum_congr rfl
  intro i _
  ring

section Field
variable {F : Type*} [Field F]

/-- Reciprocal action on the 70-moment ABI. The exponent 71 is fixed
by the ABI, independently of samples, masks or verifier seeds. -/
theorem reciprocal_one (x e : F) (j : ℕ) (hx : x ≠ 0) (hj : j ≤ 71) :
    (x^71*e)*(x⁻¹)^j = e*x^(71-j) := by
  have h : j+(71-j)=71 := by omega
  have hp : x^j*x^(71-j)=x^71 := by rw [← pow_add,h]
  calc
    _ = (x^j*x^(71-j)*e)*(x⁻¹)^j := by rw [hp]
    _ = e*x^(71-j)*(x^j*(x⁻¹)^j) := by ring
    _ = _ := by rw [← mul_pow, mul_inv_cancel₀ hx, one_pow, mul_one]

theorem reciprocal_moments {I : Type*} [Fintype I]
    (x e : I → F) (j : ℕ) (hx : ∀ i,x i ≠ 0) (hj : j ≤ 71) :
    (∑ i,(x i^71*e i)*((x i)⁻¹)^j) =
      ∑ i,e i*x i^(71-j) := by
  apply Finset.sum_congr rfl
  intro i _
  exact reciprocal_one (x i) (e i) j (hx i) hj

theorem reciprocal_amplitude_twice (x e : F) (hx : x ≠ 0) :
    (x⁻¹)^71*(x^71*e) = e := by
  calc
    _ = ((x⁻¹)^71*x^71)*e := by ring
    _ = _ := by rw [← mul_pow, inv_mul_cancel₀ hx, one_pow, one_mul]

theorem scalar_mask_inverse (x m e : F) (hx : x ≠ 0) :
    ((x⁻¹)*m)*(x*e)=m*e := by
  calc
    _ = (x⁻¹*x)*(m*e) := by ring
    _ = _ := by rw [inv_mul_cancel₀ hx,one_mul]

end Field
section Unitized
variable {F : Type*} [Field F] [DecidableEq F]

/-- Complete a clipped scale to a total permutation without changing its
action on a nonzero pivot. This is not a proof of the singular-chart phase. -/
def unitize (d : F) : F := if d=0 then 1 else d

theorem unitize_nonzero (d : F) : unitize d ≠ 0 := by
  by_cases h : d=0
  · simp [unitize,h]
  · simp [unitize,h]

theorem unitize_agrees (d : F) (h : d ≠ 0) : unitize d=d := by
  simp [unitize,h]

theorem unitized_reciprocal (d : F) :
    (unitize d)⁻¹ = d⁻¹ + (if d=0 then 1 else 0) := by
  by_cases h : d=0
  · simp [unitize,h]
  · simp [unitize,h]

theorem scale_restore (d v : F) : (v*unitize d)/(unitize d)=v := by
  exact mul_div_cancel_right₀ v (unitize_nonzero d)

theorem divide_restore (d v : F) : (v/unitize d)*unitize d=v := by
  exact div_mul_cancel₀ v (unitize_nonzero d)

theorem norm_flag_valid {N : Type*} [Zero N] [DecidableEq N]
    (n : F → N) (h : ∀ d,n d=0 ↔ d=0) (d : F) :
    (if n d=0 then (1:F) else 0) = if d=0 then 1 else 0 := by
  rw [h d]

end Unitized

#print axioms pool_phase
#print axioms pool_refinement
#print axioms guard_xor
#print axioms phase_debt
#print axioms mask_transpose
#print axioms reciprocal_one
#print axioms reciprocal_moments
#print axioms reciprocal_amplitude_twice
#print axioms scalar_mask_inverse
#print axioms unitize_nonzero
#print axioms unitize_agrees
#print axioms unitized_reciprocal
#print axioms scale_restore
#print axioms divide_restore
#print axioms norm_flag_valid
end GVQCC.GuardedCubicPool
