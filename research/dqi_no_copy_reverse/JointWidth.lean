import Lean

namespace GVQCC.JointWidth
abbrev bx := Bool.xor

/-- Distribute a mask over a quotient representative. -/
theorem mask_quotient (f a b : Bool) :
    (f && bx a b) = bx (f && a) (f && b) := by
  cases f <;> cases a <;> cases b <;> decide

/-- Involutory CNOT coordinate transport. -/
theorem row_restore (a b : Bool) :
    bx (bx b a) a = b := by
  cases a <;> cases b <;> decide

/-- Masked phase conjugation through a controlled swap. -/
theorem cswap_phase (p a d m : Bool) :
    (m && (if p then a else d)) =
      bx (bx (m && d) (m && p && a)) (m && p && d) := by
  cases p <;> cases a <;> cases d <;> cases m <;> decide

/-- Two identical phase characters cancel. -/
theorem phase_cancel (p m x : Bool) :
    bx (bx p (m && x)) (m && x) = p := by
  cases p <;> cases m <;> cases x <;> decide

/-- A conditional restoration cannot replace an arbitrary inactive chart. -/
theorem inactive_restore_requires_equality (f old restored : Bool)
    (hf : f = false) :
    (if f then restored else old) = old := by
  revert hf
  cases f <;> cases old <;> cases restored <;> decide

end GVQCC.JointWidth

#print axioms GVQCC.JointWidth.mask_quotient
#print axioms GVQCC.JointWidth.row_restore
#print axioms GVQCC.JointWidth.cswap_phase
#print axioms GVQCC.JointWidth.phase_cancel
#print axioms GVQCC.JointWidth.inactive_restore_requires_equality
