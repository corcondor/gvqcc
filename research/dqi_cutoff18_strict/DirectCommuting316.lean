import Mathlib
namespace GVQCC.DirectCommuting316

/-- XOR-update involution under an unchanged classical condition. -/
theorem cancel_controlled_update (x a c : Bool) :
    (x ^^ (a && c)) ^^ (a && c) = x := by
  cases x <;> cases a <;> cases c <;> decide

/-- Two updates of the same target commute if their operands are unchanged. -/
theorem commute_updates (x a b : Bool) :
    (x ^^ a) ^^ b = (x ^^ b) ^^ a := by
  cases x <;> cases a <;> cases b <;> decide

/-- Identical conditional phase factors cancel. -/
theorem cancel_phase (p a b c : Bool) :
    (p ^^ (a && b && c)) ^^ (a && b && c) = p := by
  cases p <;> cases a <;> cases b <;> cases c <;> decide

/-- An invertible fixed coordinate change cannot remove a value counterexample. -/
theorem conjugation_failure {A : Type*} (f : A ≃ A) (u : A → A)
    (x : A) (h : u x ≠ x) : f.symm (u (f (f.symm x))) ≠ f.symm x := by
  rw [Equiv.apply_symm_apply]
  intro he
  exact h (f.symm.injective he)

end GVQCC.DirectCommuting316
#print axioms GVQCC.DirectCommuting316.cancel_controlled_update
#print axioms GVQCC.DirectCommuting316.commute_updates
#print axioms GVQCC.DirectCommuting316.cancel_phase
#print axioms GVQCC.DirectCommuting316.conjugation_failure
