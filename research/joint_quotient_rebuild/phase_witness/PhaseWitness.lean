import Lean

namespace GVQCC.PhaseWitness

/-- A measurement of a provably zero computational-basis wire contributes no character. -/
theorem zero_measurement (m : Bool) : (m && false) = false := by cases m <;> decide

/-- The discrepancy of a reconstructed measurement witness is the exact XOR residual. -/
theorem witness_debt (m x xhat : Bool) :
    Bool.xor (m && x) (m && xhat) = (m && Bool.xor x xhat) := by
  cases m <;> cases x <;> cases xhat <;> decide

/-- Removing a phase-only dependence when the measurement witness is zero. -/
theorem zero_lifetime (p m f : Bool) :
    Bool.xor (Bool.xor (Bool.xor p (m && false)) (m && f)) (m && f) = p := by
  cases p <;> cases m <;> cases f <;> decide

/-- Repay a correctly recovered witness, independently of the measurement outcome. -/
theorem exact_repay (p m x : Bool) :
    Bool.xor (Bool.xor p (m && x)) (m && x) = p := by
  cases p <;> cases m <;> cases x <;> decide

/-- If a restoration witness is unavailable, the same correction cannot cancel both phases. -/
theorem incompatible_witness (c : Bool) :
    ¬ ((Bool.xor (true && false) c = false) ∧
       (Bool.xor (true && true) c = false)) := by
  cases c <;> decide

end GVQCC.PhaseWitness
#print axioms GVQCC.PhaseWitness.zero_measurement
#print axioms GVQCC.PhaseWitness.witness_debt
#print axioms GVQCC.PhaseWitness.zero_lifetime
#print axioms GVQCC.PhaseWitness.exact_repay
#print axioms GVQCC.PhaseWitness.incompatible_witness
