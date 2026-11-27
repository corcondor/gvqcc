import Mathlib
namespace GVQCC.RollingCutoff
variable {F : Type*} [Field F]

noncomputable def select (n d : F) : F × F := by
  classical
  exact if n = 0 then (d,n) else (n,d)

theorem select_unit (n d : F) (h : n ≠ 0 ∨ d ≠ 0) :
    (select n d).1 ≠ 0 := by
  classical
  by_cases hn : n = 0
  · have hd : d ≠ 0 := h.resolve_left (by simp [hn])
    simp [select, hn, hd]
  · simp [select, hn]

theorem head_zero_iff (n d : F) :
    (select n d).2 / (select n d).1 = 0 ↔ n = 0 ∨ d = 0 := by
  classical
  by_cases hn : n = 0
  · simp [select,hn]
  · constructor
    · intro hz
      have hh : d/n = 0 := by simpa [select,hn] using hz
      right
      by_contra hd
      exact (div_ne_zero hd hn) hh
    · intro hz
      have hd := hz.resolve_left hn
      simp [select,hn,hd]

theorem lost_selector (x : F) (hx : x ≠ 0) :
    select (0:F) x = select x 0 ∧ ((0:F),x) ≠ (x,0) := by
  classical
  constructor
  · simp [select,hx]
  · intro h
    exact hx (congrArg Prod.fst h).symm

theorem previous_reconstruction (p z : Bool) :
    Bool.xor (Bool.xor p z) z = p := by
  cases p <;> cases z <;> decide

theorem zero_chart_phase (p z m phase : Bool) :
    Bool.xor (Bool.xor phase (m && z)) (m && (Bool.xor p (Bool.xor p z))) = phase := by
  cases p <;> cases z <;> cases m <;> cases phase <;> decide

theorem unitless_ratio_collision (a b : F) : a / (0:F) = b / 0 := by simp

end GVQCC.RollingCutoff
#print axioms GVQCC.RollingCutoff.select_unit
#print axioms GVQCC.RollingCutoff.head_zero_iff
#print axioms GVQCC.RollingCutoff.lost_selector
#print axioms GVQCC.RollingCutoff.previous_reconstruction
#print axioms GVQCC.RollingCutoff.zero_chart_phase
#print axioms GVQCC.RollingCutoff.unitless_ratio_collision
