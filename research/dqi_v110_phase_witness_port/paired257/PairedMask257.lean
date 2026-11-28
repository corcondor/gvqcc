import Std.Tactic

set_option autoImplicit false

namespace Gvqcc.PairedMask257

/-- Model the trace-dual identity as the oracle phase shift. The paired test
detects exactly when the two absolute error bits differ. It says nothing
about a phase error common to both arms. -/
theorem translatedDelta (f0 f1 p0 p1 d : Bool)
    (h : Bool.xor p0 p1 = d) :
    Bool.xor (Bool.xor f0 f1) d =
    Bool.xor (Bool.xor f0 p0) (Bool.xor f1 p1) := by
  cases f0 <;> cases f1 <;> cases p0 <;> cases p1 <;> simp_all

/-- Shared deterministic wrong return cannot be repaired by a phase-only
translation. This comparison intentionally ignores relative phase. -/
theorem identicalBadValue {α : Type} (input a b : α)
    (same : a = b) (wrong : a ≠ input) : b ≠ input := by
  simpa [same] using wrong

/-- For a common measurement record, a canceling phase debt drops out of
the paired comparison. This is conditional on the debt being shared. -/
theorem commonDebt (a b r : Bool) :
    Bool.xor (Bool.xor a r) (Bool.xor b r) = Bool.xor a b := by
  cases a <;> cases b <;> cases r <;> decide

#print axioms translatedDelta
#print axioms identicalBadValue
#print axioms commonDebt

end Gvqcc.PairedMask257
