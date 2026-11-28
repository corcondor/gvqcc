import Mathlib

namespace GVQCC.FullMaskResidue
open scoped BigOperators

section Algebra
variable {F : Type*} [Field F]

/-- Norm in a characteristic-two quadratic tower t²+t=k. -/
theorem tower_norm (a b t k : F) (h2 : (2:F)=0)
    (ht : t^2+t=k) :
    (a+b*t)*((a+b)+b*t)=a^2+a*b+k*b^2 := by
  calc
    _ = a^2+a*b+b^2*(t^2+t)+2*a*b*t := by ring
    _ = _ := by rw [ht,h2]; ring

/-- The trace-coordinate of (c+d*t) conjugate(a+b*t).
    This contraction replaces reconstruction of the full inverse word. -/
theorem tower_cross (a b c d t k : F) (ht : t^2+t=k) :
    (c+d*t)*((a+b)+b*t) =
      (c*(a+b)+d*b*k)+(c*b+d*a)*t := by
  calc
    _ = c*(a+b)+d*b*(t^2+t)+(c*b+d*a)*t := by ring
    _ = _ := by rw [ht]

theorem inverse_conjugate (s c n : F) (h : s*c=n) (hn : n≠0) :
    s⁻¹=c*n⁻¹ := by
  have hs : s≠0 := by
    intro hz
    apply hn
    rw [← h,hz,zero_mul]
  apply (mul_left_cancel₀ hs)
  calc
    s*s⁻¹=1 := mul_inv_cancel₀ hs
    _ = n*n⁻¹ := (mul_inv_cancel₀ hn).symm
    _ = s*(c*n⁻¹) := by rw [← h]; ring

theorem residue_scale (N x U d m : F) :
    m*(N/(x*U*d)) = (m/(x*U))*N*d⁻¹ := by
  simp only [div_eq_mul_inv,mul_inv_rev]
  ring

theorem point_mask_split (e m x r : F) (h2 : (2:F)=0) :
    e*m=e*(m+x*r)+e*x*r := by
  calc
    _ = e*m+2*e*x*r := by rw [h2]; ring
    _ = _ := by ring

theorem anchor_cancel (m x r : F) (h2 : (2:F)=0) (h : m=x*r) :
    m+x*r=0 := by
  rw [h]
  calc
    _ = 2*(x*r) := by ring
    _ = 0 := by rw [h2,zero_mul]

theorem gauge_compensate {I J : Type*} [Fintype I] [Fintype J]
    (e m x : I → F) (R : J → F) (k : J → Nat) (h2 : (2:F)=0) :
    (∑ i, e i*m i) =
      (∑ i, e i*(m i+x i*(∑ j, R j*x i^k j))) +
      ∑ j, R j*(∑ i, e i*x i^(k j+1)) := by
  have h :
      (∑ i, e i*x i*(∑ j, R j*x i^k j)) =
        ∑ j, R j*(∑ i, e i*x i^(k j+1)) := by
    simp_rw [Finset.mul_sum]
    rw [Finset.sum_comm]
    apply Finset.sum_congr rfl
    intro j _
    apply Finset.sum_congr rfl
    intro i _
    rw [pow_succ]
    ring
  rw [← h,← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro i _
  exact point_mask_split _ _ _ _ h2

theorem gauge_phase {I J : Type*} [Fintype I] [Fintype J]
    (tr : F →+ ZMod 2) (e m x : I → F) (R : J → F)
    (k : J → Nat) (h2 : (2:F)=0) :
    tr (∑ i, e i*m i) =
      tr (∑ i, e i*(m i+x i*(∑ j, R j*x i^k j))) +
      tr (∑ j, R j*(∑ i, e i*x i^(k j+1))) := by
  rw [gauge_compensate e m x R k h2,map_add]

/-- Delta evaluation when the D1 lane already carries D' at the old node. -/
theorem rolling_eval (D0 D1 tail dx old new : F) :
    D0+(old+new)*(D1+tail)+((old+new)*tail+dx) =
      D0+(old+new)*D1+dx+2*(old+new)*tail := by ring

theorem rolling_eval_char2 (D0 D1 tail dx old new : F) (h2 : (2:F)=0) :
    D0+(old+new)*(D1+tail)+((old+new)*tail+dx) =
      D0+(old+new)*D1+dx := by rw [rolling_eval,h2]; ring

theorem row_add_inverse (x y : F) (h2 : (2:F)=0) :
    (x+y)+y=x := by
  calc
    _ = x+2*y := by ring
    _ = x := by rw [h2]; ring

theorem projective_scaling (N d p : F) (hp : p≠0) :
    (p*N)/(p*d)=N/d := by
  simp only [div_eq_mul_inv,mul_inv_rev]
  calc
    _ = (p*p⁻¹)*(N*d⁻¹) := by ring
    _ = _ := by rw [mul_inv_cancel₀ hp,one_mul]

end Algebra

section Boolean
theorem guard_phase (g a b : Bool) : (a && b && g) = (a && (g && b)) := by
  cases g <;> cases a <;> cases b <;> decide

theorem hmr_guard_repay (g x r : Bool) :
    Bool.xor (r && (g && x)) (g && x && r)=false := by
  cases g <;> cases x <;> cases r <;> decide

theorem conditional_row_inverse (g a b : Bool) :
    Bool.xor (Bool.xor b (g && a)) (g && a)=b := by
  cases g <;> cases a <;> cases b <;> decide

theorem exact_width : 852+13+18+11+6=900 := by decide
theorem saved_anchor_cost : 219629+(4095-70)*83=553704 := by decide
end Boolean
end GVQCC.FullMaskResidue

#print axioms GVQCC.FullMaskResidue.tower_norm
#print axioms GVQCC.FullMaskResidue.tower_cross
#print axioms GVQCC.FullMaskResidue.inverse_conjugate
#print axioms GVQCC.FullMaskResidue.residue_scale
#print axioms GVQCC.FullMaskResidue.point_mask_split
#print axioms GVQCC.FullMaskResidue.anchor_cancel
#print axioms GVQCC.FullMaskResidue.gauge_compensate
#print axioms GVQCC.FullMaskResidue.gauge_phase
#print axioms GVQCC.FullMaskResidue.rolling_eval
#print axioms GVQCC.FullMaskResidue.rolling_eval_char2
#print axioms GVQCC.FullMaskResidue.row_add_inverse
#print axioms GVQCC.FullMaskResidue.projective_scaling
#print axioms GVQCC.FullMaskResidue.guard_phase
#print axioms GVQCC.FullMaskResidue.hmr_guard_repay
#print axioms GVQCC.FullMaskResidue.conditional_row_inverse
#print axioms GVQCC.FullMaskResidue.exact_width
#print axioms GVQCC.FullMaskResidue.saved_anchor_cost
