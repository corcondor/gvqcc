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
  field_simp [hx] <;> ring

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

end GVQCC.FirstPole316
#print axioms GVQCC.FirstPole316.selected_nonzero
#print axioms GVQCC.FirstPole316.add_eq_sub_char_two
#print axioms GVQCC.FirstPole316.selected_nonzero_char_two
#print axioms GVQCC.FirstPole316.pole_contribution
#print axioms GVQCC.FirstPole316.pad_undo
#print axioms GVQCC.FirstPole316.phase_select
#print axioms GVQCC.FirstPole316.support_budget
