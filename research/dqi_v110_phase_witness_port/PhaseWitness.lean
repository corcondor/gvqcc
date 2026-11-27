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

/-- An identical CCX pair cancels through an intervening target XOR whose
controls and phase do not depend on the toggled target. -/
theorem ccx_pair_through_xor (a b t k : Bool) :
    Bool.xor (Bool.xor (Bool.xor t (a && b)) k) (a && b) = Bool.xor t k := by
  cases a <;> cases b <;> cases t <;> cases k <;> decide

/-- The residual-annihilator guard, separated into its three independent
obligations. The final hypothesis is the weighted Vandermonde step: at
least one of the first w filtered moments of the true input is nonzero.
The lemma does not establish that the native circuit satisfies these
hypotheses, or assert that output zero implies input zero. -/
theorem prefix_guard
    {d w : Nat} (s r y : Nat → BitVec 12)
    (filter : (Nat → BitVec 12) → Nat → BitVec 12)
    (hadd : ∀ j, filter y j = filter s j ^^^ filter r j)
    (hann : ∀ j, filter r j = 0)
    (hwin : ∀ j, (∀ k, k ≤ d → y (j+k) = 0) → filter y j = 0)
    (hVandermonde : ∃ j, j < w ∧ filter s j ≠ 0) :
    ¬ (∀ i, i < d+w → y i = 0) := by
  intro hpref
  obtain ⟨j, hj, hn⟩ := hVandermonde
  have hz : filter y j = 0 := hwin j (by
    intro k hk
    apply hpref
    omega)
  rw [hadd, hann] at hz
  exact hn (by simpa using hz)

end GVQCC.PhaseWitness
#print axioms GVQCC.PhaseWitness.zero_measurement
#print axioms GVQCC.PhaseWitness.witness_debt
#print axioms GVQCC.PhaseWitness.zero_lifetime
#print axioms GVQCC.PhaseWitness.exact_repay
#print axioms GVQCC.PhaseWitness.incompatible_witness
#print axioms GVQCC.PhaseWitness.ccx_pair_through_xor
#print axioms GVQCC.PhaseWitness.prefix_guard
