import Init
namespace JointBudget316
def phasePatch (chart correction phase : Bool) : Bool :=
  phase ^^ (chart && correction)
theorem complement_unchanged (p c : Bool) :
    phasePatch false c p = p := by
  cases p <;> cases c <;> decide
theorem complement_error_persists (p c expected : Bool) (h : p != expected) :
    phasePatch false c p != expected := by
  rw [complement_unchanged]
  exact h
theorem phase_only_cannot_repair_value {A : Type} (out expected : A)
    (p chart correction : Bool) (h : out ≠ expected) :
    (out, phasePatch chart correction p).1 ≠ expected := h
theorem conditional_hmr (p d m f : Bool) :
    (p ^^ (d && m && f)) ^^ (if d && m then f else false) = p := by
  cases p <;> cases d <;> cases m <;> cases f <;> decide
#print axioms complement_unchanged
#print axioms complement_error_persists
#print axioms phase_only_cannot_repair_value
#print axioms conditional_hmr
end JointBudget316
