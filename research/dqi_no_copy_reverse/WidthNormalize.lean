import Mathlib

namespace GVQCC.WidthNormalize
variable {F : Type*} [Field F]

/-- Normalization of the first payload and the square-lifted second payload.
The physical multiplier must separately establish the division ABI. -/
theorem square_payload (s l d : F) (hs : s^2 = l) :
    (s/d)^2 = l/d^2 := by
  rw [div_pow, hs]

theorem restore_payload (n l d : F) (hd : d ≠ 0) :
    (n/d)*d = n ∧ (l/d^2)*d^2 = l := by
  exact ⟨div_mul_cancel₀ n hd, div_mul_cancel₀ l (pow_ne_zero 2 hd)⟩

noncomputable def selected (n d : F) : F := by
  classical
  exact if d=0 then n else d

theorem selected_nonzero (n d : F) (h : n ≠ 0 ∨ d ≠ 0) :
    selected n d ≠ 0 := by
  classical
  by_cases hd : d = 0
  · have hn : n ≠ 0 := h.resolve_right (fun hnd => hnd hd)
    simp [selected,hd,hn]
  · simp [selected,hd]

/-- A fully coherently restored payload incurs no extra measured phase debt.
The actual gate sequence needs its own semantic certificate. -/
theorem zero_debt (p f : Bool) : Bool.xor p (false && f) = p := by
  cases p <;> cases f <;> decide

theorem repay_measured_gauge (p m c c' : Bool) (h : c'=c) :
    Bool.xor (Bool.xor p (m && c)) (m && c') = p := by
  subst c'
  cases p <;> cases m <;> cases c <;> decide

end GVQCC.WidthNormalize
#print axioms GVQCC.WidthNormalize.square_payload
#print axioms GVQCC.WidthNormalize.restore_payload
#print axioms GVQCC.WidthNormalize.selected_nonzero
#print axioms GVQCC.WidthNormalize.zero_debt
#print axioms GVQCC.WidthNormalize.repay_measured_gauge
