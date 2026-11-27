import Mathlib

namespace GVQCC.FirstPole316

/-- The selector compares a linear Hermite evaluation with the first pad.
This is a first-chart guarantee only, not a proof of all decoder branches. -/
theorem selected_nonzero {F : Type*} [Field F] [DecidableEq F]
    (s p q : F) (hpq : p ≠ q) :
    s - (if s = p then q else p) ≠ 0 := by
  by_cases h : s = p
  · rw [if_pos h, h]
    exact sub_ne_zero.mpr hpq
  · rw [if_neg h]
    exact sub_ne_zero.mpr h

theorem add_eq_sub_char_two {F : Type*} [Field F] [CharP F 2]
    (a b : F) : a + b = a - b := by
  have ht : (2 : F) = 0 := CharP.cast_eq_zero F 2
  have hb : b+b=0 := by
    calc
      b+b = 2*b := by ring
      _ = 0 := by rw [ht, zero_mul]
  linear_combination hb

theorem selected_nonzero_char_two {F : Type*} [Field F] [CharP F 2]
    [DecidableEq F] (s p q : F) (hpq : p ≠ q) :
    s + (if s = p then q else p) ≠ 0 := by
  rw [add_eq_sub_char_two]
  exact selected_nonzero s p q hpq

/-- Synthetic division U=(X+z)Q makes the first chart a linear
functional of the original syndrome moments, without a decoder. -/
theorem pole_contribution {F : Type*} [Field F] (e x z u q : F)
    (hu : u = (x+z)*q) (hx : x+z ≠ 0) :
    e*x*u/(x+z) = e*x*q := by
  rw [hu]
  field_simp [hx]

/-- Apply the selected constant translation twice after syndrome restoration. -/
theorem pad_undo {F : Type*} [Field F] [CharP F 2] (s p : F) :
    s+p+p=s := by
  rw [add_eq_sub_char_two (s+p) p]
  exact add_sub_cancel_right s p

/-- The two conditional Zs and one conditional NEG used in the joint
native tape select exactly one of the two classical phase debts. -/
theorem phase_select (tag d0 d1 : Bool) :
    Bool.xor d0 (Bool.xor (tag && d0) (tag && d1)) =
      (if tag then d1 else d0) := by
  cases tag <;> cases d0 <;> cases d1 <;> rfl

/-- Support-count hypotheses for the existing Vandermonde uniqueness argument.
This does not by itself establish that the parent decoder works on every chart. -/
theorem support_budget (w v : ℕ) (hw : w ≤ 17) (hv : v ≤ 35) :
    w+18+v ≤ 70 := by omega

/-- For a nonzero norm, cross multiplication gives the exact second-chart
predicate without computing a field inverse. The extension representation
and the physical selector still require their own validation. -/
theorem second_pole_norm_test {F : Type*} [Field F]
    (n v b u : F) (hn : n ≠ 0) :
    n*v = b*u^2 ↔ v = (b/n)*u^2 := by
  have h : n*((b/n)*u^2) = b*u^2 := by
    calc
      _ = ((b/n)*n)*u^2 := by ring
      _ = b*u^2 := by rw [div_mul_cancel₀ _ hn]
  constructor
  · intro hv
    exact mul_left_cancel₀ hn (hv.trans h.symm)
  · intro hv
    exact (congrArg (fun x => n*x) hv).trans h

end GVQCC.FirstPole316
#print axioms GVQCC.FirstPole316.selected_nonzero
#print axioms GVQCC.FirstPole316.add_eq_sub_char_two
#print axioms GVQCC.FirstPole316.selected_nonzero_char_two
#print axioms GVQCC.FirstPole316.pole_contribution
#print axioms GVQCC.FirstPole316.pad_undo
#print axioms GVQCC.FirstPole316.phase_select
#print axioms GVQCC.FirstPole316.support_budget
#print axioms GVQCC.FirstPole316.second_pole_norm_test
