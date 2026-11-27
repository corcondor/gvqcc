import Mathlib

namespace GVQCC.V120
variable {F : Type*} [Field F]

/-- A total, tag-free atlas for two field words. Division by zero is defined
as zero by the field structure. The zero row is encoded separately, in place. -/
noncomputable def atlas (c : F) (x : F × F) : F × F := by
  classical
  exact (c / x.1, if x.1 = 0 then c / x.2 else c * x.2 / x.1^2)

theorem atlas_zero (c b : F) : atlas c (0,b) = (0,c/b) := by
  classical
  simp [atlas]

theorem atlas_nonzero (c a b : F) (ha : a ≠ 0) :
    atlas c (a,b) = (c/a,c*b/a^2) := by
  classical
  simp [atlas,ha]

theorem scaled_inv_involution (c a : F) (hc : c ≠ 0) :
    c/(c/a) = a := by
  by_cases ha : a = 0
  · simp [ha]
  · field_simp [hc,ha] <;> ring

theorem second_coordinate_involution (c a b : F)
    (hc : c ≠ 0) (ha : a ≠ 0) :
    c*(c*b/a^2)/(c/a)^2 = b := by
  field_simp [hc,ha] <;> ring

/-- Involutive on ALL field pairs, including both coefficients zero.
The same circuit specification is usable in forward and reverse. -/
theorem atlas_involution (c : F) (hc : c ≠ 0) (x : F × F) :
    atlas c (atlas c x) = x := by
  rcases x with ⟨a,b⟩
  by_cases ha : a = 0
  · subst a
    rw [atlas_zero,atlas_zero,scaled_inv_involution c b hc]
  · have hu : c/a ≠ 0 := div_ne_zero hc ha
    rw [atlas_nonzero c a b ha,atlas_nonzero c (c/a) (c*b/a^2) hu,
      scaled_inv_involution c a hc,second_coordinate_involution c a b hc ha]

theorem atlas_injective (c : F) (hc : c ≠ 0) :
    Function.Injective (atlas c) := by
  intro x y h
  have hh := congrArg (atlas c) h
  rw [atlas_involution c hc x,atlas_involution c hc y] at hh
  exact hh

theorem atlas_surjective (c : F) (hc : c ≠ 0) :
    Function.Surjective (atlas c) := by
  intro y
  exact ⟨atlas c y, atlas_involution c hc y⟩

/-- The first stored word carries the chart selector, so no independent
selector bit is information-theoretically necessary for this encoding. -/
theorem atlas_zero_selector (c a b : F) (hc : c ≠ 0) :
    (atlas c (a,b)).1 = 0 ↔ a = 0 := by
  by_cases ha : a = 0
  · subst a
    rw [atlas_zero]
  · rw [atlas_nonzero c a b ha]
    exact iff_of_false (div_ne_zero hc ha) ha

/-- At the same node, a nonzero previous denominator becomes the new
numerator. The totalized quotient zero is then exactly the pole selector. -/
theorem repeated_head_selector (prev n d : F)
    (hp : prev ≠ 0) (hn : n = prev) : n/d = 0 ↔ d = 0 := by
  subst n
  constructor
  · intro h
    by_contra hd
    exact (div_ne_zero hp hd) h
  · intro hd
    simp [hd]

/-- The exceptional encoding agrees with the known finite tail equations
when the constant coefficient is a unit. -/
theorem finite_tail_agrees (c a b : F) (ha : a ≠ 0) :
    (atlas c (a,b)).1 * a = c ∧
    (atlas c (a,b)).2 * a^2 = c*b := by
  rw [atlas_nonzero c a b ha]
  exact ⟨div_mul_cancel₀ c ha, div_mul_cancel₀ (c*b) (pow_ne_zero 2 ha)⟩

end GVQCC.V120

#print axioms GVQCC.V120.atlas_zero
#print axioms GVQCC.V120.atlas_nonzero
#print axioms GVQCC.V120.scaled_inv_involution
#print axioms GVQCC.V120.second_coordinate_involution
#print axioms GVQCC.V120.atlas_involution
#print axioms GVQCC.V120.atlas_injective
#print axioms GVQCC.V120.atlas_surjective
#print axioms GVQCC.V120.atlas_zero_selector
#print axioms GVQCC.V120.repeated_head_selector
#print axioms GVQCC.V120.finite_tail_agrees
